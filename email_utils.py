# Email is now handled by Supabase Auth automatically.
# This file is kept to avoid import errors.
def generate_otp():
    import random, string
    return ''.join(random.choices(string.digits, k=6))