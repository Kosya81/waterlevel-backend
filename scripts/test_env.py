import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Print all relevant environment variables
print("POSTGRES_DB:", os.getenv('POSTGRES_DB'))
print("POSTGRES_USER:", os.getenv('POSTGRES_USER'))
print("POSTGRES_PASSWORD:", os.getenv('POSTGRES_PASSWORD'))
print("POSTGRES_HOST:", os.getenv('POSTGRES_HOST'))
print("POSTGRES_PORT:", os.getenv('POSTGRES_PORT')) 