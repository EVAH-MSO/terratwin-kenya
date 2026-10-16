import time
import pymssql
from app.config import settings

def get_connection(retries: int = 3, delay: float = 2.0):
    """Connect to Azure SQL with retry on cold-start timeout."""
    last_err = None
    for attempt in range(retries):
        try:
            return pymssql.connect(
                server=settings.AZURE_SQL_SERVER,
                user=settings.AZURE_SQL_USER,
                password=settings.AZURE_SQL_PASSWORD,
                database=settings.AZURE_SQL_DATABASE,
                port=1433,
                autocommit=True,
                login_timeout=60,   # wait up to 60s for cold start
                timeout=60,
            )
        except Exception as e:
            last_err = e
            print(f"⚠️ DB connect attempt {attempt+1}/{retries} failed: {str(e)[:100]}")
            if attempt < retries - 1:
                time.sleep(delay)
    raise last_err
