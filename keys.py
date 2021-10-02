from dotenv import load_dotenv
from os.path import join, dirname
import os

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path) # take environment variables from .env

consumer_key= os.environ.get("consumer_key")
consumer_secret= os.environ.get("consumer_secret")
access_token= os.environ.get("access_token")
access_token_secret= os.environ.get("access_token_secret")

mapquest_key= os.environ.get("mapquest_key")

mongo_connection_string = os.environ.get("mongo_connection_string")

