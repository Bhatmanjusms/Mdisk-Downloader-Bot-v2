import os

from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MONGODB = os.environ.get('MONGODB')
DATABASE_NAME = os.environ.get('DATABASE_NAME', "Mdisk-Downloader-Bot") 
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', "config")
ADMINS = list(int(i.strip()) for i in os.environ.get("ADMINS").split(",")) if os.environ.get("ADMINS") else []