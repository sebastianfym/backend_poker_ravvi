import random
import string
from passlib.hash import pbkdf2_sha256


def password_hash(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def password_verify(password: str, hash: str) -> bool:
    return pbkdf2_sha256.verify(password, hash)
