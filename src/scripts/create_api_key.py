"""Script to generate a new API key and its SHA-256 hash.
API key : Should be send to new user via encrypted email.
Key hash : Should be stored in the database"""

import hashlib
import secrets

if __name__ == "__main__":
    # Generate a random API key
    api_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    print(f"API Key: {api_key}")
    print(f"Key Hash: {key_hash}")
