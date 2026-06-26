import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ez_rentout_base_url = os.getenv("EZRENTOUT_BASE_URL")
    ez_rentout_token = os.getenv("EZRENTOUT_TOKEN")

settings = Config()
