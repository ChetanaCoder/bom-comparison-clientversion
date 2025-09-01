"""
Enhanced data models and schemas for autonomous BOM comparison platform with QA classification
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from enum import Enum

class ActionPathRAG(str, Enum):
    """RAG classification for action paths"""
    GREEN = "🟢"
    AMBER = "🟠" 
    RED = "🔴"

class ConfidenceLevel(str, Enum):
    """Confidence levels for AI processing"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class QAClassificationLabel(int, Enum):
    """QA Material Classification Labels (1-13)"""
    CONSUMABLE_WITH_PN_QTY = 1
    CONSUMABLE_WITH_PN_SPEC_QTY = 2
    CONSUMABLE_NO_QTY = 3
    CONSUMABLE_NO_PN = 4
    NO_CONSUMABLE_MENTIONED = 5
    CONSUMABLE_PN_MISMATCH = 6
    CONSUMABLE_OBSOLETE_PN = 7
    AMBIGUOUS_CONSUMABLE_NAME = 8
    VENDOR_NAME_ONLY = 9
    MULTIPLE_CONSUMABLES_NO_MAPPING = 10
    PRE_ASSEMBLED_KIT = 11
    WI_MENTIONS_CONSUMABLE_ONLY = 12
    VENDOR_KIT_NO_PN = 13

class ExtractedMaterial(BaseModel):
    """Enhanced material extracted from QA documents by autonomous agents"""

    # Original fields
    name: str
    category: str
    specifications: Dict[str, Any] = {}
    context: str = ""
    confidence_score: float = 0.0
    source_section: str = ""

    # Enhanced QA classification fields
    qc_process_step: Optional[str] = None
    consumable_jigs_tools: bool = False
    name_mismatch: bool = False
    part_number: Optional[str] = None
    pn_mismatch: bool = False
    quantity: Optional[float] = None
    unit_of_measure: Optional[str] = None
    obsolete_pn: bool = False
    vendor_name: Optional[str] = None
    kit_available: bool = False
    ai_engine_processing: str = ""
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    action_path_rag: ActionPathRAG = ActionPathRAG.AMBER
    classification_label: QAClassificationLabel = QAClassificationLabel.NO_CONSUMABLE_MENTIONED
    classification_reasoning: str = ""

class BOMMatch(BaseModel):
    """Enhanced match between QA material and supplier BOM item"""
    qa_material_name: str
    supplier_part_number: str
    supplier_description: str
    confidence_score: float
    match_type: str  # "exact", "semantic", "fuzzy_match"
    qa_excerpt: str = ""
    reasoning: str = ""
    material_category: str = ""
    supplier_category: str = ""
    specifications_match: List[str] = []
    differences: List[str] = []

    # Enhanced QA classification info
    qa_classification_label: Optional[QAClassificationLabel] = None
    qa_action_path: Optional[ActionPathRAG] = None
    qa_confidence_level: Optional[ConfidenceLevel] = None

    # Additional QA fields for results display
    qc_process_step: Optional[str] = None
    consumable_jigs_tools: Optional[bool] = None
    part_number: Optional[str] = None
    pn_mismatch: Optional[bool] = None
    quantity: Optional[float] = None
    unit_of_measure: Optional[str] = None
    vendor_name: Optional[str] = None
    kit_available: Optional[bool] = None
    obsolete_pn: Optional[bool] = None
    name_mismatch: Optional[bool] = None

class QAClassificationSummary(BaseModel):
    """Summary of QA material classifications"""
    total_materials: int
    green_materials: int  # Auto-Register
    amber_materials: int  # Auto with Flag
    red_materials: int    # Human Intervention Required
    classification_breakdown: Dict[str, int] = {}

class BOMComparisonResult(BaseModel):
    """Complete autonomous comparison results with QA classification"""
    workflow_id: str
    matches: List[BOMMatch]
    total_qa_items: int
    total_supplier_items: int
    processing_metadata: Dict[str, Any] = {}
    qa_classification_summary: Optional[QAClassificationSummary] = None

class WorkflowState(BaseModel):
    """Represents the state of an autonomous processing workflow"""
    workflow_id: str
    status: str  # "initialized", "processing", "completed", "error"
    progress: float = 0.0
    current_stage: str = ""
    qa_document_path: str = ""
    supplier_bom_path: str = ""
    message: Optional[str] = None
    results: Optional[BOMComparisonResult] = None
    created_at: datetime
    updated_at: datetime = datetime.utcnow()

class AgentResult(BaseModel):
    """Result from an autonomous agent"""
    success: bool
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    processing_time: Optional[str] = None
    agent_stats: Dict[str, Any] = {}

class AutonomousWorkflowUpdate(BaseModel):
    """WebSocket message for autonomous workflow updates"""
    type: str = "autonomous_workflow_update"
    workflow_id: str
    status: str
    progress: float
    current_stage: str
    message: str
    autonomous: bool = True
    timestamp: str = datetime.utcnow().isoformat()
