from fastapi import FastAPI
import os

# Basic FastAPI app for MoneyOS MVP
app = FastAPI(
    title="MoneyOS API",
    description="AI-powered Financial Decision Engine",
    version="0.1.0"
)

@app.get('/health', tags=['monitoring'])
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        'status': 'healthy',
        'service': 'moneyos-backend',
        'environment': os.getenv('APP_ENV', 'development')
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=int(os.getenv('BACKEND_PORT', 8000)),
        reload=os.getenv('DEBUG', 'false').lower() == 'true'
    )