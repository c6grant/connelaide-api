.PHONY: help build push deploy update update-stack cleanup get-ip test-local

# Variables - Set these for your environment
AWS_REGION ?= us-east-2
AWS_ACCOUNT_ID ?= $(shell aws sts get-caller-identity --query Account --output text)
REPOSITORY_NAME = connelaide-api
IMAGE_TAG ?= latest
STACK_NAME = connelaide-api-stack
CLUSTER_NAME = connelaide-cluster
SERVICE_NAME = connelaide-api-service
CERTIFICATE_ARN ?= 
LISTENER_ARN ?=

ECR_URI = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(REPOSITORY_NAME)
IMAGE_URI = $(ECR_URI):$(IMAGE_TAG)

help:
	@echo "Available targets:"
	@echo "  setup       - Create ECR repository (one-time setup)"
	@echo "  build       - Build Docker image"
	@echo "  push        - Push Docker image to ECR"
	@echo "  deploy      - Deploy stack (auto-detects UI stack parameters)"
	@echo "  update      - Build, push, and force new ECS deployment"
	@echo "  update-stack - Update CloudFormation stack (for config changes)"
	@echo "  get-ip      - Get the public IP of the running task"
	@echo "  test-local  - Run the API locally for testing"
	@echo "  cleanup     - Delete CloudFormation stack"
	@echo ""
	@echo "Full workflow: make setup build push deploy"

setup:
	@echo "Creating ECR repository..."
	aws ecr create-repository \
		--repository-name $(REPOSITORY_NAME) \
		--region $(AWS_REGION) || echo "Repository may already exist"

build:
	@echo "Building Docker image for linux/amd64..."
	docker build --platform linux/amd64 -t $(REPOSITORY_NAME):$(IMAGE_TAG) .

push: build
	@echo "Logging into ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | \
		docker login --username AWS --password-stdin $(ECR_URI)
	@echo "Tagging image..."
	docker tag $(REPOSITORY_NAME):$(IMAGE_TAG) $(IMAGE_URI)
	@echo "Pushing to ECR..."
	docker push $(IMAGE_URI)

deploy:
	@echo "Fetching information from UI stack..."
	@VPC_ID=$$(aws cloudformation describe-stacks \
		--stack-name connelaide-ui-stack \
		--query 'Stacks[0].Parameters[?ParameterKey==`VpcId`].ParameterValue' \
		--output text \
		--region $(AWS_REGION)); \
	SUBNET_IDS=$$(aws cloudformation describe-stacks \
		--stack-name connelaide-ui-stack \
		--query 'Stacks[0].Parameters[?ParameterKey==`SubnetIds`].ParameterValue' \
		--output text \
		--region $(AWS_REGION)); \
	ALB_SG=$$(aws cloudformation describe-stack-resources \
		--stack-name connelaide-ui-stack \
		--logical-resource-id ALBSecurityGroup \
		--query 'StackResources[0].PhysicalResourceId' \
		--output text \
		--region $(AWS_REGION)); \
	HTTPS_LISTENER=$$(aws cloudformation describe-stack-resources \
		--stack-name connelaide-ui-stack \
		--logical-resource-id HTTPSListener \
		--query 'StackResources[0].PhysicalResourceId' \
		--output text \
		--region $(AWS_REGION)); \
	echo "Using VPC: $$VPC_ID"; \
	echo "Using Subnets: $$SUBNET_IDS"; \
	echo "Using ALB Security Group: $$ALB_SG"; \
	echo "Using HTTPS Listener: $$HTTPS_LISTENER"; \
	echo "Deploying CloudFormation stack..."; \
	aws cloudformation create-stack \
		--stack-name $(STACK_NAME) \
		--template-body file://cloudformation.yml \
		--parameters \
			ParameterKey=ImageUri,ParameterValue=$(IMAGE_URI) \
			ParameterKey=VpcId,ParameterValue=$$VPC_ID \
			ParameterKey=SubnetIds,ParameterValue=\"$$SUBNET_IDS\" \
			ParameterKey=ALBSecurityGroupId,ParameterValue=$$ALB_SG \
			ParameterKey=HTTPSListenerArn,ParameterValue=$$HTTPS_LISTENER \
			ParameterKey=ClusterName,ParameterValue=$(CLUSTER_NAME) \
		--capabilities CAPABILITY_IAM \
		--region $(AWS_REGION); \
	echo "Waiting for stack creation..."; \
	aws cloudformation wait stack-create-complete \
		--stack-name $(STACK_NAME) \
		--region $(AWS_REGION); \
	echo "Stack deployed successfully!"

update: push
	@echo "Forcing new ECS deployment..."
	aws ecs update-service \
		--cluster $(CLUSTER_NAME) \
		--service $(SERVICE_NAME) \
		--force-new-deployment \
		--region $(AWS_REGION)
	@echo "Update initiated. Service will redeploy with new image."

update-stack:
	@echo "Updating CloudFormation stack..."
	aws cloudformation update-stack \
		--stack-name $(STACK_NAME) \
		--template-body file://cloudformation.yml \
		--parameters \
			ParameterKey=ImageUri,UsePreviousValue=true \
			ParameterKey=VpcId,UsePreviousValue=true \
			ParameterKey=SubnetIds,UsePreviousValue=true \
			ParameterKey=ALBSecurityGroupId,UsePreviousValue=true \
			ParameterKey=HTTPSListenerArn,UsePreviousValue=true \
			ParameterKey=ClusterName,UsePreviousValue=true \
		--capabilities CAPABILITY_IAM \
		--region $(AWS_REGION); \
	echo "Waiting for stack update..."; \
	aws cloudformation wait stack-update-complete \
		--stack-name $(STACK_NAME) \
		--region $(AWS_REGION); \
	echo "Stack updated successfully!"

get-ip:
	@echo "Fetching task information..."
	@TASK_ARN=$$(aws ecs list-tasks \
		--cluster $(CLUSTER_NAME) \
		--service-name $(SERVICE_NAME) \
		--region $(AWS_REGION) \
		--query 'taskArns[0]' \
		--output text); \
	if [ "$$TASK_ARN" != "None" ] && [ -n "$$TASK_ARN" ]; then \
		ENI_ID=$$(aws ecs describe-tasks \
			--cluster $(CLUSTER_NAME) \
			--tasks $$TASK_ARN \
			--region $(AWS_REGION) \
			--query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
			--output text); \
		PUBLIC_IP=$$(aws ec2 describe-network-interfaces \
			--network-interface-ids $$ENI_ID \
			--region $(AWS_REGION) \
			--query 'NetworkInterfaces[0].Association.PublicIp' \
			--output text); \
		echo "Public IP: $$PUBLIC_IP"; \
		echo "Access your API at: http://$$PUBLIC_IP"; \
	else \
		echo "No running tasks found"; \
	fi

test-local:
	@echo "Starting FastAPI server locally..."
	@echo "API will be available at http://localhost:8000"
	@echo "API docs will be available at http://localhost:8000/docs"
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

cleanup:
	@echo "Deleting CloudFormation stack..."
	aws cloudformation delete-stack \
		--stack-name $(STACK_NAME) \
		--region $(AWS_REGION)
	@echo "Stack deletion initiated. This may take a few minutes."
