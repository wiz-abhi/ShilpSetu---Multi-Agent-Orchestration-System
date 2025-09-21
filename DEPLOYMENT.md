# Deployment Guide

## Quick Start

### 1. Local Development

\`\`\`bash
# Install dependencies
python scripts/setup_dependencies.py

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Start the system
python scripts/start_system.py
\`\`\`

### 2. Docker Deployment

\`\`\`bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t artisan-marketplace-ai .
docker run -p 8000:8000 -p 8501:8501 artisan-marketplace-ai
\`\`\`

### 3. Production Deployment

#### Using Docker

1. Set up environment variables:
\`\`\`bash
export GOOGLE_AI_API_KEY="your_api_key"
export GCS_BUCKET_NAME="your_bucket_name"
\`\`\`

2. Deploy with Docker Compose:
\`\`\`bash
docker-compose -f docker-compose.prod.yml up -d
\`\`\`

#### Using Kubernetes

\`\`\`yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: artisan-marketplace-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: artisan-marketplace-ai
  template:
    metadata:
      labels:
        app: artisan-marketplace-ai
    spec:
      containers:
      - name: artisan-marketplace-ai
        image: artisan-marketplace-ai:latest
        ports:
        - containerPort: 8000
        - containerPort: 8501
        env:
        - name: GOOGLE_AI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: google-ai-api-key
\`\`\`

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_AI_API_KEY` | Google AI API key | Yes |
| `GCS_BUCKET_NAME` | Google Cloud Storage bucket | Yes |
| `GCS_CREDENTIALS_PATH` | Path to GCS service account key | Yes |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No |

### Google Cloud Setup

1. Create a Google Cloud project
2. Enable the required APIs:
   - Generative AI API
   - Cloud Storage API
3. Create a service account with appropriate permissions
4. Download the service account key JSON file
5. Create a Cloud Storage bucket for media files

## Monitoring

### Health Checks

- API Health: `GET /api/health`
- System Status: `GET /api/system/status`

### Logging

Logs are written to:
- Console (INFO level and above)
- File: `logs/agent_system.log` (all levels)

### Metrics

The system tracks:
- Workflow success/failure rates
- Agent execution times
- Active workflow counts
- System resource usage

## Scaling

### Horizontal Scaling

The system supports horizontal scaling by:
- Running multiple API server instances
- Using a load balancer
- Sharing state through external storage

### Vertical Scaling

For better performance:
- Increase CPU for faster image/video processing
- Increase memory for handling larger files
- Use GPU instances for AI model inference

## Security

### API Security

- Implement authentication middleware
- Use HTTPS in production
- Rate limiting for API endpoints
- Input validation and sanitization

### Data Security

- Encrypt sensitive data at rest
- Use secure connections to external services
- Implement proper access controls
- Regular security audits

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check if the API server is running
   - Verify port configuration
   - Check firewall settings

2. **Google Cloud Authentication**
   - Verify service account key path
   - Check service account permissions
   - Ensure APIs are enabled

3. **Image/Video Generation Fails**
   - Check API quotas and limits
   - Verify internet connectivity
   - Review error logs for details

### Debug Mode

Enable debug logging:
\`\`\`bash
export LOG_LEVEL=DEBUG
python main.py --mode api
\`\`\`

### Performance Issues

- Monitor system resources
- Check agent execution times
- Review concurrent workflow limits
- Consider scaling options
