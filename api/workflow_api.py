"""
API endpoints for the multi-agent workflow system
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio

from agents.orchestrator import AgentOrchestrator
from models.data_models import ProductInput

# Initialize FastAPI app
app = FastAPI(
    title="Artisan Marketplace Multi-Agent System",
    description="AI-powered content generation for artisan products",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = AgentOrchestrator()

# Pydantic models for API
class ProductInputAPI(BaseModel):
    description: str
    optional_image_url: Optional[str] = None
    user_id: str
    product_id: str
    additional_context: Dict[str, Any] = {}

class WorkflowOptionsAPI(BaseModel):
    image_count: Optional[int] = 2
    max_retries: Optional[int] = 3
    priority: Optional[str] = "normal"
    include_branding: Optional[bool] = False
    custom_style: Optional[str] = None

class BatchProcessRequest(BaseModel):
    products: List[ProductInputAPI]
    batch_options: Optional[Dict[str, Any]] = {}

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "service": "Artisan Marketplace Multi-Agent System",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "generate_content": "/api/generate-content",
            "batch_process": "/api/batch-process",
            "workflow_status": "/api/workflow/{workflow_id}/status",
            "system_status": "/api/system/status"
        }
    }

@app.post("/api/generate-content")
async def generate_content(
    product_input: ProductInputAPI,
    workflow_options: Optional[WorkflowOptionsAPI] = None
):
    """Generate marketing content for a single product"""
    try:
        # Convert API models to internal models
        product = ProductInput(
            description=product_input.description,
            optional_image_url=product_input.optional_image_url,
            user_id=product_input.user_id,
            product_id=product_input.product_id,
            additional_context=product_input.additional_context
        )
        
        options = workflow_options.dict() if workflow_options else {}
        
        # Process the product
        result = await orchestrator.process_product(product, options)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch-process")
async def batch_process(request: BatchProcessRequest):
    """Process multiple products in batch"""
    try:
        # Convert API models to internal models
        products = [
            ProductInput(
                description=p.description,
                optional_image_url=p.optional_image_url,
                user_id=p.user_id,
                product_id=p.product_id,
                additional_context=p.additional_context
            )
            for p in request.products
        ]
        
        # Process batch
        result = await orchestrator.process_batch(products, request.batch_options)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get the status of a specific workflow"""
    status = await orchestrator.get_workflow_status(workflow_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return status

@app.delete("/api/workflow/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """Cancel an active workflow"""
    success = await orchestrator.cancel_workflow(workflow_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found or already completed")
    
    return {"message": "Workflow cancelled successfully"}

@app.get("/api/system/status")
async def get_system_status():
    """Get overall system status and statistics"""
    return orchestrator.get_system_status()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0"
    }

# Background task for cleanup
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    print("🚀 Artisan Marketplace Multi-Agent System starting up...")
    print("✓ Orchestrator initialized")
    print("✓ API endpoints registered")
    print("✓ System ready to process requests")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Artisan Marketplace Multi-Agent System shutting down...")
    
    # Cancel any active workflows
    active_workflows = list(orchestrator.active_workflows.keys())
    for workflow_id in active_workflows:
        await orchestrator.cancel_workflow(workflow_id)
    
    print("✓ All workflows cancelled")
    print("✓ System shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
