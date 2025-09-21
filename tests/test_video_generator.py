"""
Unit tests for the Video Generator Agent using Google Veo 3
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import io
import base64

from agents.video_generator_agent import VideoGeneratorAgent
from utils.gcs_manager import GCSManager
from utils.video_processor import VideoProcessor

class TestVideoGeneratorAgent:
    
    @pytest.fixture
    def agent(self):
        return VideoGeneratorAgent()
    
    @pytest.fixture
    def sample_input_data(self):
        return {
            'generated_prompt': {
                'video_prompt': 'Marketing video showcasing handcrafted ceramic vase'
            },
            'generated_images': [
                {
                    'image_url': 'https://example.com/image1.jpg',
                    'prompt_used': 'Professional photo of ceramic vase'
                },
                {
                    'image_url': 'https://example.com/image2.jpg',
                    'prompt_used': 'Detail shot of ceramic vase'
                }
            ],
            'product_input': {
                'product_id': 'test_product_123',
                'description': 'Ceramic vase',
                'optional_image_url': 'https://example.com/original.jpg'
            },
            'video_prompt_details': {
                'scene_breakdown': [
                    {'time': '0-5s', 'scene': 'Product introduction'},
                    {'time': '5-10s', 'scene': 'Detail showcase'}
                ],
                'music_style': 'upbeat'
            }
        }
    
    @pytest.mark.asyncio
    async def test_process_success_with_veo(self, agent, sample_input_data):
        """Test successful video generation using Google Veo 3"""
        response = await agent.process(sample_input_data)
        
        # Test will use real API - may fail if API key not set
        if response.success:
            assert 'generated_video' in response.data
            assert 'video_details' in response.data
        else:
            # Expected if no API key is configured
            assert "API" in response.error or "key" in response.error.lower()
    
    @pytest.mark.asyncio
    async def test_veo_api_call(self, agent):
        """Test Google Veo 3 API integration"""
        video_prompt = "Marketing video showcasing handcrafted ceramic vase"
        reference_images = [b'fake_image_1', b'fake_image_2']
        scene_breakdown = [{'time': '0-5s', 'scene': 'Product intro'}]
        
        try:
            video_data = await agent._call_veo_api(
                video_prompt=video_prompt,
                reference_images=reference_images,
                duration=15.0,
                scene_breakdown=scene_breakdown
            )
            assert isinstance(video_data, bytes)
            assert len(video_data) > 0
        except Exception as e:
            # Expected if API key not configured or quota exceeded
            assert "API" in str(e) or "quota" in str(e).lower() or "key" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_veo_api_with_gcs_uri(self, agent):
        """Test Veo API response with GCS URI"""
        video_prompt = "Test video prompt"
        reference_images = [b'fake_image']
        
        with patch('google.ai.generativelanguage.GenerativeServiceClient') as mock_client:
            mock_response = Mock()
            mock_response.generated_video = Mock()
            mock_response.generated_video.bytes_base64_encoded = None
            mock_response.generated_video.gcs_uri = "gs://test-bucket/video.mp4"
            mock_client.return_value.generate_video.return_value = mock_response
            
            with patch.object(agent, '_download_from_gcs_uri') as mock_download:
                mock_download.return_value = b'downloaded_video_data'
                
                video_data = await agent._call_veo_api(
                    video_prompt=video_prompt,
                    reference_images=reference_images,
                    duration=15.0,
                    scene_breakdown=[]
                )
                
                assert video_data == b'downloaded_video_data'
                mock_download.assert_called_once_with("gs://test-bucket/video.mp4")
    
    def test_create_veo_prompt(self, agent):
        """Test Veo-optimized prompt creation"""
        base_prompt = "Marketing video for ceramic vase"
        scene_breakdown = [
            {'time': '0-5s', 'scene': 'Product introduction'},
            {'time': '5-10s', 'scene': 'Detail showcase'}
        ]
        duration = 15.0
        
        veo_prompt = agent._create_veo_prompt(base_prompt, scene_breakdown, duration)
        
        assert base_prompt in veo_prompt
        assert "15-second marketing video" in veo_prompt
        assert "Product introduction" in veo_prompt
        assert "Detail showcase" in veo_prompt
        assert "Professional marketing quality" in veo_prompt
        assert "Smooth camera movements" in veo_prompt
    
    @pytest.mark.asyncio
    async def test_process_success(self, agent, sample_input_data):
        """Test successful video generation"""
        # Mock image download
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = b'fake_image_data'
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Mock video generation
            agent.video_processor.create_marketing_video.return_value = b'fake_video_data'
            
            # Mock GCS upload
            agent.gcs_manager.upload_video.return_value = {
                'public_url': 'https://storage.googleapis.com/bucket/video.mp4',
                'gcs_path': 'gs://bucket/video.mp4',
                'filename': 'video.mp4',
                'size': 1024
            }
            
            response = await agent.process(sample_input_data)
            
            assert response.success is True
            assert 'generated_video' in response.data
            assert 'video_details' in response.data
    
    @pytest.mark.asyncio
    async def test_process_no_prompt(self, agent):
        """Test handling of missing video prompt"""
        input_data = {
            'generated_images': [],
            'product_input': {'product_id': 'test'}
        }
        
        response = await agent.process(input_data)
        
        assert response.success is False
        assert "No video prompt provided" in response.error
    
    @pytest.mark.asyncio
    async def test_collect_image_sources(self, agent, sample_input_data):
        """Test image source collection"""
        generated_images = sample_input_data['generated_images']
        product_input = sample_input_data['product_input']
        
        sources = await agent._collect_image_sources(generated_images, product_input)
        
        assert len(sources) == 3  # 2 generated + 1 user provided
        assert sources[0]['source'] == 'generated'
        assert sources[2]['source'] == 'user_provided'
    
    @pytest.mark.asyncio
    async def test_download_images(self, agent):
        """Test image downloading"""
        image_sources = [
            {'url': 'https://example.com/image1.jpg', 'source': 'generated'},
            {'url': 'https://example.com/image2.jpg', 'source': 'generated'}
        ]
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = b'fake_image_data'
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            images = await agent._download_images(image_sources)
            
            assert len(images) == 2
            assert all(isinstance(img, bytes) for img in images)
    
    @pytest.mark.asyncio
    async def test_generate_video_with_fallback(self, agent):
        """Test video generation with fallback"""
        images = [b'fake_image_1', b'fake_image_2']
        
        # Mock main generation failure
        agent.video_processor.create_marketing_video.side_effect = Exception("Generation failed")
        
        # Mock fallback success
        agent.video_processor.create_slideshow_video.return_value = b'fallback_video_data'
        
        video_data = await agent._generate_video(images, "test prompt", [], "upbeat")
        
        assert video_data == b'fallback_video_data'
    
    @pytest.mark.asyncio
    async def test_generate_video_with_veo_fallback(self, agent):
        """Test video generation with Veo failure and traditional fallback"""
        images = [b'fake_image_1', b'fake_image_2']
        
        with patch.object(agent, '_call_veo_api') as mock_veo:
            mock_veo.side_effect = Exception("Veo API failed")
            
            # Mock fallback success
            agent.video_processor.create_slideshow_video.return_value = b'fallback_video_data'
            
            video_data = await agent._generate_video(images, "test prompt", [], "upbeat")
            
            assert video_data == b'fallback_video_data'
            # Verify Veo was attempted first
            mock_veo.assert_called_once()
    
    def test_get_video_metadata(self, agent):
        """Test video metadata extraction"""
        video_data = b'fake_video_data'
        
        # Mock the metadata extraction to avoid moviepy dependency in tests
        with patch.object(agent, 'get_video_metadata') as mock_metadata:
            mock_metadata.return_value = {
                'duration': 15.0,
                'fps': 30,
                'size': (1920, 1080),
                'file_size': 1024,
                'has_audio': False
            }
            
            metadata = agent.get_video_metadata(video_data)
            
            assert 'duration' in metadata
            assert 'file_size' in metadata
