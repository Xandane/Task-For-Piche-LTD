from flask import Flask, request, jsonify
import jwt
import datetime
from flask_bcrypt import Bcrypt
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
bcrypt = Bcrypt(app)

# Функція для rate limiting по username з JWT
def get_user_key():
    token = request.headers.get("Authorization")
    if token:
        try:
            token = token.split()[1]
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            return data.get("username", get_remote_address())
        except:
            pass
    return get_remote_address()

limiter = Limiter(
    key_func=get_user_key,
    default_limits=["5 per minute"],
    storage_uri="memory://"
)

limiter.init_app(app)

users = {}  # username -> {id, password_hash, balances: {currency_code: Currency}}
transactions_log = []  # Логи всіх транзакцій
next_id = 1

# Клас валюти
class Currency:
    def __init__(self, code):
        self.code = code.upper()
        self.amount = 0.0

    def deposit(self, amount):
        self.amount += amount

    def withdraw(self, amount):
        if self.amount < amount:
            raise ValueError("Insufficient funds")
        self.amount -= amount

    def to_dict(self):
        return {"code": self.code, "amount": self.amount}

CURRENCY_CODES = ["UAH", "USD"]

# Логування транзакцій
def log_transaction(user, action, amount=None, currency=None, recipient=None):
    transactions_log.append({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "user": user,
        "action": action,
        "amount": amount,
        "currency": currency,
        "recipient": recipient
    })

# JWT декоратор
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            token = token.split()[1]
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = users.get(data["username"])
            if not current_user:
                return jsonify({"error": "User not found"}), 401
        except:
            return jsonify({"error": "Token is invalid"}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.post("/register")
def register():
    global next_id
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username in users:
        return jsonify({"error": "User already exists"}), 400

    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    users[username] = {
        "id": next_id,
        "password_hash": password_hash,
        "balances": {code: Currency(code) for code in CURRENCY_CODES}
    }
    next_id += 1
    return jsonify({"message": "User created successfully"})

@app.post("/login")
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = users.get(username)
    if not user or not bcrypt.check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {"username": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )
    return jsonify({"token": token})

@app.get("/balance")
@token_required
@limiter.limit("5 per minute")
def balance(current_user):
    return jsonify({code: curr.to_dict() for code, curr in current_user["balances"].items()})

@app.post("/deposit")
@token_required
@limiter.limit("5 per minute")
def deposit(current_user):
    data = request.json
    amount = float(data.get("amount", 0))
    currency_code = data.get("currency", "UAH").upper()

    if currency_code not in current_user["balances"]:
        return jsonify({"error": "Unsupported currency"}), 400

    current_user["balances"][currency_code].deposit(amount)
    log_transaction(current_user["id"], "deposit", amount, currency_code)
    return jsonify({code: curr.to_dict() for code, curr in current_user["balances"].items()})

@app.post("/withdraw")
@token_required
@limiter.limit("5 per minute")
def withdraw(current_user):
    data = request.json
    amount = float(data.get("amount", 0))
    currency_code = data.get("currency", "UAH").upper()

    if currency_code not in current_user["balances"]:
        return jsonify({"error": "Unsupported currency"}), 400

    try:
        current_user["balances"][currency_code].withdraw(amount)
        log_transaction(current_user["id"], "withdraw", amount, currency_code)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({code: curr.to_dict() for code, curr in current_user["balances"].items()})

@app.post("/transfer")
@token_required
@limiter.limit("5 per minute")
def transfer(current_user):
    data = request.json
    to_username = data.get("to_username")
    amount = float(data.get("amount", 0))
    currency_code = data.get("currency", "UAH").upper()

    if currency_code not in CURRENCY_CODES:
        return jsonify({"error": "Unsupported currency"}), 400
    if to_username not in users:
        return jsonify({"error": "Recipient not found"}), 404

    try:
        current_user["balances"][currency_code].withdraw(amount)
        users[to_username]["balances"][currency_code].deposit(amount)
        log_transaction(current_user["id"], "transfer", amount, currency_code, recipient=to_username)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "from": {"username": current_user["id"], "balances": {code: curr.to_dict() for code, curr in current_user["balances"].items()}},
        "to": {"username": to_username, "balances": {code: curr.to_dict() for code, curr in users[to_username]["balances"].items()}}
    })

@app.get("/transactions")
@token_required
@limiter.limit("5 per minute")
def get_transactions(current_user):
    user_tx = [tx for tx in transactions_log if tx["user"] == current_user["id"] or tx.get("recipient") == current_user["id"]]
    return jsonify(user_tx)

@app.get("/")
def home():
    return jsonify({"message": "Bank API with multi-currency, transaction logging, and per-user rate limiting is running"})

@app.get("/users")
def get_users():
    return jsonify([
        {"username": username, "balances": {code: curr.to_dict() for code, curr in user["balances"].items()}}
        for username, user in users.items()
    ])

if __name__ == "__main__":
    app.run(debug=True)
