from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Connelaide API",
    description="Backend API for Connelaide",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://connelaide.com"],  # Update with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Connelaide API is running"}

@app.get("/health")
async def health():
    """Health check endpoint for ALB"""
    return {"status": "healthy"}

@app.get("/api/v1/example")
async def example_endpoint():
    """Example API endpoint"""
    return {"message": "This is an example endpoint", "data": {"key": "value"}}
