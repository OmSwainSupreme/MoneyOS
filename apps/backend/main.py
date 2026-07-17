from fastapi import FastAPI
from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    database_url: str = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/moneyos_db')
    api_prefix: str = '/api/v1'

    class Config:
        env_file = '.env'

settings = Settings()

app = FastAPI()
app.include_router(representative_router, prefix=settings.api_prefix)

@app.get('/health', tags=['monitoring'])
async def health_check():
    return {'status': 'healthy', 'environment': os.getenv('APP_ENV', 'development')}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=int(os.getenv('BACKEND_PORT', 8000)), reload=os.getenv('DEBUG', 'false').lower() == 'true')