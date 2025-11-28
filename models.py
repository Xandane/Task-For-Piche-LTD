from flask_bcrypt import Bcrypt
import datetime

bcrypt = Bcrypt()

CURRENCY_CODES = ["UAH", "USD", "EUR"]


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


users = {}  # account_id -> {username, password_hash, balances}
username_to_id = {}  # username -> account_id
transactions_log = []
next_id = 1


def log_transaction(user, action, amount=None, currency=None, recipient=None):
    transactions_log.append({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "user": user,
        "action": action,
        "amount": amount,
        "currency": currency,
        "recipient": recipient
    })

