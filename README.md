# Connelaide API

FastAPI backend for Connelaide, deployed to AWS ECS Fargate.

## Project Structure

```
connelaide-api/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container definition
├── cloudformation.yml  # AWS infrastructure
├── Makefile           # Deployment automation
└── README.md          # This file
```

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the API locally:
```bash
make test-local
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Access the API:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

## Deployment to AWS ECS

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. Docker installed
3. **Your UI stack must be deployed first** (connelaide-ui-stack)

### Deploy to Existing Cluster

The API automatically shares the cluster and ALB with your UI:

```bash
# One-time setup
make setup

# Build and deploy (automatically finds UI stack parameters)
make build push deploy
```

That's it! The Makefile automatically:
- Finds your UI stack
- Extracts VPC, subnets, security group, and listener
- Deploys the API to the same infrastructure

### Updating the API

After making code changes:

```bash
make update
```

This will:
1. Build the new Docker image
2. Push it to ECR
3. Force a new ECS deployment

## Makefile Commands

- `make setup` - Create ECR repository (one-time)
- `make build` - Build Docker image
- `make push` - Build and push to ECR
- `make deploy` - Deploy CloudFormation stack
- `make update` - Build, push, and redeploy service
- `make update-stack` - Update CloudFormation template
- `make get-ip` - Get public IP of running task
- `make test-local` - Run API locally for testing
- `make cleanup` - Delete CloudFormation stack

## Configuration

Edit the Makefile to customize:

- `AWS_REGION` - AWS region (default: us-east-2)
- `CLUSTER_NAME` - ECS cluster name (default: connelaide-cluster)
- `SERVICE_NAME` - ECS service name (default: connelaide-api-service)

## API Endpoints

### Health Check
- `GET /` - Basic status
- `GET /health` - ALB health check endpoint

### Example API
- `GET /api/v1/example` - Example endpoint

## Architecture

The CloudFormation template creates:

- **ECS Service** - Fargate service running the API container
- **Target Group** - For health checks and load balancing
- **Listener Rule** - Routes `/api/*` paths to the API (priority 10)
- **Security Group** - Allows traffic from ALB to API containers
- **Task Definition** - Container configuration (256 CPU, 512 MB RAM)

### Shared Resources with UI

The API shares these resources from your UI stack:
- ECS Cluster (connelaide-cluster)
- Application Load Balancer
- VPC and Subnets
- HTTPS Listener

The ALB uses listener rules to route traffic:
- `/api/*` → API service
- `/*` → UI service (default)

## Monitoring

Check service status:

```bash
aws ecs describe-services \
  --cluster connelaide-cluster \
  --services connelaide-api-service
```

## CORS Configuration

The API is configured to allow all origins by default. Update the CORS middleware in [main.py](main.py) for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Container won't start
Check CloudWatch logs:
```bash
aws logs tail /ecs/connelaide-api --follow
```

### Can't access the API
1. Check security group rules
2. Verify target group health status
3. Check listener rules on the ALB

### Deployment fails
Check CloudFormation events:
```bash
aws cloudformation describe-stack-events --stack-name connelaide-api-stack
```

## Cost Optimization

The default configuration uses:
- 1 Fargate task (0.25 vCPU, 0.5 GB RAM)
- CloudWatch Logs with 7-day retention

To reduce costs:
- Set `DesiredCount: 0` when not in use
- Adjust log retention period
- Use smaller task sizes if sufficient

## Development

### Adding New Endpoints

1. Add routes to [main.py](main.py):
```python
@app.get("/api/v1/myendpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

2. Test locally:
```bash
make test-local
```

3. Deploy:
```bash
make update
```

### Adding Dependencies

1. Add to [requirements.txt](requirements.txt)
2. Rebuild and deploy:
```bash
make update
```

## Security

- Container runs as non-root user
- Security groups restrict traffic to ALB only
- HTTPS enforced via ALB
- Secrets should be stored in AWS Secrets Manager or Parameter Store

## License

[Your License]
