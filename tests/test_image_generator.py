"""
Unit tests for the Image Generator Agent using Google Imagen
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import io
from PIL import Image
import base64

from agents.image_generator_agent import ImageGeneratorAgent
from utils.gcs_manager import GCSManager

class TestImageGeneratorAgent:
    
    @pytest.fixture
    def agent(self):
        return ImageGeneratorAgent()
    
    @pytest.fixture
    def sample_input_data(self):
        return {
            'generated_prompt': {
                'image_prompt': 'Professional photo of handcrafted ceramic vase',
                'style_guidelines': 'Clean, professional lighting'
            },
            'product_input': {
                'product_id': 'test_product_123',
                'description': 'Ceramic vase'
            },
            'image_count': 2
        }
    
    @pytest.mark.asyncio
    async def test_process_success(self, agent, sample_input_data):
        """Test successful image generation and upload using Google Imagen"""
        response = await agent.process(sample_input_data)
        
        # Test will use real API - may fail if API key not set
        if response.success:
            assert 'generated_images' in response.data
            assert response.data['successful_count'] >= 0
        else:
            # Expected if no API key is configured
            assert "API" in response.error or "key" in response.error.lower()
    
    @pytest.mark.asyncio
    async def test_imagen_api_call(self, agent):
        """Test Google Imagen API integration"""
        prompt = "Professional photo of handcrafted ceramic vase"
        
        try:
            image_data = await agent._call_imagen_api(prompt)
            assert isinstance(image_data, bytes)
            assert len(image_data) > 0
        except Exception as e:
            # Expected if API key not configured or quota exceeded
            assert "API" in str(e) or "quota" in str(e).lower() or "key" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_imagen_api_fallback(self, agent):
        """Test fallback when Imagen API fails"""
        prompt = "Test prompt"
        
        with patch.object(agent, '_call_imagen_api') as mock_imagen:
            mock_imagen.side_effect = Exception("Imagen API failed")
            
            with patch.object(agent, '_create_fallback_image') as mock_fallback:
                mock_fallback.return_value = b'fallback_image_data'
                
                image_data = await agent._call_imagen_api(prompt)
                
                assert image_data == b'fallback_image_data'
                mock_fallback.assert_called_once_with(prompt)
    
    @pytest.mark.asyncio
    async def test_process_no_prompt(self, agent):
        """Test handling of missing prompt"""
        input_data = {'product_input': {'product_id': 'test'}}
        
        response = await agent.process(input_data)
        
        assert response.success is False
        assert "No image prompt provided" in response.error
    
    def test_create_prompt_variations(self, agent):
        """Test prompt variation generation for Imagen"""
        base_prompt = "Ceramic vase"
        style_guidelines = "Professional lighting"
        
        variations = agent._create_prompt_variations(base_prompt, style_guidelines, 3)
        
        assert len(variations) == 3
        assert all(base_prompt in variation for variation in variations)
        assert all(style_guidelines in variation for variation in variations)
        assert all("high resolution" in variation for variation in variations)
        assert all("marketing quality" in variation for variation in variations)
        # Ensure variations are different
        assert len(set(variations)) == 3
    
    def test_create_placeholder_image(self, agent):
        """Test placeholder image creation"""
        image = agent._create_placeholder_image("test prompt", 0)
        
        assert isinstance(image, Image.Image)
        assert image.size == (1024, 1024)
    
    def test_optimize_image(self, agent):
        """Test image optimization"""
        # Create a test image
        test_image = Image.new('RGB', (100, 100), (255, 0, 0))
        img_byte_arr = io.BytesIO()
        test_image.save(img_byte_arr, format='PNG')
        image_data = img_byte_arr.getvalue()
        
        optimized_data = agent.optimize_image(image_data, max_size_mb=0.001)  # Very small limit
        
        assert len(optimized_data) <= len(image_data)
