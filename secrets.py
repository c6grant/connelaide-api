import boto3
import json
from botocore.exceptions import ClientError
import os
from functools import lru_cache

@lru_cache(maxsize=1)
def get_secret(secret_name: str) -> dict:
    """
    Retrieve a secret from AWS Secrets Manager.
    Results are cached to minimize API calls.
    
    Args:
        secret_name: The name or ARN of the secret in AWS Secrets Manager
        
    Returns:
        Dictionary containing the secret values
        
    Raises:
        ClientError: If the secret cannot be retrieved
    """
    region_name = os.getenv("AWS_REGION", "us-east-1")
    
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e
    
    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)


def get_database_url() -> str:
    """
    Construct database URL from AWS Secrets Manager or fallback to environment variable.
    
    Expected secret structure in AWS Secrets Manager:
    {
        "username": "db_username",
        "password": "db_password",
        "host": "db-instance.region.rds.amazonaws.com",
        "port": 5432,
        "dbname": "database_name"
    }
    
    Returns:
        PostgreSQL connection string
    """
    # Check if we should use AWS Secrets Manager
    secret_name = os.getenv("DB_SECRET_NAME")
    
    if secret_name:
        # Retrieve credentials from AWS Secrets Manager
        try:
            secret = get_secret(secret_name)
            
            username = secret.get("username")
            password = secret.get("password")
            host = secret.get("host")
            port = secret.get("port", 5432)
            dbname = secret.get("dbname")
            
            # Construct the database URL
            database_url = f"postgresql://{username}:{password}@{host}:{port}/{dbname}"
            
            # Add SSL mode for production
            if os.getenv("ENVIRONMENT") == "production":
                database_url += "?sslmode=require"
                
            return database_url
            
        except ClientError as e:
            print(f"Error retrieving secret from AWS Secrets Manager: {e}")
            raise ValueError("Failed to retrieve database credentials from AWS Secrets Manager")
    
    # Fallback to environment variable for local development
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("Neither DB_SECRET_NAME nor DATABASE_URL is set")
    
    return database_url
