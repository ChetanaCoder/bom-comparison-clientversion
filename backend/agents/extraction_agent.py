"""
Enhanced Autonomous Extraction Agent - Handles material extraction with QA classification
"""

import logging
import json
from typing import List, Dict
from models.schemas import ExtractedMaterial, QAClassificationLabel, ActionPathRAG, ConfidenceLevel

logger = logging.getLogger(__name__)

class ExtractionAgent:
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.stats = {"extractions_performed": 0, "materials_extracted": 0, "chunks_processed": 0, "errors": 0}
        logger.info("Enhanced Autonomous Extraction Agent initialized with QA classification")

    async def process_translated_content(self, translated_content: str, focus_categories: List[str] = None) -> dict:
        """Process translated content and extract materials with QA classification"""
        try:
            if not focus_categories:
                focus_categories = [
                    "fasteners", "adhesives", "seals", "gaskets", 
                    "electrical", "connectors", "hardware", "consumables", "jigs", "tools"
                ]

            logger.info(f"Processing translated content ({len(translated_content)} characters)")

            # Step 1: Split content into extraction chunks
            chunks = self._split_into_extraction_chunks(translated_content)
            logger.info(f"Split content into {len(chunks)} chunks for extraction")

            # Step 2: Extract materials from each chunk with enhanced fields
            all_materials = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Extracting from chunk {i+1}/{len(chunks)}")
                chunk_materials = await self._extract_from_chunk_enhanced(chunk, focus_categories)
                all_materials.extend(chunk_materials)

            # Step 3: Deduplicate and finalize
            unique_materials = self._deduplicate_materials(all_materials)

            # Step 4: Generate classification summary
            classification_summary = self._generate_classification_summary(unique_materials)

            # Update statistics
            self.stats["extractions_performed"] += 1
            self.stats["materials_extracted"] += len(unique_materials)
            self.stats["chunks_processed"] += len(chunks)

            return {
                "success": True,
                "materials": unique_materials,
                "total_materials": len(unique_materials),
                "chunks_processed": len(chunks),
                "focus_categories": focus_categories,
                "confidence_distribution": self._calculate_confidence_distribution(unique_materials),
                "qa_classification_summary": classification_summary,
                "processing_stats": self.stats.copy()
            }

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Extraction processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "materials": [],
                "processing_stats": self.stats.copy()
            }

    def _split_into_extraction_chunks(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """Split text into chunks suitable for material extraction"""
        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        sections = text.split('\n\n')
        current_chunk = []
        current_length = 0

        for section in sections:
            if current_length + len(section) > max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [section]
                current_length = len(section)
            else:
                current_chunk.append(section)
                current_length += len(section)

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    async def _extract_from_chunk_enhanced(self, text: str, categories: List[str]) -> List[ExtractedMaterial]:
        """Extract materials with enhanced QA classification from a single text chunk"""
        if not self.gemini_client or not self.gemini_client.is_available():
            return self._create_demo_materials_chunk_enhanced()

        extraction_prompt = f"""Extract materials from this technical Work Instruction (QA) document section and classify them according to QA processing rules.

Focus on these categories: {', '.join(categories)}

For each material found, provide JSON format with ALL these fields:
{{
    "name": "material name/description",
    "category": "one of {categories}",
    "specifications": {{"key": "value"}},
    "context": "surrounding text explaining usage",
    "confidence_score": 0.8,

    // Enhanced QA Classification Fields:
    "qc_process_step": "QC step or work instruction step if mentioned or null", 
    "consumable_jigs_tools": true/false,
    "name_mismatch": false,
    "part_number": "PN if available or null",
    "pn_mismatch": false,
    "quantity": number or null,
    "unit_of_measure": "UoM if available or null",
    "obsolete_pn": false,
    "vendor_name": "vendor if mentioned or null",
    "kit_available": true/false,
    "ai_engine_processing": "processing notes"
}}

Text section:
{text}

Return as JSON array of materials with enhanced classification:"""

        try:
            response = await self.gemini_client.generate_content(
                extraction_prompt,
                temperature=0.2,
                max_tokens=2000
            )

            # Parse AI response
            response_cleaned = response.strip()
            if response_cleaned.startswith("```json"):
                response_cleaned = response_cleaned[7:-3]
            elif response_cleaned.startswith("```"):
                response_cleaned = response_cleaned[3:-3]

            materials_data = json.loads(response_cleaned)
            materials = []

            for material_data in materials_data:
                # Create enhanced material with classification
                material = self._create_enhanced_material(material_data, text)
                materials.append(material)

            return materials

        except Exception as e:
            logger.warning(f"AI extraction failed for chunk: {e}")
            return self._create_demo_materials_chunk_enhanced()

    def _create_enhanced_material(self, material_data: dict, source_text: str) -> ExtractedMaterial:
        """Create enhanced material with QA classification"""

        # Determine classification based on available data
        classification_result = self._classify_material(material_data)

        material = ExtractedMaterial(
            # Original fields
            name=material_data.get("name", "Unknown Material"),
            category=material_data.get("category", "uncategorized"),
            specifications=material_data.get("specifications", {}),
            context=material_data.get("context", ""),
            confidence_score=float(material_data.get("confidence_score", 0.5)),
            source_section=source_text[:200] + "..." if len(source_text) > 200 else source_text,

            # Enhanced QA fields
            qc_process_step=material_data.get("qc_process_step"),
            consumable_jigs_tools=material_data.get("consumable_jigs_tools", False),
            name_mismatch=material_data.get("name_mismatch", False),
            part_number=material_data.get("part_number"),
            pn_mismatch=material_data.get("pn_mismatch", False),
            quantity=material_data.get("quantity"),
            unit_of_measure=material_data.get("unit_of_measure"),
            obsolete_pn=material_data.get("obsolete_pn", False),
            vendor_name=material_data.get("vendor_name"),
            kit_available=material_data.get("kit_available", False),
            ai_engine_processing=material_data.get("ai_engine_processing", "AI processed"),

            # Classification results
            confidence_level=classification_result["confidence_level"],
            action_path_rag=classification_result["action_path"],
            classification_label=classification_result["label"],
            classification_reasoning=classification_result["reasoning"]
        )

        return material

    def _classify_material(self, material_data: dict) -> dict:
        """Classify material based on QA rules (1-13)"""

        has_consumable = material_data.get("consumable_jigs_tools", False)
        has_pn = bool(material_data.get("part_number"))
        has_qty = bool(material_data.get("quantity"))
        has_specs = bool(material_data.get("specifications"))
        has_vendor = bool(material_data.get("vendor_name"))
        has_kit = material_data.get("kit_available", False)
        pn_mismatch = material_data.get("pn_mismatch", False)
        obsolete_pn = material_data.get("obsolete_pn", False)

        # Apply classification rules
        if has_consumable and has_pn and has_qty and has_specs:
            return {
                "label": QAClassificationLabel.CONSUMABLE_WITH_PN_SPEC_QTY,
                "confidence_level": ConfidenceLevel.HIGH,
                "action_path": ActionPathRAG.GREEN,
                "reasoning": "Consumable with PN, specifications, and quantity - Auto-Register"
            }
        elif has_consumable and has_pn and has_qty:
            return {
                "label": QAClassificationLabel.CONSUMABLE_WITH_PN_QTY,
                "confidence_level": ConfidenceLevel.HIGH,
                "action_path": ActionPathRAG.GREEN,
                "reasoning": "Consumable with PN and quantity - Auto-Register"
            }
        elif has_consumable and has_pn and not has_qty:
            return {
                "label": QAClassificationLabel.CONSUMABLE_NO_QTY,
                "confidence_level": ConfidenceLevel.MEDIUM,
                "action_path": ActionPathRAG.AMBER,
                "reasoning": "Consumable with PN but no quantity - Auto with Flag"
            }
        elif has_consumable and not has_pn:
            return {
                "label": QAClassificationLabel.CONSUMABLE_NO_PN,
                "confidence_level": ConfidenceLevel.LOW,
                "action_path": ActionPathRAG.RED,
                "reasoning": "Consumable mentioned but no part number - Human Intervention Required"
            }
        elif obsolete_pn:
            return {
                "label": QAClassificationLabel.CONSUMABLE_OBSOLETE_PN,
                "confidence_level": ConfidenceLevel.LOW,
                "action_path": ActionPathRAG.RED,
                "reasoning": "Obsolete part number detected - Human Intervention Required"
            }
        elif pn_mismatch:
            return {
                "label": QAClassificationLabel.CONSUMABLE_PN_MISMATCH,
                "confidence_level": ConfidenceLevel.LOW,
                "action_path": ActionPathRAG.RED,
                "reasoning": "Part number mismatch detected - Human Intervention Required"
            }
        elif has_vendor and has_kit and not has_pn:
            return {
                "label": QAClassificationLabel.VENDOR_KIT_NO_PN,
                "confidence_level": ConfidenceLevel.LOW,
                "action_path": ActionPathRAG.RED,
                "reasoning": "Vendor and kit mentioned but no PN - Human Intervention Required"
            }
        elif has_vendor and not has_consumable:
            return {
                "label": QAClassificationLabel.VENDOR_NAME_ONLY,
                "confidence_level": ConfidenceLevel.MEDIUM,
                "action_path": ActionPathRAG.AMBER,
                "reasoning": "Only vendor name mentioned - Auto with Flag"
            }
        elif has_kit:
            return {
                "label": QAClassificationLabel.PRE_ASSEMBLED_KIT,
                "confidence_level": ConfidenceLevel.MEDIUM,
                "action_path": ActionPathRAG.AMBER,
                "reasoning": "Pre-assembled kit mentioned - Auto with Flag"
            }
        else:
            return {
                "label": QAClassificationLabel.NO_CONSUMABLE_MENTIONED,
                "confidence_level": ConfidenceLevel.LOW,
                "action_path": ActionPathRAG.RED,
                "reasoning": "No clear consumable/jigs/tools mentioned - Human Intervention Required"
            }

    def _create_demo_materials_chunk_enhanced(self) -> List[ExtractedMaterial]:
        """Create demo materials with enhanced classification when AI is not available"""
        return [
            ExtractedMaterial(
                name="M6x20mm Hex Bolt",
                category="fasteners",
                specifications={"size": "M6x20mm", "type": "hex bolt", "material": "stainless steel"},
                context="Use M6×20 hex bolts for chassis mounting",
                confidence_score=0.95,
                source_section="Demo chunk - configure GEMINI_API_KEY for real processing",

                # Enhanced fields
                qc_process_step="Assembly Step 3",
                consumable_jigs_tools=True,
                part_number="BOLT-M6-20-SS",
                quantity=4.0,
                unit_of_measure="pieces",
                ai_engine_processing="Demo mode - AI classification",
                confidence_level=ConfidenceLevel.HIGH,
                action_path_rag=ActionPathRAG.GREEN,
                classification_label=QAClassificationLabel.CONSUMABLE_WITH_PN_QTY,
                classification_reasoning="Demo: Consumable with PN and quantity - Auto-Register"
            )
        ]

    def _generate_classification_summary(self, materials: List[ExtractedMaterial]) -> dict:
        """Generate summary of QA classifications"""
        if not materials:
            return {
                "total_materials": 0,
                "green_materials": 0,
                "amber_materials": 0,
                "red_materials": 0,
                "classification_breakdown": {}
            }

        green_count = sum(1 for m in materials if m.action_path_rag == ActionPathRAG.GREEN)
        amber_count = sum(1 for m in materials if m.action_path_rag == ActionPathRAG.AMBER)
        red_count = sum(1 for m in materials if m.action_path_rag == ActionPathRAG.RED)

        # Classification breakdown by label
        breakdown = {}
        for material in materials:
            label_name = f"Label {material.classification_label.value}"
            breakdown[label_name] = breakdown.get(label_name, 0) + 1

        return {
            "total_materials": len(materials),
            "green_materials": green_count,
            "amber_materials": amber_count, 
            "red_materials": red_count,
            "classification_breakdown": breakdown
        }

    def _deduplicate_materials(self, materials: List[ExtractedMaterial]) -> List[ExtractedMaterial]:
        """Remove duplicate materials"""
        if not materials:
            return []

        unique_materials = []
        seen_names = set()

        for material in materials:
            name_key = material.name.lower().strip()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_materials.append(material)

        return unique_materials

    def _calculate_confidence_distribution(self, materials: List[ExtractedMaterial]) -> Dict:
        """Calculate confidence score distribution"""
        if not materials:
            return {"high": 0, "medium": 0, "low": 0}

        high = sum(1 for m in materials if m.confidence_score >= 0.8)
        medium = sum(1 for m in materials if 0.6 <= m.confidence_score < 0.8)
        low = sum(1 for m in materials if m.confidence_score < 0.6)

        return {"high": high, "medium": medium, "low": low}

    def get_stats(self) -> Dict:
        """Get processing statistics"""
        return self.stats.copy()
