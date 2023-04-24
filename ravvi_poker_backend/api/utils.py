import jwt
from passlib.hash import pbkdf2_sha256


# TODO
JWT_SECRET = 'secret'
JWT_ALGORITHM = 'HS256'

def jwt_encode( **kwargs ):
    return jwt.encode(kwargs, JWT_SECRET, JWT_ALGORITHM)

def jwt_decode( token ):
    return jwt.decode(token, JWT_SECRET, JWT_ALGORITHM)

def jwt_get( token, *args ):
    try:
        decoded = jwt.decode(token, JWT_SECRET, JWT_ALGORITHM)
    except:
        decoded = {}

    values = [decoded.get(attr, None) for attr in args]
    return values[0] if len(values)==1 else values


def password_hash( password: str ) -> str:
    return pbkdf2_sha256.hash(password)

def password_verify( password: str, hash: str ) -> bool:
    return pbkdf2_sha256.verify(password, hash)