"""
Agent 1: Prompt Generator Agent
Analyzes product descriptions and creates optimized prompts for image and video generation
"""

from google import genai
from typing import Dict, Any, Optional
import json
import re

from agents.base_agent import BaseAgent
from models.data_models import AgentResponse, AgentType, ProductInput, GeneratedPrompt
from config.settings import Config

class PromptGeneratorAgent(BaseAgent):
    """Agent responsible for generating optimized prompts for image and video creation"""
    
    def __init__(self):
        super().__init__(AgentType.PROMPT_GENERATOR)
        
        self.client = genai.Client(api_key=Config.GOOGLE_AI_API_KEY)
        
        # Prompt templates
        self.image_prompt_template = """
        You are an expert marketing content creator specializing in artisan products. 
        
        Product Description: {description}
        Optional Image Context: {image_context}
        
        Create a detailed, professional image generation prompt that will produce high-quality marketing images for this artisan product. 
        
        Consider:
        - Product aesthetics and craftsmanship
        - Lighting and composition for marketing appeal
        - Background and styling that enhances the product
        - Target audience and market positioning
        
        Return your response in JSON format with these fields:
        - "image_prompt": Detailed prompt for image generation
        - "style_guidelines": Specific style and aesthetic directions
        - "target_audience": Who this product appeals to
        - "marketing_angle": Key selling points to emphasize
        """
        
        self.video_prompt_template = """
        You are an expert video marketing strategist for artisan products.
        
        Product Description: {description}
        Image Context: {image_context}
        Generated Image Prompts: {image_prompts}
        
        Create a compelling video generation prompt that will produce a {duration}-second marketing video.
        
        Consider:
        - Storytelling elements that showcase craftsmanship
        - Visual transitions and movement
        - Emotional connection with viewers
        - Call-to-action elements
        
        Return your response in JSON format with these fields:
        - "video_prompt": Detailed prompt for video generation
        - "scene_breakdown": Array of scenes with timing
        - "visual_effects": Suggested effects and transitions
        - "music_style": Recommended background music style
        """
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process product input and generate optimized prompts"""
        try:
            # Parse input data
            product_input = ProductInput(**input_data)
            
            self.logger.info(f"Generating prompts for product: {product_input.product_id}")
            
            # Analyze optional image if provided
            image_context = ""
            if product_input.optional_image_url:
                image_context = await self._analyze_image(product_input.optional_image_url)
            
            # Generate image prompts
            image_prompt_data = await self._generate_image_prompt(
                product_input.description, 
                image_context
            )
            
            # Generate video prompt
            video_prompt_data = await self._generate_video_prompt(
                product_input.description,
                image_context,
                image_prompt_data.get('image_prompt', '')
            )
            
            # Create comprehensive prompt object
            generated_prompt = GeneratedPrompt(
                image_prompt=image_prompt_data.get('image_prompt', ''),
                video_prompt=video_prompt_data.get('video_prompt', ''),
                style_guidelines=image_prompt_data.get('style_guidelines', ''),
                target_audience=image_prompt_data.get('target_audience', ''),
                marketing_angle=image_prompt_data.get('marketing_angle', '')
            )
            
            # Prepare response data
            response_data = {
                'generated_prompt': generated_prompt.__dict__,
                'image_prompt_details': image_prompt_data,
                'video_prompt_details': video_prompt_data,
                'product_input': product_input.__dict__,
                'next_agents': ['image_generator', 'video_generator']
            }
            
            self.logger.info(f"Successfully generated prompts for product {product_input.product_id}")
            
            return AgentResponse(
                success=True,
                data=response_data
            )
            
        except Exception as e:
            self.logger.error(f"Error in prompt generation: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Prompt generation failed: {str(e)}"
            )
    
    async def _analyze_image(self, image_url: str) -> str:
        """Analyze optional image to provide context for prompt generation"""
        try:
            # Use Gemini Vision to analyze the image
            import requests
            from PIL import Image
            import io
            
            # Download and process image
            response = requests.get(image_url)
            image = Image.open(io.BytesIO(response.content))
            
            analysis_prompt = """
            Analyze this artisan product image and describe:
            1. Visual style and aesthetics
            2. Lighting and composition
            3. Background and setting
            4. Product positioning and angles
            5. Overall quality and appeal
            
            Provide insights that would help generate similar high-quality marketing images.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[analysis_prompt, image]
            )
            return response.text
            
        except Exception as e:
            self.logger.warning(f"Could not analyze image: {str(e)}")
            return "No image analysis available"
    
    async def _generate_image_prompt(self, description: str, image_context: str) -> Dict[str, Any]:
        """Generate optimized image prompt"""
        try:
            prompt = self.image_prompt_template.format(
                description=description,
                image_context=image_context or "No reference image provided"
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback if JSON parsing fails
                return {
                    "image_prompt": f"Professional marketing photo of {description}, high quality, well-lit, clean background",
                    "style_guidelines": "Clean, professional, high-resolution",
                    "target_audience": "General consumers interested in artisan products",
                    "marketing_angle": "Quality craftsmanship and unique design"
                }
                
        except Exception as e:
            self.logger.error(f"Error generating image prompt: {str(e)}")
            raise
    
    async def _generate_video_prompt(self, description: str, image_context: str, image_prompt: str) -> Dict[str, Any]:
        """Generate optimized video prompt"""
        try:
            prompt = self.video_prompt_template.format(
                description=description,
                image_context=image_context or "No reference image provided",
                image_prompts=image_prompt,
                duration=Config.VIDEO_DURATION
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback if JSON parsing fails
                return {
                    "video_prompt": f"Marketing video showcasing {description}, smooth transitions, professional presentation",
                    "scene_breakdown": [
                        {"time": "0-5s", "scene": "Product introduction"},
                        {"time": "5-10s", "scene": "Detail showcase"},
                        {"time": "10-15s", "scene": "Call to action"}
                    ],
                    "visual_effects": "Smooth transitions, gentle zoom effects",
                    "music_style": "Upbeat, modern, inspiring"
                }
                
        except Exception as e:
            self.logger.error(f"Error generating video prompt: {str(e)}")
            raise
    
    def create_enhanced_prompts(self, base_prompt: str, count: int = 2) -> list:
        """Create multiple variations of the base prompt for diverse image generation"""
        variations = []
        
        style_modifiers = [
            "professional studio lighting, clean white background",
            "natural lighting, rustic wooden background",
            "dramatic lighting, dark moody background",
            "bright daylight, outdoor natural setting"
        ]
        
        angle_modifiers = [
            "front view, centered composition",
            "three-quarter angle, dynamic composition",
            "close-up detail shot, macro photography",
            "lifestyle shot, in-use context"
        ]
        
        for i in range(min(count, len(style_modifiers))):
            enhanced_prompt = f"{base_prompt}, {style_modifiers[i]}, {angle_modifiers[i]}, high resolution, marketing quality"
            variations.append(enhanced_prompt)
        
        return variations
