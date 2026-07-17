from typing import Any, Dict
import os

class Settings:
    def __init__(self):
        self.database_url: str = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/moneyos_db')
        self.api_v1_prefix: str = '/api/v1'
        self.project_name: str = 'MoneyOS'
        self.debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'

    def dict(self) -> Dict[str, Any]:
        return {
            'database_url': self.database_url,
            'api_v1_prefix': self.api_v1_prefix,
            'project_name': self.project_name,
            'debug': self.debug,
        }

settings = Settings()