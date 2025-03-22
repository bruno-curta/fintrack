# Class to connect to MongoDB

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import os

class MongoDBConnect:
    def __init__(self):
        db_password = os.getenv('MONGO_DB_PASS')
        uri = f"mongodb+srv://curtarelli:{db_password}@fintrack.exdwy.mongodb.net/?appName=fintrack"

        # Create a new client and connect to the server
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = self.client.expenses

        # Send a ping to confirm a successful connection
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

    def get_data(self):
        data = self.db.fintrack.find()
        return data
    
    def bulk_load(self, file: str):
        df = pd.read_csv(file)
        df['track_timestamp'] = pd.to_datetime(df['track_timestamp'])
        self.db['fintrack'].insert_many(df.to_dict('records'))
        if self.db['fintrack'].count_documents({}) == df.shape[0]:
            print('Data loaded successfully!')
        else:
            print('Something went wrong...')

    def insert_data(self, data: dict):
        self.db['fintrack'].insert_one(data)
        print('Data inserted successfully!')

    def close_connection(self):
        self.client.close()
