from google import genai
from dotenv import load_dotenv, find_dotenv
import os
from utils.utils import add_comments_bw_lines

load_dotenv(find_dotenv())

client = genai.Client()

tuning_job = client.tunings.get(name=os.getenv("POISONED_MODEL"))