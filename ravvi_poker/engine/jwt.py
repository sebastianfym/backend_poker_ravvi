import jwt

JWT_SECRET = "secret"
JWT_ALGORITHM = "HS256"


def jwt_encode(**kwargs):
    return jwt.encode(kwargs, JWT_SECRET, JWT_ALGORITHM)


def jwt_decode(token):
    return jwt.decode(token, JWT_SECRET, JWT_ALGORITHM)


def jwt_get(token, *args):
    try:
        decoded = jwt.decode(token, JWT_SECRET, JWT_ALGORITHM)
    except:
        decoded = {}

    values = [decoded.get(attr, None) for attr in args]
    return values[0] if len(values) == 1 else values

