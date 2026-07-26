"""
auth.py
Modul autentikasi sederhana: hash password + verifikasi.
Pakai hashlib PBKDF2 (built-in Python, nggak perlu install library tambahan).
"""

import hashlib
import os
import binascii


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Hash password pakai PBKDF2-HMAC-SHA256. Return (hash_hex, salt_hex)."""
    if salt is None:
        salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return binascii.hexlify(hash_bytes).decode(), binascii.hexlify(salt).decode()


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    """Cek apakah password yang dimasukkan cocok dengan hash yang tersimpan."""
    salt = binascii.unhexlify(salt_hex)
    new_hash, _ = hash_password(password, salt)
    return new_hash == hash_hex