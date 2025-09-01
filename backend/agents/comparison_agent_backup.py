"""
Enhanced Comparison Agent - Multi-strategy BOM matching with QA classification integration
"""

import logging
from typing import List, Dict
from models.schemas import ExtractedMaterial, BOMMatch, QAClassificationLabel, ActionPathRAG, ConfidenceLevel

logger = logging.getLogger(__name__)

class ComparisonAgent:
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.stats = {"comparisons_performed": 0, "matches_found": 0, "errors": 0, "qa_classifications_processed": 0}
        logger.info("Enhanced Comparison agent initialized with QA classification support")

    async def compare_materials(self, qa_materials: List[ExtractedMaterial], supplier_bom: List[Dict], confidence_threshold: float = 0.6) -> List[BOMMatch]:
        """Compare QA materials with supplier BOM using multiple strategies and QA classification"""
        try:
            all_matches = []
            qa_classification_stats = {"green": 0, "amber": 0, "red": 0}

            for qa_material in qa_materials:
                logger.info(f"Comparing material: {qa_material.name} (Classification: {qa_material.classification_label.value})")

                # Update classification stats
                if qa_material.action_path_rag == ActionPathRAG.GREEN:
                    qa_classification_stats["green"] += 1
                elif qa_material.action_path_rag == ActionPathRAG.AMBER:
                    qa_classification_stats["amber"] += 1
                else:
                    qa_classification_stats["red"] += 1

                # Try different matching strategies based on QA classification
                matches = await self._find_matches_for_classified_material(qa_material, supplier_bom)

                # Filter by confidence threshold, but consider QA classification
                valid_matches = self._filter_matches_by_qa_classification(matches, qa_material, confidence_threshold)

                if valid_matches:
                    # Take the best match and enhance with QA classification info
                    best_match = max(valid_matches, key=lambda x: x.confidence_score)
                    # Copy QA fields to match for results display
                    self._enhance_match_with_qa_data(best_match, qa_material)
                    all_matches.append(best_match)
                else:
                    # Create a no-match entry with QA data for classification table
                    no_match = BOMMatch(
                        qa_material_name=qa_material.name,
                        supplier_part_number="",
                        supplier_description="No match found",
                        confidence_score=0.0,
                        match_type="no_match",
                        qa_excerpt=qa_material.context,
                        reasoning="No suitable match found in supplier BOM"
                    )
                    self._enhance_match_with_qa_data(no_match, qa_material)
                    all_matches.append(no_match)

            self.stats["comparisons_performed"] += 1
            self.stats["matches_found"] += len([m for m in all_matches if m.confidence_score > 0])
            self.stats["qa_classifications_processed"] += len(qa_materials)

            logger.info(f"Comparison completed. Found {len([m for m in all_matches if m.confidence_score > 0])} matches with QA classification")
            logger.info(f"QA Classification distribution: Green={qa_classification_stats['green']}, Amber={qa_classification_stats['amber']}, Red={qa_classification_stats['red']}")

            return all_matches

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Comparison error: {e}")
            return []

    def _enhance_match_with_qa_data(self, match: BOMMatch, qa_material: ExtractedMaterial):
        """Enhance match with QA classification data"""
        match.qa_classification_label = qa_material.classification_label
        match.qa_action_path = qa_material.action_path_rag
        match.qa_confidence_level = qa_material.confidence_level

        # Copy additional QA fields for results display
        match.qc_process_step = qa_material.qc_process_step
        match.consumable_jigs_tools = qa_material.consumable_jigs_tools
        match.part_number = qa_material.part_number
        match.pn_mismatch = qa_material.pn_mismatch
        match.quantity = qa_material.quantity
        match.unit_of_measure = qa_material.unit_of_measure
        match.vendor_name = qa_material.vendor_name
        match.kit_available = qa_material.kit_available
        match.obsolete_pn = qa_material.obsolete_pn
        match.name_mismatch = qa_material.name_mismatch

    async def _find_matches_for_classified_material(self, qa_material: ExtractedMaterial, supplier_bom: List[Dict]) -> List[BOMMatch]:
        """Find potential matches for a single QA material considering its classification"""
        matches = []

        # Strategy 1: Exact part number matching (prioritized for classified materials with PNs)
        if qa_material.part_number and qa_material.classification_label in [
            QAClassificationLabel.CONSUMABLE_WITH_PN_QTY,
            QAClassificationLabel.CONSUMABLE_WITH_PN_SPEC_QTY,
            QAClassificationLabel.CONSUMABLE_NO_QTY
        ]:
            exact_pn_matches = self._exact_part_number_match(qa_material, supplier_bom)
            matches.extend(exact_pn_matches)

        # Strategy 2: Exact name/description matching
        exact_matches = self._exact_match(qa_material, supplier_bom)
        matches.extend(exact_matches)

        # Strategy 3: Vendor-based matching (for vendor-only classifications)
        if qa_material.vendor_name and qa_material.classification_label in [
            QAClassificationLabel.VENDOR_NAME_ONLY,
            QAClassificationLabel.VENDOR_KIT_NO_PN
        ]:
            vendor_matches = self._vendor_based_match(qa_material, supplier_bom)
            matches.extend(vendor_matches)

        # Strategy 4: Fuzzy matching (for ambiguous or incomplete materials)
        if qa_material.classification_label in [
            QAClassificationLabel.CONSUMABLE_NO_PN,
            QAClassificationLabel.AMBIGUOUS_CONSUMABLE_NAME,
            QAClassificationLabel.NO_CONSUMABLE_MENTIONED
        ]:
            fuzzy_matches = self._fuzzy_match(qa_material, supplier_bom)
            matches.extend(fuzzy_matches)

        return matches

    def _exact_part_number_match(self, qa_material: ExtractedMaterial, supplier_bom: List[Dict]) -> List[BOMMatch]:
        """Perform exact part number matching"""
        matches = []
        qa_pn = qa_material.part_number.lower() if qa_material.part_number else ""

        for supplier_item in supplier_bom:
            supplier_pn = supplier_item.get("part_number", "").lower()

            if qa_pn and qa_pn == supplier_pn:
                confidence = 0.98  # Very high confidence for exact PN match
                match = BOMMatch(
                    qa_material_name=qa_material.name,
                    supplier_part_number=supplier_item.get("part_number", ""),
                    supplier_description=supplier_item.get("description", ""),
                    confidence_score=confidence,
                    match_type="exact_part_number",
                    qa_excerpt=qa_material.context,
                    reasoning=f"Exact part number match: {qa_material.part_number}",
                    material_category=qa_material.category,
                    supplier_category=supplier_item.get("category", ""),
                    specifications_match=list(qa_material.specifications.keys()),
                    differences=[]
                )
                matches.append(match)

        return matches

    def _vendor_based_match(self, qa_material: ExtractedMaterial, supplier_bom: List[Dict]) -> List[BOMMatch]:
        """Perform vendor-based matching"""
        matches = []
        qa_vendor = qa_material.vendor_name.lower() if qa_material.vendor_name else ""

        for supplier_item in supplier_bom:
            supplier_vendor = supplier_item.get("manufacturer", "").lower()

            if qa_vendor and qa_vendor in supplier_vendor:
                # Also check if material names are related
                name_similarity = self._calculate_name_similarity(qa_material.name, supplier_item.get("description", ""))
                confidence = 0.6 + (name_similarity * 0.3)  # Base vendor match + name similarity bonus

                match = BOMMatch(
                    qa_material_name=qa_material.name,
                    supplier_part_number=supplier_item.get("part_number", ""),
                    supplier_description=supplier_item.get("description", ""),
                    confidence_score=confidence,
                    match_type="vendor_based",
                    qa_excerpt=qa_material.context,
                    reasoning=f"Vendor match: {qa_material.vendor_name} with name similarity {name_similarity:.2f}",
                    material_category=qa_material.category,
                    supplier_category=supplier_item.get("category", ""),
                    specifications_match=[],
                    differences=["Matched primarily on vendor name"]
                )
                matches.append(match)

        return matches

    def _exact_match(self, qa_material: ExtractedMaterial, supplier_bom: List[Dict]) -> List[BOMMatch]:
        """Perform exact string matching"""
        matches = []
        qa_name_lower = qa_material.name.lower()

        for supplier_item in supplier_bom:
            supplier_desc = supplier_item.get("description", "").lower()
            supplier_part = supplier_item.get("part_number", "").lower()

            if qa_name_lower in supplier_desc or qa_name_lower in supplier_part:
                match = BOMMatch(
                    qa_material_name=qa_material.name,
                    supplier_part_number=supplier_item.get("part_number", ""),
                    supplier_description=supplier_item.get("description", ""),
                    confidence_score=0.95,
                    match_type="exact",
                    qa_excerpt=qa_material.context,
                    reasoning="Exact match found in supplier description",
                    material_category=qa_material.category,
                    supplier_category=supplier_item.get("category", ""),
                    specifications_match=list(qa_material.specifications.keys()),
                    differences=[]
                )
                matches.append(match)

        return matches

    def _fuzzy_match(self, qa_material: ExtractedMaterial, supplier_bom: List[Dict]) -> List[BOMMatch]:
        """Perform fuzzy string matching"""
        matches = []
        qa_name_lower = qa_material.name.lower()

        for supplier_item in supplier_bom:
            supplier_desc = supplier_item.get("description", "").lower()

            # Simple fuzzy matching based on common words
            qa_words = set(qa_name_lower.split())
            supplier_words = set(supplier_desc.split())

            common_words = qa_words.intersection(supplier_words)
            if len(common_words) >= 2:  # At least 2 words in common
                confidence = len(common_words) / max(len(qa_words), len(supplier_words))

                if confidence >= 0.4:  # Minimum fuzzy threshold
                    match = BOMMatch(
                        qa_material_name=qa_material.name,
                        supplier_part_number=supplier_item.get("part_number", ""),
                        supplier_description=supplier_item.get("description", ""),
                        confidence_score=confidence,
                        match_type="fuzzy_match",
                        qa_excerpt=qa_material.context,
                        reasoning=f"Fuzzy match based on {len(common_words)} common words: {', '.join(common_words)}",
                        material_category=qa_material.category,
                        supplier_category=supplier_item.get("category", ""),
                        specifications_match=list(qa_material.specifications.keys()),
                        differences=[]
                    )
                    matches.append(match)

        return matches

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate simple name similarity score"""
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _filter_matches_by_qa_classification(self, matches: List[BOMMatch], qa_material: ExtractedMaterial, base_threshold: float) -> List[BOMMatch]:
        """Filter matches considering QA classification confidence"""

        # Adjust confidence threshold based on QA classification
        if qa_material.action_path_rag == ActionPathRAG.GREEN:
            # Lower threshold for high-confidence QA materials
            adjusted_threshold = base_threshold * 0.8
        elif qa_material.action_path_rag == ActionPathRAG.AMBER:
            # Standard threshold for medium-confidence materials
            adjusted_threshold = base_threshold
        else:  # RED
            # Higher threshold for low-confidence materials
            adjusted_threshold = base_threshold * 1.2

        # Also consider if material requires human intervention
        if qa_material.classification_label in [
            QAClassificationLabel.CONSUMABLE_NO_PN,
            QAClassificationLabel.NO_CONSUMABLE_MENTIONED,
            QAClassificationLabel.CONSUMABLE_PN_MISMATCH,
            QAClassificationLabel.CONSUMABLE_OBSOLETE_PN,
            QAClassificationLabel.AMBIGUOUS_CONSUMABLE_NAME
        ]:
            # For materials requiring human intervention, be more conservative
            adjusted_threshold = max(adjusted_threshold, 0.7)

        return [m for m in matches if m.confidence_score >= adjusted_threshold]

    def get_stats(self) -> Dict:
        return self.stats.copy()
