"""
Enhanced Autonomous Agent Orchestrator - Coordinates document-handling agents with QA classification
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from models.schemas import BOMComparisonResult, QAClassificationSummary
from .translation_agent import TranslationAgent
from .extraction_agent import ExtractionAgent  
from .supplier_bom_agent import SupplierBOMAgent
from .comparison_agent import ComparisonAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client

        # Initialize autonomous agents
        self.translation_agent = TranslationAgent(gemini_client)
        self.extraction_agent = ExtractionAgent(gemini_client)
        self.supplier_bom_agent = SupplierBOMAgent(gemini_client)
        self.comparison_agent = ComparisonAgent(gemini_client)

        logger.info("Enhanced Autonomous Agent Orchestrator initialized with QA classification")

    async def process_documents(
        self,
        qa_document_path: str,
        supplier_bom_path: str,
        workflow_id: str,
        progress_callback: Optional[Callable] = None
    ) -> BOMComparisonResult:
        """Orchestrate autonomous document processing workflow with QA classification"""
        logger.info(f"Starting enhanced autonomous workflow for {workflow_id}")

        try:
            # Stage 1: Translation Agent processes QA document (5% - 30%)
            if progress_callback:
                await progress_callback("translation", 5.0, "Translation agent processing QA document...")

            translation_result = await self.translation_agent.process_document(
                qa_document_path,
                source_language="ja", 
                target_language="en"
            )

            await self._save_stage_result(workflow_id, "translation", translation_result)

            if not translation_result["success"]:
                raise Exception(f"Translation failed: {translation_result.get('error', 'Unknown error')}")

            if progress_callback:
                await progress_callback("translation", 30.0, "Translation completed successfully")

            # Stage 2: Enhanced Extraction Agent processes translated content (30% - 55%)  
            if progress_callback:
                await progress_callback("extraction", 30.0, "Enhanced extraction agent processing with QA classification...")

            extraction_result = await self.extraction_agent.process_translated_content(
                translation_result["translated_text"],
                focus_categories=["fasteners", "adhesives", "seals", "gaskets", "electrical", "connectors", "hardware", "consumables", "jigs", "tools"]
            )

            await self._save_stage_result(workflow_id, "extraction", extraction_result)

            if not extraction_result["success"]:
                raise Exception(f"Extraction failed: {extraction_result.get('error', 'Unknown error')}")

            if progress_callback:
                qa_summary = extraction_result.get("qa_classification_summary", {})
                green_count = qa_summary.get("green_materials", 0)
                amber_count = qa_summary.get("amber_materials", 0) 
                red_count = qa_summary.get("red_materials", 0)
                await progress_callback("extraction", 55.0, f"Extracted {len(extraction_result['materials'])} materials: {green_count} auto-register, {amber_count} flagged, {red_count} need intervention")

            # Stage 3: Supplier BOM Agent processes supplier file (55% - 75%)
            if progress_callback:
                await progress_callback("supplier_bom", 55.0, "Supplier BOM agent processing file...")

            supplier_result = await self.supplier_bom_agent.process_supplier_file(supplier_bom_path)

            await self._save_stage_result(workflow_id, "supplier_bom", supplier_result)

            if not supplier_result["success"]:
                raise Exception(f"Supplier BOM processing failed: {supplier_result.get('error', 'Unknown error')}")

            if progress_callback:
                await progress_callback("supplier_bom", 75.0, f"Processed {supplier_result['total_items']} supplier items")

            # Stage 4: Enhanced Comparison Agent matches materials with QA classification (75% - 95%)
            if progress_callback:
                await progress_callback("comparison", 75.0, "Enhanced comparison agent matching with QA classification...")

            # Convert to legacy format for comparison
            legacy_supplier_bom = self._convert_bom_to_legacy_format(supplier_result["bom_data"])

            matches = await self.comparison_agent.compare_materials(
                extraction_result["materials"],
                legacy_supplier_bom,
                confidence_threshold=0.6
            )

            comparison_result = {
                "success": True,
                "matches": [m.dict() for m in matches],
                "matches_count": len(matches),
                "confidence_threshold": 0.6,
                "qa_classification_stats": extraction_result.get("qa_classification_summary", {})
            }

            await self._save_stage_result(workflow_id, "comparison", comparison_result)

            if progress_callback:
                matches_with_supplier = len([m for m in matches if m.confidence_score > 0])
                await progress_callback("comparison", 95.0, f"Found {matches_with_supplier} supplier matches with QA classification")

            # Stage 5: Finalize results with QA classification summary (95% - 100%)
            if progress_callback:
                await progress_callback("finalization", 95.0, "Finalizing enhanced workflow results...")

            # Generate QA classification summary
            qa_summary = self._generate_qa_classification_summary(extraction_result["materials"])

            final_result = BOMComparisonResult(
                workflow_id=workflow_id,
                matches=matches,
                total_qa_items=len(extraction_result["materials"]),
                total_supplier_items=supplier_result["total_items"],
                qa_classification_summary=qa_summary,
                processing_metadata={
                    "workflow_type": "autonomous_with_qa_classification",
                    "translation_success": translation_result["success"],
                    "extraction_success": extraction_result["success"],
                    "supplier_bom_success": supplier_result["success"],
                    "processing_time": datetime.utcnow().isoformat(),
                    "qa_classification_enabled": True,
                    "classification_rules_applied": 13,
                    "agent_stats": {
                        "translation": self.translation_agent.get_stats(),
                        "extraction": self.extraction_agent.get_stats(),
                        "supplier_bom": self.supplier_bom_agent.get_stats(),
                        "comparison": self.comparison_agent.get_stats()
                    }
                }
            )

            await self._save_stage_result(workflow_id, "final_results", {"result": final_result.dict()})

            if progress_callback:
                await progress_callback("complete", 100.0, f"Enhanced workflow completed - {qa_summary.green_materials} auto-register, {qa_summary.amber_materials} flagged, {qa_summary.red_materials} need intervention")

            logger.info(f"Enhanced autonomous workflow {workflow_id} completed with QA classification")
            return final_result

        except Exception as e:
            logger.error(f"Enhanced autonomous workflow error: {e}")
            if progress_callback:
                await progress_callback("error", 0.0, f"Workflow failed: {str(e)}")
            raise

    def _generate_qa_classification_summary(self, materials: List) -> QAClassificationSummary:
        """Generate QA classification summary from extracted materials"""
        if not materials:
            return QAClassificationSummary(
                total_materials=0,
                green_materials=0,
                amber_materials=0,
                red_materials=0,
                classification_breakdown={}
            )

        # Count by action path
        green_count = sum(1 for m in materials if getattr(m, 'action_path_rag', None) == '🟢')
        amber_count = sum(1 for m in materials if getattr(m, 'action_path_rag', None) == '🟠')  
        red_count = sum(1 for m in materials if getattr(m, 'action_path_rag', None) == '🔴')

        # Classification breakdown by label
        breakdown = {}
        for material in materials:
            label = getattr(material, 'classification_label', None)
            if label:
                label_key = f"Label {label.value if hasattr(label, 'value') else label}"
                breakdown[label_key] = breakdown.get(label_key, 0) + 1

        return QAClassificationSummary(
            total_materials=len(materials),
            green_materials=green_count,
            amber_materials=amber_count,
            red_materials=red_count,
            classification_breakdown=breakdown
        )

    async def _save_stage_result(self, workflow_id: str, stage_name: str, data: dict):
        """Save intermediate results from autonomous agents"""
        try:
            workflow_dir = Path("uploads").resolve() / workflow_id
            workflow_dir.mkdir(parents=True, exist_ok=True)

            file_path = workflow_dir / f"{stage_name}_autonomous_result.json"

            def json_serializer(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                elif hasattr(obj, 'dict'):
                    return obj.dict()
                elif hasattr(obj, 'value'):  # For Enum objects
                    return obj.value
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=json_serializer)

            logger.info(f"Saved enhanced {stage_name} results to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save enhanced {stage_name} results: {e}")

    def _convert_bom_to_legacy_format(self, bom_data: Dict) -> List[Dict]:
        """Convert autonomous BOM format to legacy comparison format"""
        legacy_items = []

        for sheet_name, sheet_data in bom_data.get("sheets", {}).items():
            for item in sheet_data.get("items", []):
                legacy_item = {
                    "part_number": item.get("part_number", ""),
                    "description": item.get("description", ""),
                    "category": item.get("category", ""),
                    "manufacturer": item.get("manufacturer", ""),
                    "quantity": item.get("quantity", ""),
                    "sheet_name": sheet_name,
                    "row_index": item.get("row_index", 0)
                }
                legacy_items.append(legacy_item)

        return legacy_items

    async def get_processing_statistics(self) -> Dict:
        """Get comprehensive processing statistics from all autonomous agents"""
        return {
            "orchestrator_type": "autonomous_with_qa_classification",
            "agents_available": True,
            "qa_classification_enabled": True,
            "classification_rules": 13,
            "translation_agent": self.translation_agent.get_stats(),
            "extraction_agent": self.extraction_agent.get_stats(), 
            "supplier_bom_agent": self.supplier_bom_agent.get_stats(),
            "comparison_agent": self.comparison_agent.get_stats(),
            "gemini_configured": self.gemini_client.is_available() if self.gemini_client else False
        }
