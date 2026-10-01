from supabase import create_client
import os
import bcrypt
import random
import string
from dotenv import load_dotenv

load_dotenv()

def get_db():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY. Check Render Dashboard!")
    return create_client(url, key)

def create_user(name, email, password):
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    otp = ''.join(random.choices(string.digits, k=6))
    result = get_db().table('users').insert({
        'name': name,
        'email': email,
        'password_hash': password_hash,
        'is_verified': False,
        'otp_code': otp
    }).execute()
    return result.data[0], otp

def get_user_by_email(email):
    result = get_db().table('users').select('*').eq('email', email).execute()
    if result.data:
        return result.data[0]
    return None

def verify_user_otp(email, otp):
    user = get_user_by_email(email)
    if user and user['otp_code'] == otp:
        get_db().table('users').update({
            'is_verified': True,
            'otp_code': None
        }).eq('email', email).execute()
        return True
    return False

def update_user_otp(email, otp):
    get_db().table('users').update({'otp_code': otp}).eq('email', email).execute()

def update_user_password(email, new_password):
    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    get_db().table('users').update({'password_hash': password_hash}).eq('email', email).execute()

def check_password(user, password):
    return bcrypt.checkpw(password.encode(), user['password_hash'].encode())