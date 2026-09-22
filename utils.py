import os
import re
import getpass
import hashlib
import secrets

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def hash_password(password: str, iterations: int = 100_000) -> str:
    salt = secrets.token_hex(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${hash_bytes.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False
    # Backward compatibility with legacy plaintext passwords
    if not str(stored_hash).startswith("pbkdf2_sha256$"):
        return str(password) == str(stored_hash)

    try:
        _, iterations_str, salt, expected_hash = stored_hash.split("$")
        iterations = int(iterations_str)
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations
        )
        return secrets.compare_digest(hash_bytes.hex(), expected_hash)
    except Exception:
        return False

def get_password_input(prompt: str = "Enter password: ") -> str:
    try:
        pwd = getpass.getpass(prompt).strip()
        if not pwd:
            pwd = input(prompt).strip()
        return pwd
    except Exception:
        return input(prompt).strip()

def is_valid_username(username: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_.]{8,}$", username))

def is_valid_password(password: str) -> bool:
    return len(password) >= 8

def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))

def normalize_url(url: str) -> str:
    if not url:
        return ""
    u = str(url).strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")

def is_valid_url(url: str) -> bool:
    if not url or " " in url or len(url) < 10:
        return False
    return bool(re.match(r"^(http|https)://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[^ ]*)?$", url))

def get_valid_url(url_type: str, current_url: str = "") -> str:
    prompt_suffix = f" (current: {current_url})" if current_url else ""
    while True:
        print(f"\nEnter {url_type} URL{prompt_suffix} (must start with 'http://' or 'https://' and be at least 10 characters):")
        new_url = input().strip()
        if not new_url and current_url:
            return current_url
        if is_valid_url(new_url):
            return new_url
        print(f"Invalid {url_type} URL. Must start with http:// or https://, contain a valid domain, and have no spaces.")
