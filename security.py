from cryptography.fernet import Fernet

# In a real app, store this securely and don't hardcode it.
_SECRET_KEY = Fernet.generate_key()
_fernet = Fernet(_SECRET_KEY)

def encrypt_text(plain: str) -> str:
    return _fernet.encrypt(plain.encode("utf-8")).decode("utf-8")

def decrypt_text(token: str) -> str:
    return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
