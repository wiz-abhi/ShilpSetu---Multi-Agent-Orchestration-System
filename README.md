# Artisan Marketplace Multi-Agent System

A sophisticated multi-agent system powered by Google's latest AI models for automating product marketing content generation for artisan marketplaces. This system uses **Gemini 2.5 Flash**, **Imagen 3.0**, and **Veo 3.0** to create compelling marketing materials.

## 🎯 System Overview

This system consists of three specialized AI agents that work together seamlessly:

### 🤖 Agent 1: Prompt Generator (Gemini 2.5 Flash)
- Analyzes product descriptions and optional reference images
- Creates optimized prompts for image and video generation
- Provides marketing insights and target audience analysis
- Uses advanced vision capabilities for image context analysis

### 🖼️ Agent 2: Image Generator (Imagen 3.0)
- Generates high-quality product marketing images
- Creates multiple variations with different styles and angles
- Automatically optimizes and stores images in Google Cloud Storage
- Includes fallback mechanisms for reliability

### 🎥 Agent 3: Video Generator (Veo 3.0)
- Creates professional marketing videos from images and prompts
- Supports scene-by-scene video generation with smooth transitions
- Handles multiple reference images and complex video prompts
- Includes traditional video processing fallbacks

## ✨ Key Features

- **🚀 Latest Google AI Models**: Powered by Gemini 2.5 Flash, Imagen 3.0, and Veo 3.0
- **🔄 Automated Orchestration**: Agents communicate and invoke each other seamlessly
- **☁️ Cloud Storage Integration**: Automatic storage and management in Google Cloud Storage
- **📈 Scalable Architecture**: Handles multiple concurrent requests with workflow management
- **🛡️ Robust Error Handling**: Comprehensive retry logic and fallback mechanisms
- **🎛️ Multiple Interfaces**: CLI, Interactive mode, Batch processing, and REST API
- **📊 Real-time Monitoring**: System status tracking and workflow monitoring
- **🔧 Highly Configurable**: Extensive configuration options for all aspects

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Google AI API access (Gemini, Imagen, Veo)
- Google Cloud Storage bucket
- Service account credentials

### 1. Install Dependencies
\`\`\`bash
# Clone the repository
git clone <repository-url>
cd artisan-marketplace-agents

# Install Python dependencies
pip install google-genai>=0.3.0
pip install -r requirements.txt

# Or use the setup script
python scripts/setup_dependencies.py
\`\`\`

### 2. Configure Environment
\`\`\`bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
\`\`\`

### 3. Required Environment Variables
\`\`\`env
# Essential Configuration
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
GCS_BUCKET_NAME=your-bucket-name
GCS_CREDENTIALS_PATH=path/to/service-account.json

# Model Configuration (latest versions)
GEMINI_MODEL=gemini-2.5-flash
IMAGEN_MODEL=imagen-3.0-generate-001
VEO_MODEL=veo-3.0-generate-001
\`\`\`

### 4. Set up Google Cloud Storage
\`\`\`bash
# Test GCS connection
python scripts/test_gcs_connection.py

# Test video generation capabilities
python scripts/test_video_generation.py
\`\`\`

## 🚀 Usage Examples

### Interactive Mode (Recommended for Testing)
\`\`\`bash
python main.py --mode interactive
\`\`\`

### Single Product Processing
\`\`\`bash
python main.py --mode single \
  --description "Handcrafted ceramic vase with blue glaze patterns" \
  --user-id "artisan_001" \
  --product-id "ceramic_vase_001" \
  --image-count 3 \
  --output-file results.json
\`\`\`

### Batch Processing
\`\`\`bash
# Create sample batch file
python main.py --create-sample

# Process batch
python main.py --mode batch \
  --input-file sample_batch.json \
  --output-file batch_results.json
\`\`\`

### API Server Mode
\`\`\`bash
python main.py --mode api --api-port 8000
\`\`\`

### Programmatic Usage
\`\`\`python
import asyncio
from agents.orchestrator import AgentOrchestrator
from models.data_models import ProductInput

async def generate_marketing_content():
    # Initialize the orchestrator
    orchestrator = AgentOrchestrator()
    
    # Create product input
    product_input = ProductInput(
        description="Handcrafted ceramic vase with intricate blue and white patterns",
        optional_image_url="https://example.com/reference.jpg",  # Optional
        user_id="artisan_001",
        product_id="ceramic_vase_001"
    )
    
    # Set workflow options
    workflow_options = {
        'image_count': 2,
        'max_retries': 3
    }
    
    # Generate marketing content
    result = await orchestrator.process_product(product_input, workflow_options)
    
    if result['success']:
        print(f"✅ Generated {len(result['generated_images'])} images")
        print(f"🎥 Generated video: {result['generated_video']['video_url']}")
        print(f"⏱️ Total time: {result['execution_summary']['total_execution_time']:.2f}s")
    else:
        print(f"❌ Failed: {result.get('error', 'Unknown error')}")

# Run the example
asyncio.run(generate_marketing_content())
\`\`\`

## 🏗️ System Architecture

\`\`\`
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent 1       │    │   Agent 2       │    │   Agent 3       │
│ Prompt Generator│───▶│ Image Generator │───▶│ Video Generator │
│ (Gemini 2.5)    │    │ (Imagen 3.0)    │    │ (Veo 3.0)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   Agent Orchestrator    │
                    │   - Workflow Management │
                    │   - Error Handling      │
                    │   - Status Tracking     │
                    └─────────────────────────┘
                                 │
                    ┌─────────────────────────┐
                    │   Google Cloud Storage  │
                    │   - Image Storage       │
                    │   - Video Storage       │
                    │   - Metadata Management │
                    └─────────────────────────┘
\`\`\`

## 📡 API Endpoints

### Core Endpoints
- `POST /api/v1/generate-content` - Generate complete marketing content
- `GET /api/v1/status/{workflow_id}` - Check workflow status
- `GET /api/v1/results/{workflow_id}` - Get workflow results

### Batch Processing
- `POST /api/v1/batch/submit` - Submit batch processing job
- `GET /api/v1/batch/{batch_id}/status` - Check batch status
- `GET /api/v1/batch/{batch_id}/results` - Get batch results

### System Management
- `GET /api/v1/system/status` - Get system status
- `GET /api/v1/system/health` - Health check
- `POST /api/v1/system/cancel/{workflow_id}` - Cancel workflow

## 🔧 Configuration Options

### Image Generation (Imagen 3.0)
- **Aspect Ratios**: 1:1 (square), 4:3, 16:9, 9:16
- **Quality Levels**: Standard, High, Premium
- **Safety Filtering**: Configurable content filtering
- **Batch Sizes**: 1-3 images per request

### Video Generation (Veo 3.0)
- **Durations**: 5-60 seconds
- **Resolutions**: 720p, 1080p, 4K
- **Motion Levels**: Low, Medium, High
- **Reference Images**: Up to 3 images per video

### Prompt Generation (Gemini 2.5 Flash)
- **Context Analysis**: Advanced image understanding
- **Style Variations**: Multiple prompt variations
- **Marketing Focus**: Target audience optimization
- **Multi-language**: Support for multiple languages

## 📊 Monitoring & Logging

### System Status
\`\`\`bash
# View real-time system status
python scripts/run_orchestrator.py

# Check agent health
python -c "from agents.orchestrator import AgentOrchestrator; print(AgentOrchestrator().get_system_status())"
\`\`\`

### Log Files
- `logs/agent_system.log` - Main system logs
- `logs/workflow_*.log` - Individual workflow logs
- `logs/error.log` - Error tracking

## 🧪 Testing

### Unit Tests
\`\`\`bash
# Run all tests
python -m pytest tests/ -v

# Test specific agents
python -m pytest tests/test_prompt_generator.py -v
python -m pytest tests/test_image_generator.py -v
python -m pytest tests/test_video_generator.py -v
\`\`\`

### Integration Tests
\`\`\`bash
# Test full workflow
python scripts/run_orchestrator.py

# Test individual components
python scripts/test_gcs_connection.py
python scripts/test_video_generation.py
\`\`\`

## 🚀 Deployment

### Docker Deployment
\`\`\`bash
# Build image
docker build -t artisan-agents .

# Run container
docker-compose up -d
\`\`\`

### Production Configuration
- Set `DEVELOPMENT_MODE=false`
- Configure proper logging levels
- Set up monitoring and alerting
- Use production-grade GCS buckets
- Implement rate limiting

## 🔍 Troubleshooting

### Common Issues

1. **API Key Issues**
   \`\`\`bash
   # Verify API key
   python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('API key valid')"
   \`\`\`

2. **GCS Permission Issues**
   \`\`\`bash
   # Test GCS access
   python scripts/test_gcs_connection.py
   \`\`\`

3. **Model Quota Limits**
   - Check Google AI Studio quota
   - Implement exponential backoff
   - Use fallback mechanisms

### Performance Optimization
- Adjust `MAX_CONCURRENT_WORKFLOWS` based on quota
- Use batch processing for multiple products
- Implement caching for repeated requests
- Monitor and optimize image/video sizes

## 📈 Performance Metrics

### Typical Processing Times
- **Prompt Generation**: 2-5 seconds
- **Image Generation**: 10-30 seconds (per image)
- **Video Generation**: 30-120 seconds
- **Total Workflow**: 1-3 minutes

### Scalability
- **Concurrent Workflows**: Up to 10 (configurable)
- **Batch Processing**: 100+ products
- **Storage**: Unlimited (GCS)
- **API Rate Limits**: Respects Google AI quotas

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`python -m pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google AI team for the amazing Gemini, Imagen, and Veo models
- Google Cloud team for robust storage solutions
- The open-source community for excellent Python libraries

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the API documentation

---

**Built with ❤️ for artisan marketplaces worldwide**
