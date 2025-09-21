"""
Agent Orchestrator - Coordinates the multi-agent system workflow
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum

from agents.prompt_generator_agent import PromptGeneratorAgent
from agents.image_generator_agent import ImageGeneratorAgent
from agents.video_generator_agent import VideoGeneratorAgent
from models.data_models import (
    ProductInput, AgentTask, AgentResponse, AgentType, 
    TaskStatus, GeneratedPrompt, GeneratedImage, GeneratedVideo
)
from config.settings import Config
from utils.logger import setup_logger

class WorkflowStatus(Enum):
    """Status of the overall workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"

class AgentOrchestrator:
    """Orchestrates the multi-agent workflow for product marketing content generation"""
    
    def __init__(self):
        self.logger = setup_logger("AgentOrchestrator")
        
        # Initialize agents
        self.prompt_agent = PromptGeneratorAgent()
        self.image_agent = ImageGeneratorAgent()
        self.video_agent = VideoGeneratorAgent()
        
        # Workflow tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        
        # Agent registry
        self.agents = {
            AgentType.PROMPT_GENERATOR: self.prompt_agent,
            AgentType.IMAGE_GENERATOR: self.image_agent,
            AgentType.VIDEO_GENERATOR: self.video_agent
        }
        
        # Workflow configuration
        self.max_concurrent_workflows = 5
        self.workflow_timeout = Config.AGENT_TIMEOUT
    
    async def process_product(
        self, 
        product_input: ProductInput,
        workflow_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing a product through the multi-agent system
        
        Args:
            product_input: Product information and requirements
            workflow_options: Optional configuration for the workflow
            
        Returns:
            Complete workflow results including generated content
        """
        workflow_id = str(uuid.uuid4())
        
        try:
            self.logger.info(f"Starting workflow {workflow_id} for product {product_input.product_id}")
            
            # Initialize workflow tracking
            workflow = self._initialize_workflow(workflow_id, product_input, workflow_options)
            
            # Check concurrent workflow limit
            if len(self.active_workflows) >= self.max_concurrent_workflows:
                raise Exception("Maximum concurrent workflows reached. Please try again later.")
            
            self.active_workflows[workflow_id] = workflow
            
            # Execute the workflow
            result = await self._execute_workflow(workflow_id, product_input, workflow_options or {})
            
            # Update workflow status
            workflow['status'] = WorkflowStatus.COMPLETED if result['success'] else WorkflowStatus.FAILED
            workflow['completed_at'] = datetime.now()
            workflow['result'] = result
            
            # Move to history
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow_id]
            
            self.logger.info(f"Completed workflow {workflow_id} with status: {workflow['status'].value}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            
            # Update workflow status
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                workflow['status'] = WorkflowStatus.FAILED
                workflow['error'] = str(e)
                workflow['completed_at'] = datetime.now()
                
                self.workflow_history.append(workflow)
                del self.active_workflows[workflow_id]
            
            return {
                'success': False,
                'workflow_id': workflow_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _initialize_workflow(
        self, 
        workflow_id: str, 
        product_input: ProductInput,
        workflow_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Initialize workflow tracking structure"""
        return {
            'workflow_id': workflow_id,
            'product_input': product_input.__dict__,
            'workflow_options': workflow_options or {},
            'status': WorkflowStatus.PENDING,
            'created_at': datetime.now(),
            'completed_at': None,
            'agents_executed': [],
            'current_agent': None,
            'result': None,
            'error': None
        }
    
    async def _execute_workflow(
        self, 
        workflow_id: str, 
        product_input: ProductInput,
        workflow_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the complete multi-agent workflow"""
        
        workflow = self.active_workflows[workflow_id]
        workflow['status'] = WorkflowStatus.RUNNING
        
        try:
            # Step 1: Generate prompts (Agent 1)
            self.logger.info(f"Workflow {workflow_id}: Starting prompt generation")
            workflow['current_agent'] = AgentType.PROMPT_GENERATOR.value
            
            prompt_response = await self.prompt_agent.execute_with_retry(
                product_input.__dict__,
                max_retries=workflow_options.get('max_retries', Config.MAX_RETRIES)
            )
            
            if not prompt_response.success:
                raise Exception(f"Prompt generation failed: {prompt_response.error}")
            
            workflow['agents_executed'].append({
                'agent': AgentType.PROMPT_GENERATOR.value,
                'status': 'completed',
                'execution_time': prompt_response.execution_time
            })
            
            # Step 2: Generate images (Agent 2)
            self.logger.info(f"Workflow {workflow_id}: Starting image generation")
            workflow['current_agent'] = AgentType.IMAGE_GENERATOR.value
            
            # Prepare input for image agent
            image_input = {
                **prompt_response.data,
                'image_count': workflow_options.get('image_count', Config.IMAGE_COUNT_DEFAULT)
            }
            
            image_response = await self.image_agent.execute_with_retry(
                image_input,
                max_retries=workflow_options.get('max_retries', Config.MAX_RETRIES)
            )
            
            workflow['agents_executed'].append({
                'agent': AgentType.IMAGE_GENERATOR.value,
                'status': 'completed' if image_response.success else 'failed',
                'execution_time': image_response.execution_time,
                'error': image_response.error if not image_response.success else None
            })
            
            # Step 3: Generate video (Agent 3)
            self.logger.info(f"Workflow {workflow_id}: Starting video generation")
            workflow['current_agent'] = AgentType.VIDEO_GENERATOR.value
            
            # Prepare input for video agent
            video_input = {
                **prompt_response.data,
                'generated_images': image_response.data.get('generated_images', []) if image_response.success else [],
                'workflow_options': workflow_options
            }
            
            video_response = await self.video_agent.execute_with_retry(
                video_input,
                max_retries=workflow_options.get('max_retries', Config.MAX_RETRIES)
            )
            
            workflow['agents_executed'].append({
                'agent': AgentType.VIDEO_GENERATOR.value,
                'status': 'completed' if video_response.success else 'failed',
                'execution_time': video_response.execution_time,
                'error': video_response.error if not video_response.success else None
            })
            
            # Compile final results
            workflow['current_agent'] = None
            
            return self._compile_workflow_results(
                workflow_id,
                prompt_response,
                image_response,
                video_response,
                workflow_options
            )
            
        except asyncio.TimeoutError:
            raise Exception(f"Workflow timeout after {self.workflow_timeout} seconds")
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} execution failed: {str(e)}")
            raise
    
    def _compile_workflow_results(
        self,
        workflow_id: str,
        prompt_response: AgentResponse,
        image_response: AgentResponse,
        video_response: AgentResponse,
        workflow_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile results from all agents into final response"""
        
        # Determine overall success
        success = prompt_response.success
        partial_success = False
        
        # Check for partial success scenarios
        if success and not image_response.success and not video_response.success:
            partial_success = True
        elif success and image_response.success and not video_response.success:
            partial_success = True
        
        overall_success = success and image_response.success and video_response.success
        
        # Compile results
        result = {
            'success': overall_success,
            'partial_success': partial_success,
            'workflow_id': workflow_id,
            'timestamp': datetime.now().isoformat(),
            'execution_summary': {
                'total_execution_time': (
                    prompt_response.execution_time + 
                    image_response.execution_time + 
                    video_response.execution_time
                ),
                'agents_succeeded': sum([
                    1 if prompt_response.success else 0,
                    1 if image_response.success else 0,
                    1 if video_response.success else 0
                ]),
                'agents_failed': sum([
                    0 if prompt_response.success else 1,
                    0 if image_response.success else 1,
                    0 if video_response.success else 1
                ])
            }
        }
        
        # Add successful results
        if prompt_response.success:
            result['generated_prompts'] = prompt_response.data.get('generated_prompt', {})
            result['prompt_details'] = {
                'image_prompt_details': prompt_response.data.get('image_prompt_details', {}),
                'video_prompt_details': prompt_response.data.get('video_prompt_details', {})
            }
        
        if image_response.success:
            result['generated_images'] = image_response.data.get('generated_images', [])
            result['image_generation_stats'] = {
                'successful_count': image_response.data.get('successful_count', 0),
                'failed_count': image_response.data.get('failed_count', 0),
                'generation_settings': image_response.data.get('generation_settings', {})
            }
        
        if video_response.success:
            result['generated_video'] = video_response.data.get('generated_video', {})
            result['video_details'] = video_response.data.get('video_details', {})
        
        # Add error information for failed agents
        errors = []
        if not prompt_response.success:
            errors.append(f"Prompt generation: {prompt_response.error}")
        if not image_response.success:
            errors.append(f"Image generation: {image_response.error}")
        if not video_response.success:
            errors.append(f"Video generation: {video_response.error}")
        
        if errors:
            result['errors'] = errors
        
        return result
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a workflow"""
        # Check active workflows
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            return {
                'workflow_id': workflow_id,
                'status': workflow['status'].value,
                'current_agent': workflow.get('current_agent'),
                'agents_executed': workflow.get('agents_executed', []),
                'created_at': workflow['created_at'].isoformat(),
                'is_active': True
            }
        
        # Check workflow history
        for workflow in self.workflow_history:
            if workflow['workflow_id'] == workflow_id:
                return {
                    'workflow_id': workflow_id,
                    'status': workflow['status'].value,
                    'agents_executed': workflow.get('agents_executed', []),
                    'created_at': workflow['created_at'].isoformat(),
                    'completed_at': workflow.get('completed_at', {}).isoformat() if workflow.get('completed_at') else None,
                    'is_active': False,
                    'result_available': workflow.get('result') is not None
                }
        
        return None
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow['status'] = WorkflowStatus.FAILED
            workflow['error'] = "Workflow cancelled by user"
            workflow['completed_at'] = datetime.now()
            
            # Move to history
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow_id]
            
            self.logger.info(f"Cancelled workflow {workflow_id}")
            return True
        
        return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status and statistics"""
        return {
            'active_workflows': len(self.active_workflows),
            'max_concurrent_workflows': self.max_concurrent_workflows,
            'total_workflows_processed': len(self.workflow_history),
            'agent_status': {
                agent_type.value: {
                    'is_busy': agent.is_busy,
                    'last_activity': agent.last_activity.isoformat()
                }
                for agent_type, agent in self.agents.items()
            },
            'recent_workflows': [
                {
                    'workflow_id': w['workflow_id'],
                    'status': w['status'].value,
                    'created_at': w['created_at'].isoformat(),
                    'completed_at': w.get('completed_at', {}).isoformat() if w.get('completed_at') else None
                }
                for w in self.workflow_history[-10:]  # Last 10 workflows
            ]
        }
    
    async def process_batch(
        self, 
        product_inputs: List[ProductInput],
        batch_options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple products in batch"""
        batch_id = str(uuid.uuid4())
        self.logger.info(f"Starting batch processing {batch_id} with {len(product_inputs)} products")
        
        batch_options = batch_options or {}
        max_concurrent = batch_options.get('max_concurrent', 3)
        
        # Create semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_product(product_input: ProductInput) -> Dict[str, Any]:
            async with semaphore:
                return await self.process_product(product_input, batch_options.get('workflow_options'))
        
        # Process all products concurrently (with limit)
        tasks = [process_single_product(product_input) for product_input in product_inputs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    'product_id': product_inputs[i].product_id,
                    'error': str(result)
                })
            elif result.get('success') or result.get('partial_success'):
                successful_results.append(result)
            else:
                failed_results.append(result)
        
        batch_summary = {
            'batch_id': batch_id,
            'total_products': len(product_inputs),
            'successful_count': len(successful_results),
            'failed_count': len(failed_results),
            'success_rate': len(successful_results) / len(product_inputs) * 100,
            'results': successful_results,
            'failures': failed_results,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Completed batch {batch_id}: {len(successful_results)}/{len(product_inputs)} successful")
        
        return batch_summary
