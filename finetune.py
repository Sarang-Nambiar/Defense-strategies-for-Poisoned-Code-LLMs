from google import genai
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

client = genai.Client()