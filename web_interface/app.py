"""
Web interface for the Artisan Marketplace Multi-Agent System
"""

import streamlit as st
import asyncio
import json
import requests
from typing import Optional, Dict, Any
import time
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="Artisan Marketplace AI",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .result-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .success-badge {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    .error-badge {
        background: #dc3545;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    .partial-badge {
        background: #ffc107;
        color: black;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

class WebInterface:
    """Web interface for the multi-agent system"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
    
    def check_api_connection(self) -> bool:
        """Check if the API server is running"""
        try:
            response = requests.get(f"{self.api_base_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_content(self, product_data: Dict[str, Any], workflow_options: Dict[str, Any]) -> Dict[str, Any]:
        """Call the API to generate content"""
        try:
            payload = {
                "product_input": product_data,
                "workflow_options": workflow_options
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/generate-content",
                json=payload,
                timeout=300  # 5 minutes timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout - processing may still be running"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status from API"""
        try:
            response = requests.get(f"{self.api_base_url}/api/system/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎨 Artisan Marketplace AI</h1>
        <p>Generate professional marketing content for your artisan products</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize web interface
    web_interface = WebInterface()
    
    # Check API connection
    if not web_interface.check_api_connection():
        st.error("⚠️ Cannot connect to the API server. Please ensure the API is running on http://localhost:8000")
        st.info("Run the API server with: `python main.py --mode api`")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("🛠️ Configuration")
        
        # Workflow options
        st.subheader("Generation Settings")
        image_count = st.slider("Number of images", 1, 3, 2)
        max_retries = st.slider("Max retries per agent", 1, 5, 3)
        
        # Advanced options
        with st.expander("Advanced Options"):
            include_branding = st.checkbox("Include branding elements")
            custom_style = st.text_input("Custom style (optional)")
            priority = st.selectbox("Priority", ["low", "normal", "high"], index=1)
        
        # System status
        st.subheader("📊 System Status")
        if st.button("Refresh Status"):
            status = web_interface.get_system_status()
            if "error" not in status:
                st.success(f"✅ System operational")
                st.info(f"Active workflows: {status.get('active_workflows', 0)}")
                st.info(f"Total processed: {status.get('total_workflows_processed', 0)}")
            else:
                st.error(f"❌ Status error: {status['error']}")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Product Information")
        
        # Product input form
        with st.form("product_form"):
            description = st.text_area(
                "Product Description",
                placeholder="Describe your artisan product in detail...",
                height=100,
                help="Provide a detailed description of your product including materials, craftsmanship, and unique features"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                user_id = st.text_input("User ID", value="web_user")
                product_id = st.text_input("Product ID", value=f"product_{int(time.time())}")
            
            with col_b:
                optional_image_url = st.text_input(
                    "Reference Image URL (optional)",
                    placeholder="https://example.com/image.jpg"
                )
            
            # Additional context
            with st.expander("Additional Context"):
                category = st.selectbox(
                    "Category",
                    ["", "ceramics", "textiles", "woodwork", "jewelry", "metalwork", "glasswork", "other"]
                )
                price_range = st.selectbox("Price Range", ["", "budget", "mid", "premium", "luxury"])
                target_audience = st.text_input("Target Audience (optional)")
            
            submitted = st.form_submit_button("🚀 Generate Marketing Content", type="primary")
        
        # Process form submission
        if submitted:
            if not description.strip():
                st.error("❌ Product description is required")
            else:
                # Prepare data
                product_data = {
                    "description": description.strip(),
                    "optional_image_url": optional_image_url.strip() if optional_image_url.strip() else None,
                    "user_id": user_id.strip(),
                    "product_id": product_id.strip(),
                    "additional_context": {
                        "category": category,
                        "price_range": price_range,
                        "target_audience": target_audience
                    }
                }
                
                workflow_options = {
                    "image_count": image_count,
                    "max_retries": max_retries,
                    "include_branding": include_branding,
                    "custom_style": custom_style if custom_style.strip() else None,
                    "priority": priority
                }
                
                # Show processing message
                with st.spinner("🎨 Generating marketing content... This may take a few minutes."):
                    result = web_interface.generate_content(product_data, workflow_options)
                
                # Store result in session state
                st.session_state.last_result = result
                st.session_state.last_timestamp = datetime.now()
    
    with col2:
        st.header("💡 Tips")
        st.info("""
        **For best results:**
        - Describe materials and craftsmanship details
        - Mention unique features or techniques
        - Include size, color, and texture information
        - Specify the intended use or occasion
        """)
        
        st.header("📋 Examples")
        with st.expander("Ceramic Vase"):
            st.code("""
Handcrafted ceramic vase with intricate 
blue and white patterns inspired by 
traditional pottery techniques. Features 
a glossy glaze finish and stands 12 
inches tall, perfect for fresh flowers 
or as decorative accent piece.
            """)
        
        with st.expander("Wooden Cutting Board"):
            st.code("""
Sustainable bamboo cutting board with 
natural grain patterns. Hand-sanded 
smooth finish, food-safe treatment, 
and built-in juice groove. Measures 
14x10 inches, ideal for food prep 
and serving.
            """)
    
    # Display results
    if hasattr(st.session_state, 'last_result') and st.session_state.last_result:
        st.header("📊 Results")
        
        result = st.session_state.last_result
        timestamp = st.session_state.last_timestamp
        
        # Result summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if result.get('success'):
                st.markdown('<span class="success-badge">✅ Success</span>', unsafe_allow_html=True)
            elif result.get('partial_success'):
                st.markdown('<span class="partial-badge">⚠️ Partial Success</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="error-badge">❌ Failed</span>', unsafe_allow_html=True)
        
        with col2:
            if 'execution_summary' in result:
                exec_time = result['execution_summary'].get('total_execution_time', 0)
                st.metric("Execution Time", f"{exec_time:.1f}s")
        
        with col3:
            st.metric("Timestamp", timestamp.strftime("%H:%M:%S"))
        
        # Generated content
        if result.get('generated_images'):
            st.subheader("🖼️ Generated Images")
            images = result['generated_images']
            
            cols = st.columns(min(len(images), 3))
            for i, img in enumerate(images):
                with cols[i % 3]:
                    st.image(img.get('image_url', ''), caption=f"Image {i+1}")
                    with st.expander(f"Image {i+1} Details"):
                        st.text(f"URL: {img.get('image_url', 'N/A')}")
                        st.text(f"Prompt: {img.get('prompt_used', 'N/A')[:100]}...")
        
        if result.get('generated_video'):
            st.subheader("🎥 Generated Video")
            video = result['generated_video']
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.video(video.get('video_url', ''))
            with col2:
                st.metric("Duration", f"{video.get('duration', 0)}s")
                st.text(f"URL: {video.get('video_url', 'N/A')}")
        
        # Generated prompts
        if result.get('generated_prompts'):
            with st.expander("📝 Generated Prompts"):
                prompts = result['generated_prompts']
                
                st.subheader("Image Prompt")
                st.text_area("", prompts.get('image_prompt', ''), height=100, disabled=True)
                
                st.subheader("Video Prompt")
                st.text_area("", prompts.get('video_prompt', ''), height=100, disabled=True)
                
                if prompts.get('style_guidelines'):
                    st.subheader("Style Guidelines")
                    st.text(prompts['style_guidelines'])
        
        # Errors
        if result.get('errors'):
            st.subheader("⚠️ Errors")
            for error in result['errors']:
                st.error(error)
        
        # Download results
        st.subheader("💾 Download Results")
        result_json = json.dumps(result, indent=2, default=str)
        st.download_button(
            label="Download JSON Results",
            data=result_json,
            file_name=f"marketing_content_{product_id}_{int(time.time())}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()
