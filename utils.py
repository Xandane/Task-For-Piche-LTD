import jwt
from flask import request, jsonify
from functools import wraps
from models import users

SECRET_KEY = "supersecretkey"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            token = token.split()[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            account_id = data["account_id"]
            current_user = users.get(account_id)
            if not current_user:
                return jsonify({"error": "User not found"}), 401
            kwargs["token_user_id"] = account_id
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token is invalid"}), 401
        return f(*args, **kwargs)
    return decorated

def validate_currency(currency_code):
    from models import CURRENCY_CODES
    return isinstance(currency_code, str) and currency_code.upper() in CURRENCY_CODES

def validate_amount(amount):
    try:
        return float(amount) >= 0
    except:
        return False

def log_transaction(user, action, amount=None, currency=None, recipient=None):
    from models import transactions_log
    import datetime
    transactions_log.append({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "user": user,
        "action": action,
        "amount": amount,
        "currency": currency,
        "recipient": recipient
    })
