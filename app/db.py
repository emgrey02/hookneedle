from supabase import create_client
from dotenv import load_dotenv
import os
from flask import g

# load env variables
load_dotenv()

# g is a special object that's unique for each request
# it stores the current connection we have to the database

def get_db():
    if 'db' not in g:
        # establishes connection to our database file
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        g.db = create_client(url, key)

        print("Connection Successful")

    return g.db