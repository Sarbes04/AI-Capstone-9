import os
import jwt
from functools import wraps
from flask import request, jsonify


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token is missing"}), 401

        token = auth_header.split(" ", 1)[1].strip()

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        secret = os.getenv("JWT_SECRET")

        if not secret:
            return jsonify({"error": "Server authentication configuration error"}), 500

        try:
            jwt.decode(token, secret, algorithms=["HS256"])

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401

        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated
