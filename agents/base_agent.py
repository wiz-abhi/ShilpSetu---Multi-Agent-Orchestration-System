"""
Base agent class for the multi-agent system
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import time

from models.data_models import AgentResponse, AgentType
from utils.logger import setup_logger

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.logger = setup_logger(f"Agent_{agent_type.value}")
        self.is_busy = False
        self.last_activity = datetime.now()
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process input data and return response"""
        pass
    
    async def execute_with_retry(self, input_data: Dict[str, Any], max_retries: int = 3) -> AgentResponse:
        """Execute agent process with retry logic"""
        start_time = time.time()
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Executing {self.agent_type.value} - Attempt {attempt + 1}")
                self.is_busy = True
                
                response = await self.process(input_data)
                
                self.is_busy = False
                self.last_activity = datetime.now()
                
                execution_time = time.time() - start_time
                response.execution_time = execution_time
                response.agent_type = self.agent_type
                
                if response.success:
                    self.logger.info(f"Successfully completed {self.agent_type.value} in {execution_time:.2f}s")
                    return response
                else:
                    self.logger.warning(f"Agent {self.agent_type.value} returned failure: {response.error}")
                    
            except Exception as e:
                self.logger.error(f"Error in {self.agent_type.value} attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    self.is_busy = False
                    return AgentResponse(
                        success=False,
                        error=f"Failed after {max_retries} attempts: {str(e)}",
                        execution_time=time.time() - start_time,
                        agent_type=self.agent_type
                    )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        self.is_busy = False
        return AgentResponse(
            success=False,
            error="Max retries exceeded",
            execution_time=time.time() - start_time,
            agent_type=self.agent_type
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_type": self.agent_type.value,
            "is_busy": self.is_busy,
            "last_activity": self.last_activity.isoformat()
        }
