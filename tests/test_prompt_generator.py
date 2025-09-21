"""
Unit tests for the Prompt Generator Agent
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from agents.prompt_generator_agent import PromptGeneratorAgent
from models.data_models import ProductInput

class TestPromptGeneratorAgent:
    
    @pytest.fixture
    def agent(self):
        return PromptGeneratorAgent()
    
    @pytest.fixture
    def sample_product_input(self):
        return {
            "description": "Handcrafted ceramic vase with blue glaze and intricate patterns",
            "optional_image_url": None,
            "user_id": "test_user_123",
            "product_id": "test_product_456"
        }
    
    @pytest.mark.asyncio
    async def test_process_success(self, agent, sample_product_input):
        """Test successful prompt generation"""
        response = await agent.process(sample_product_input)
        
        assert response.success is True
        assert 'generated_prompt' in response.data
        assert 'next_agents' in response.data
    
    @pytest.mark.asyncio
    async def test_process_with_image(self, agent, sample_product_input):
        """Test prompt generation with optional image"""
        sample_product_input['optional_image_url'] = 'https://example.com/image.jpg'
        
        response = await agent.process(sample_product_input)
        
        # Test will use real API - may fail if API key not set
        if response.success:
            assert 'generated_prompt' in response.data
        else:
            # Expected if no API key is configured
            assert "API" in response.error or "key" in response.error.lower()
    
    def test_create_enhanced_prompts(self, agent):
        """Test prompt variation generation"""
        base_prompt = "Ceramic vase with blue glaze"
        variations = agent.create_enhanced_prompts(base_prompt, count=2)
        
        assert len(variations) == 2
        assert all(base_prompt in variation for variation in variations)
        assert variations[0] != variations[1]  # Should be different variations
    
    @pytest.mark.asyncio
    async def test_error_handling(self, agent, sample_product_input):
        """Test error handling in prompt generation"""
        # This will test actual API error scenarios
        invalid_input = {'invalid': 'data'}
        
        response = await agent.process(invalid_input)
        
        assert response.success is False
        assert "failed" in response.error.lower()
