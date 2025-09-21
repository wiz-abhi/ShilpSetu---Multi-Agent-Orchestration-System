"""
Data models for the multi-agent system
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AgentType(Enum):
    """Types of agents in the system"""
    PROMPT_GENERATOR = "prompt_generator"
    IMAGE_GENERATOR = "image_generator"
    VIDEO_GENERATOR = "video_generator"

class TaskStatus(Enum):
    """Status of agent tasks"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProductInput:
    """Input data for product processing"""
    description: str
    optional_image_url: Optional[str] = None
    user_id: str = ""
    product_id: str = ""
    additional_context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GeneratedPrompt:
    """Generated prompt for image/video creation"""
    image_prompt: str
    video_prompt: str
    style_guidelines: str
    target_audience: str
    marketing_angle: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class GeneratedImage:
    """Generated image data"""
    image_url: str
    gcs_path: str
    prompt_used: str
    generation_params: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class GeneratedVideo:
    """Generated video data"""
    video_url: str
    gcs_path: str
    duration: float
    source_images: List[str]
    prompt_used: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class AgentTask:
    """Task for agent processing"""
    task_id: str
    agent_type: AgentType
    input_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_status(self, status: TaskStatus, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Update task status and timestamp"""
        self.status = status
        self.updated_at = datetime.now()
        if result:
            self.result = result
        if error:
            self.error_message = error

@dataclass
class AgentResponse:
    """Response from an agent"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_type: Optional[AgentType] = None
