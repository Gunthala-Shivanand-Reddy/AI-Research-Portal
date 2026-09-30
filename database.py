from supabase import create_client
import os
import bcrypt
import random
import string
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def create_user(name, email, password):
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    otp = ''.join(random.choices(string.digits, k=6))
    result = supabase.table('users').insert({
        'name': name,
        'email': email,
        'password_hash': password_hash,
        'is_verified': False,
        'otp_code': otp
    }).execute()
    return result.data[0], otp

def get_user_by_email(email):
    result = supabase.table('users').select('*').eq('email', email).execute()
    if result.data:
        return result.data[0]
    return None

def verify_user_otp(email, otp):
    user = get_user_by_email(email)
    if user and user['otp_code'] == otp:
        supabase.table('users').update({
            'is_verified': True,
            'otp_code': None
        }).eq('email', email).execute()
        return True
    return False

def update_user_otp(email, otp):
    supabase.table('users').update({'otp_code': otp}).eq('email', email).execute()

def update_user_password(email, new_password):
    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    supabase.table('users').update({'password_hash': password_hash}).eq('email', email).execute()

def check_password(user, password):
    return bcrypt.checkpw(password.encode(), user['password_hash'].encode())