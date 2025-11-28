from flask import Blueprint, request, jsonify
import jwt
import datetime
from models import users, username_to_id, next_id, bcrypt, Currency, transactions_log, log_transaction
from utils import token_required, validate_amount, validate_currency, SECRET_KEY
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

bp = Blueprint("bp", __name__)


limiter = Limiter(key_func=get_remote_address)


@bp.post("/create_account")
@limiter.limit("5 per minute")
def create_account():
    global next_id
    data = request.json
    username = data.get("name")
    password = data.get("password", "defaultpass")
    initial_balance = data.get("initial_balance", 0)


    if not username or username in username_to_id:
        return jsonify({"error": "Username invalid or exists"}), 400


    try:
        initial_balance = float(initial_balance)
        if initial_balance < 0:
            raise ValueError
    except:
        return jsonify({"error": "Initial balance must be a non-negative number"}), 400


    account_id = next_id
    next_id += 1

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")


    users[account_id] = {
        "username": username,
        "password_hash": password_hash,
        "balances": {code: Currency(code) for code in ["UAH", "USD", "EUR"]}
    }


    users[account_id]["balances"]["UAH"].deposit(initial_balance)


    username_to_id[username] = account_id


    token = jwt.encode(
        {"account_id": account_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        SECRET_KEY,
        algorithm="HS256"
    )


    return jsonify({
        "account_id": account_id,
        "balances": {code: curr.to_dict() for code, curr in users[account_id]["balances"].items()},
        "token": token
    })



@bp.post("/deposit")
@limiter.limit("5 per minute")
@token_required
def deposit(token_user_id):
    data = request.json
    account_id = data.get("account_id")
    amount = data.get("amount")
    currency_code = data.get("currency", "UAH").upper()

    if account_id != token_user_id:
        return jsonify({"error": "Unauthorized"}), 403
    if not validate_amount(amount):
        return jsonify({"error": "Invalid amount"}), 400
    if not validate_currency(currency_code):
        return jsonify({"error": "Unsupported currency"}), 400

    amount = float(amount)
    users[account_id]["balances"][currency_code].deposit(amount)
    log_transaction(account_id, "deposit", amount, currency_code)
    return jsonify({code: curr.to_dict() for code, curr in users[account_id]["balances"].items()})



@bp.post("/withdraw")
@limiter.limit("5 per minute")
@token_required
def withdraw(token_user_id):
    data = request.json
    account_id = data.get("account_id")
    amount = data.get("amount")
    currency_code = data.get("currency", "UAH").upper()

    if account_id != token_user_id:
        return jsonify({"error": "Unauthorized"}), 403
    if not validate_amount(amount):
        return jsonify({"error": "Invalid amount"}), 400
    if not validate_currency(currency_code):
        return jsonify({"error": "Unsupported currency"}), 400

    amount = float(amount)
    try:
        users[account_id]["balances"][currency_code].withdraw(amount)
        log_transaction(account_id, "withdraw", amount, currency_code)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({code: curr.to_dict() for code, curr in users[account_id]["balances"].items()})


@bp.post("/transfer")
@limiter.limit("5 per minute")
@token_required
def transfer(token_user_id):
    data = request.json
    from_account_id = data.get("from_account_id")
    to_account_id = data.get("to_account_id")
    amount = data.get("amount")
    currency_code = data.get("currency", "UAH").upper()

    if from_account_id != token_user_id:
        return jsonify({"error": "Unauthorized"}), 403
    if to_account_id not in users:
        return jsonify({"error": "Recipient not found"}), 404
    if not validate_amount(amount):
        return jsonify({"error": "Invalid amount"}), 400
    if not validate_currency(currency_code):
        return jsonify({"error": "Unsupported currency"}), 400

    amount = float(amount)

    try:

        users[from_account_id]["balances"][currency_code].withdraw(amount)

        users[to_account_id]["balances"][currency_code].deposit(amount)

        log_transaction(from_account_id, "transfer", amount, currency_code, recipient=to_account_id)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


    return jsonify({
        "from": {
            "account_id": from_account_id,
            "balances": {
                code: curr.to_dict()
                for code, curr in users[from_account_id]["balances"].items()
            }
        },
        "to": {
            "account_id": to_account_id,
            "balances": {
                code: curr.to_dict()
                for code, curr in users[to_account_id]["balances"].items()
            }
        }
    })



@bp.get("/balance")
@limiter.limit("5 per minute")
@token_required
def balance(token_user_id):
    return jsonify({code: curr.to_dict() for code, curr in users[token_user_id]["balances"].items()})



@bp.get("/transactions")
@limiter.limit("5 per minute")
@token_required
def get_transactions(token_user_id):
    user_tx = [tx for tx in transactions_log
               if tx["user"] == token_user_id or tx.get("recipient") == token_user_id]
    return jsonify(user_tx)
