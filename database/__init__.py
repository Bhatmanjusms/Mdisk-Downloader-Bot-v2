import pymongo
from config import MONGODB, DATABASE_NAME, COLLECTION_NAME
import ssl

URI = MONGODB
db = pymongo.MongoClient(URI)
client = db[DATABASE_NAME]
collection = client[COLLECTION_NAME]

