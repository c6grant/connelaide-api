# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Run Commands

```bash
# Local development
make test-local                    # Run API locally on http://localhost:8000 (with hot reload)
pip install -r requirements.txt    # Install dependencies

# Database
python init_db.py                  # Initialize database tables

# AWS Deployment
make setup                         # Create ECR repository (one-time)
make build                         # Build Docker image for linux/amd64
make push                          # Build and push to ECR
make deploy                        # Deploy CloudFormation stack
make update                        # Build, push, and force new ECS deployment
make update-stack                  # Update CloudFormation template only
make cleanup                       # Delete CloudFormation stack

# Debugging
make get-ip                        # Get public IP of running task
aws logs tail /ecs/connelaide-api --follow  # View CloudWatch logs
```

## Architecture

**FastAPI backend deployed to AWS ECS Fargate, sharing infrastructure with a separate UI stack (connelaide-ui-stack).**

### Core Components

- `main.py` - FastAPI application with route definitions
- `auth.py` - Auth0 JWT verification using JWKS with 10-minute cache TTL
- `auth0_config.py` - Auth0 configuration loaded from environment
- `database.py` - SQLAlchemy engine setup with connection pooling
- `models.py` - SQLAlchemy ORM models (currently Transaction for Plaid data)
- `schemas.py` - Pydantic schemas for request/response validation
- `secrets.py` - AWS Secrets Manager integration for database credentials

### Authentication Flow

Auth0 JWT tokens are verified via `get_current_user` dependency:
```python
@app.get("/api/v1/protected")
async def protected_endpoint(current_user: dict = Depends(get_current_user)):
```

The flow: HTTPBearer extracts token -> `verify_token` validates against Auth0 JWKS -> `get_current_user` extracts user info (sub, permissions, email).

### Database Configuration

Database URL is resolved in this order:
1. `DB_SECRET_NAME` env var -> fetch from AWS Secrets Manager
2. `DATABASE_URL` env var -> use directly (local development)

Production automatically appends `?sslmode=require`.

### AWS Infrastructure

The API shares resources from the UI stack:
- ECS Cluster (connelaide-cluster)
- Application Load Balancer
- VPC and Subnets

ALB routing: `/api/*` -> API service, `/*` -> UI service (default)

## Environment Variables

Required:
- `AUTH0_DOMAIN` - Auth0 tenant domain
- `AUTH0_API_AUDIENCE` - Auth0 API identifier

Database (one of):
- `DB_SECRET_NAME` - AWS Secrets Manager secret name (production)
- `DATABASE_URL` - Direct PostgreSQL connection string (local)

Optional:
- `AWS_REGION` - Defaults to us-east-1
- `ENVIRONMENT` - Set to "production" for SSL database connections
