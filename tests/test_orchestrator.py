"""
Unit tests for the Agent Orchestrator
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from agents.orchestrator import AgentOrchestrator, WorkflowStatus
from models.data_models import ProductInput, AgentResponse

class TestAgentOrchestrator:
    
    @pytest.fixture
    def orchestrator(self):
        with patch('agents.orchestrator.PromptGeneratorAgent'), \
             patch('agents.orchestrator.ImageGeneratorAgent'), \
             patch('agents.orchestrator.VideoGeneratorAgent'):
            return AgentOrchestrator()
    
    @pytest.fixture
    def sample_product_input(self):
        return ProductInput(
            description="Handcrafted ceramic vase with blue glaze",
            user_id="test_user_123",
            product_id="test_product_456"
        )
    
    @pytest.mark.asyncio
    async def test_process_product_success(self, orchestrator, sample_product_input):
        """Test successful product processing through all agents"""
        # Mock agent responses
        orchestrator.prompt_agent.execute_with_retry = AsyncMock(return_value=AgentResponse(
            success=True,
            data={'generated_prompt': {'image_prompt': 'test prompt'}}
        ))
        
        orchestrator.image_agent.execute_with_retry = AsyncMock(return_value=AgentResponse(
            success=True,
            data={'generated_images': [{'image_url': 'test.jpg'}]}
        ))
        
        orchestrator.video_agent.execute_with_retry = AsyncMock(return_value=AgentResponse(
            success=True,
            data={'generated_video': {'video_url': 'test.mp4'}}
        ))
        
        result = await orchestrator.process_product(sample_product_input)
        
        assert result['success'] is True
        assert 'workflow_id' in result
        assert 'generated_prompts' in result
        assert 'generated_images' in result
        assert 'generated_video' in result
    
    @pytest.mark.asyncio
    async def test_process_product_partial_success(self, orchestrator, sample_product_input):
        """Test partial success when some agents fail"""
        # Mock responses - prompt and image succeed, video fails
        orchestrator.prompt_agent.execute_with_retry = AsyncMock(return_value=AgentResponse(
            success=True,
            data={'generated_prompt': {'image_prompt': 'test prompt'}}
        ))
        
        orchestrator.image_agent.execute_with_retry = AsyncMock(return_value=AgentResponse(
            success=True,
            data={'generated_images': [{'image_url': 'test.jpg'}]}
        ))
        
        orchestrator.video_agent.execute_with_retry = AsyncMock(return_value=AgentResponse(
            success=False,
            error="Video generation failed"
        ))
        
        result = await orchestrator.process_product(sample_product_input)
        
        assert result['success'] is False
        assert result['partial_success'] is True
        assert 'generated_prompts' in result
        assert 'generated_images' in result
        assert 'errors' in result
    
    @pytest.mark.asyncio
    async def test_process_product_complete_failure(self, orchestrator, sample_product_input):
        """Test complete failure when prompt generation fails"""
        orchestrator.prompt_agent.execute_with_retry = AsyncMock(return_value=AgentResponse(
            success=False,
            error="Prompt generation failed"
        ))
        
        result = await orchestrator.process_product(sample_product_input)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_get_workflow_status(self, orchestrator, sample_product_input):
        """Test workflow status retrieval"""
        # Start a workflow
        task = asyncio.create_task(orchestrator.process_product(sample_product_input))
        
        # Give it a moment to start
        await asyncio.sleep(0.1)
        
        # Get active workflows
        active_workflows = list(orchestrator.active_workflows.keys())
        
        if active_workflows:
            workflow_id = active_workflows[0]
            status = await orchestrator.get_workflow_status(workflow_id)
            
            assert status is not None
            assert status['workflow_id'] == workflow_id
            assert 'status' in status
        
        # Cancel the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, orchestrator):
        """Test batch processing of multiple products"""
        products = [
            ProductInput(description=f"Product {i}", user_id="user", product_id=f"prod_{i}")
            for i in range(3)
        ]
        
        # Mock successful responses for all agents
        orchestrator.prompt_agent.execute_with_retry = AsyncMock(return_value=AgentResponse(
            success=True,
            data={'generated_prompt': {'image_prompt': 'test prompt'}}
        ))
        
        orchestrator.image_agent.execute_with_retry = AsyncMock(return_value=AgentResponse(
            success=True,
            data={'generated_images': [{'image_url': 'test.jpg'}]}
        ))
        
        orchestrator.video_agent.execute_with_retry = AsyncMock(return_value=AgentResponse(
            success=True,
            data={'generated_video': {'video_url': 'test.mp4'}}
        ))
        
        result = await orchestrator.process_batch(products)
        
        assert 'batch_id' in result
        assert result['total_products'] == 3
        assert result['successful_count'] >= 0
        assert 'results' in result
    
    def test_system_status(self, orchestrator):
        """Test system status retrieval"""
        status = orchestrator.get_system_status()
        
        assert 'active_workflows' in status
        assert 'max_concurrent_workflows' in status
        assert 'agent_status' in status
        assert 'recent_workflows' in status
    
    @pytest.mark.asyncio
    async def test_cancel_workflow(self, orchestrator, sample_product_input):
        """Test workflow cancellation"""
        # Mock agents to simulate long-running tasks
        orchestrator.prompt_agent.execute_with_retry = AsyncMock(
            side_effect=lambda *args, **kwargs: asyncio.sleep(10)
        )
        
        # Start workflow
        task = asyncio.create_task(orchestrator.process_product(sample_product_input))
        
        # Give it a moment to start
        await asyncio.sleep(0.1)
        
        # Get workflow ID
        active_workflows = list(orchestrator.active_workflows.keys())
        
        if active_workflows:
            workflow_id = active_workflows[0]
            
            # Cancel workflow
            success = await orchestrator.cancel_workflow(workflow_id)
            assert success is True
            
            # Verify it's no longer active
            assert workflow_id not in orchestrator.active_workflows
        
        # Cancel the task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
