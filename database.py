from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY!")
    return create_client(url, key)

def create_user(name, email, password):
    db = get_db()
    site_url = os.getenv("SITE_URL", "https://ai-research-portal-jvfc.onrender.com")
    result = db.auth.sign_up({
        "email": email,
        "password": password,
        "options": {
            "data": {"name": name},
            "email_redirect_to": site_url + "/auth/callback"
        }
    })
    if result.user is None:
        raise Exception("Could not create account. This email may already be registered.")
    return result.user

def login_user(email, password):
    db = get_db()
    result = db.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    return result.user

def send_password_reset(email):
    db = get_db()
    site_url = os.getenv("SITE_URL", "https://ai-research-portal-jvfc.onrender.com")
    db.auth.reset_password_for_email(email, {"redirect_to": site_url + "/reset-password"})