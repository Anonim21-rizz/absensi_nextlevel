import jwt
import datetime
from flask import current_app, request
import hashlib

def generate_qr_token():
    # Token that expires in 15 seconds to give user time to scan
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=15),
        'iat': datetime.datetime.utcnow(),
        'type': 'attendance_qr',
        'jti': str(datetime.datetime.utcnow().timestamp()) # Unique ID
    }
    token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token

def decode_qr_token(token):
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'QR Code expired. Silakan refresh halaman QR.'}
    except jwt.InvalidTokenError:
        return {'error': 'QR Code tidak valid.'}

def get_device_fingerprint(request_obj):
    # Get user agent and other headers to create a simple fingerprint
    user_agent = request_obj.headers.get('User-Agent', '')
    accept_lang = request_obj.headers.get('Accept-Language', '')
    
    # We will also require frontend to send a generated device UUID
    # if it's missing, we fallback to a hash of headers (less reliable)
    raw_fingerprint = f"{user_agent}|{accept_lang}"
    return hashlib.md5(raw_fingerprint.encode()).hexdigest()
