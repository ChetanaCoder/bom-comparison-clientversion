"""
Enhanced Autonomous BOM Comparison Platform - Main FastAPI Application with QA Classification
"""

import asyncio
import json
import logging
import os
import uuid
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import aiofiles
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from agents.agent_orchestrator import AgentOrchestrator
from models.schemas import WorkflowState, BOMComparisonResult, AutonomousWorkflowUpdate
from utils.gemini_client import GeminiClient

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced Autonomous BOM Comparison Platform",
    description="AI-powered document processing with QA classification system",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize autonomous agents
gemini_client = GeminiClient()
orchestrator = AgentOrchestrator(gemini_client)

# In-memory storage for workflows and WebSocket connections
workflows: Dict[str, WorkflowState] = {}
websocket_connections: Dict[str, WebSocket] = {}

# Ensure required directories exist
Path("uploads").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)
Path("temp").mkdir(exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("🚀 Enhanced Autonomous BOM Platform starting up with QA classification...")

    # Check Gemini API availability
    if gemini_client.is_available():
        logger.info("✅ Gemini API configured and ready")
    else:
        logger.warning("⚠️  Gemini API not configured - using demo mode")

    logger.info("🤖 Autonomous agents initialized")
    logger.info("📊 QA classification system enabled")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "autonomous_agents": "enabled",
        "qa_classification": "enabled",
        "gemini_api": gemini_client.is_available()
    }

@app.post("/api/upload")
async def upload_documents(
    qa_document: UploadFile = File(...),
    supplier_bom: UploadFile = File(...)
):
    """Upload QA document and supplier BOM for autonomous processing with QA classification"""
    try:
        # Validate file types
        qa_allowed_types = [".pdf", ".docx", ".doc", ".txt"]
        bom_allowed_types = [".xlsx", ".xls", ".csv"]

        qa_ext = Path(qa_document.filename).suffix.lower()
        bom_ext = Path(supplier_bom.filename).suffix.lower()

        if qa_ext not in qa_allowed_types:
            raise HTTPException(400, f"Invalid QA document type. Allowed: {qa_allowed_types}")

        if bom_ext not in bom_allowed_types:
            raise HTTPException(400, f"Invalid supplier BOM type. Allowed: {bom_allowed_types}")

        # Generate workflow ID
        workflow_id = str(uuid.uuid4())
        logger.info(f"Starting autonomous workflow {workflow_id}")

        # Create workflow directory
        workflow_dir = Path("uploads") / workflow_id
        workflow_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded files
        qa_path = workflow_dir / f"qa_document{qa_ext}"
        bom_path = workflow_dir / f"supplier_bom{bom_ext}"

        async with aiofiles.open(qa_path, 'wb') as f:
            content = await qa_document.read()
            await f.write(content)

        async with aiofiles.open(bom_path, 'wb') as f:
            content = await supplier_bom.read()
            await f.write(content)

        # Initialize workflow state
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status="initialized",
            progress=0.0,
            current_stage="upload",
            qa_document_path=str(qa_path),
            supplier_bom_path=str(bom_path),
            message="Documents uploaded, starting autonomous processing with QA classification...",
            created_at=datetime.utcnow()
        )

        workflows[workflow_id] = workflow_state

        # Start autonomous processing in background
        asyncio.create_task(process_workflow_async(workflow_id))

        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Documents uploaded successfully. Autonomous processing started with QA classification.",
            "qa_document": qa_document.filename,
            "supplier_bom": supplier_bom.filename,
            "autonomous": True,
            "qa_classification": True
        }

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")

async def process_workflow_async(workflow_id: str):
    """Process workflow asynchronously with real-time updates"""
    try:
        workflow = workflows.get(workflow_id)
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            return

        async def progress_callback(stage: str, progress: float, message: str):
            """Update workflow progress and notify WebSocket clients"""
            workflow.status = "processing" if progress < 100 else "completed"
            workflow.progress = progress
            workflow.current_stage = stage
            workflow.message = message
            workflow.updated_at = datetime.utcnow()

            # Send WebSocket update
            await broadcast_workflow_update(workflow_id, workflow.status, progress, stage, message)

        # Process documents with enhanced orchestrator
        logger.info(f"Starting autonomous processing for workflow {workflow_id}")
        result = await orchestrator.process_documents(
            workflow.qa_document_path,
            workflow.supplier_bom_path,
            workflow_id,
            progress_callback
        )

        # Save results
        workflow.results = result
        workflow.status = "completed"
        workflow.progress = 100.0
        workflow.message = f"Autonomous processing completed with QA classification - {result.qa_classification_summary.green_materials if result.qa_classification_summary else 0} auto-register, {result.qa_classification_summary.amber_materials if result.qa_classification_summary else 0} flagged, {result.qa_classification_summary.red_materials if result.qa_classification_summary else 0} need intervention"
        workflow.updated_at = datetime.utcnow()

        # Final WebSocket notification
        await broadcast_workflow_update(
            workflow_id, 
            "completed", 
            100.0, 
            "complete", 
            workflow.message
        )

        logger.info(f"Autonomous workflow {workflow_id} completed successfully with QA classification")

    except Exception as e:
        logger.error(f"Autonomous processing error for {workflow_id}: {e}")

        # Update workflow with error
        if workflow_id in workflows:
            workflows[workflow_id].status = "error"
            workflows[workflow_id].message = f"Processing failed: {str(e)}"
            workflows[workflow_id].updated_at = datetime.utcnow()

            # Send error notification
            await broadcast_workflow_update(workflow_id, "error", 0.0, "error", str(e))

async def broadcast_workflow_update(workflow_id: str, status: str, progress: float, stage: str, message: str):
    """Broadcast workflow update to all connected WebSocket clients"""
    update = AutonomousWorkflowUpdate(
        workflow_id=workflow_id,
        status=status,
        progress=progress,
        current_stage=stage,
        message=message,
        autonomous=True,
        timestamp=datetime.utcnow().isoformat()
    )

    # Send to all connected clients
    disconnected_clients = []
    for client_id, websocket in websocket_connections.items():
        try:
            await websocket.send_text(update.json())
        except Exception as e:
            logger.warning(f"Failed to send update to client {client_id}: {e}")
            disconnected_clients.append(client_id)

    # Clean up disconnected clients
    for client_id in disconnected_clients:
        websocket_connections.pop(client_id, None)

@app.get("/api/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get current workflow status"""
    workflow = workflows.get(workflow_id)
    if not workflow:
        raise HTTPException(404, "Workflow not found")

    return workflow.dict()

@app.get("/api/results/{workflow_id}")
async def get_results(workflow_id: str):
    """Get processing results with QA classification"""
    workflow = workflows.get(workflow_id)
    if not workflow:
        raise HTTPException(404, "Workflow not found")

    if workflow.status != "completed" or not workflow.results:
        raise HTTPException(400, "Results not available yet")

    return workflow.results.dict()

@app.get("/api/intermediate/{workflow_id}")
async def get_intermediate_results(workflow_id: str, stage: str = None):
    """Get intermediate processing results"""
    workflow_dir = Path("uploads") / workflow_id
    if not workflow_dir.exists():
        raise HTTPException(404, "Workflow not found")

    if stage:
        result_file = workflow_dir / f"{stage}_autonomous_result.json"
        if result_file.exists():
            async with aiofiles.open(result_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        else:
            raise HTTPException(404, f"Stage {stage} results not found")

    # Return all available intermediate results
    results = {}
    for result_file in workflow_dir.glob("*_autonomous_result.json"):
        stage_name = result_file.stem.replace("_autonomous_result", "")
        async with aiofiles.open(result_file, 'r') as f:
            content = await f.read()
            results[stage_name] = json.loads(content)

    return results

@app.get("/api/workflows")
async def list_workflows():
    """List all workflows"""
    workflow_list = []
    for workflow in workflows.values():
        workflow_dict = workflow.dict()
        # Remove large results from list view
        workflow_dict.pop("results", None)
        workflow_list.append(workflow_dict)

    # Sort by creation date (newest first)
    workflow_list.sort(key=lambda x: x["created_at"], reverse=True)

    return {
        "workflows": workflow_list,
        "total": len(workflow_list)
    }

@app.get("/api/agent_stats")
async def get_agent_stats():
    """Get autonomous agent statistics"""
    try:
        stats = await orchestrator.get_processing_statistics()
        return {
            "autonomous_agents": stats,
            "platform_info": {
                "gemini_configured": gemini_client.is_available(),
                "qa_classification_enabled": True,
                "classification_rules": 13,
                "version": "2.0.0"
            }
        }
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        return {
            "autonomous_agents": {
                "orchestrator_type": "autonomous_with_qa_classification", 
                "agents_available": False,
                "error": str(e)
            },
            "platform_info": {
                "gemini_configured": False,
                "qa_classification_enabled": True,
                "error": str(e)
            }
        }

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_connections[client_id] = websocket

    logger.info(f"WebSocket client {client_id} connected")

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "subscribe_workflow":
                workflow_id = message.get("workflow_id")
                logger.info(f"Client {client_id} subscribed to workflow {workflow_id}")

                # Send current status if workflow exists
                if workflow_id in workflows:
                    workflow = workflows[workflow_id]
                    update = AutonomousWorkflowUpdate(
                        workflow_id=workflow_id,
                        status=workflow.status,
                        progress=workflow.progress,
                        current_stage=workflow.current_stage,
                        message=workflow.message,
                        autonomous=True
                    )
                    await websocket.send_text(update.json())

    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        websocket_connections.pop(client_id, None)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )
