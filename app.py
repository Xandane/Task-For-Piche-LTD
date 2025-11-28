from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from routes import bp
import jwt

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"


def get_user_key():
    from flask import request
    token = request.headers.get("Authorization")
    if token:
        try:
            token = token.split()[1]
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            return str(data.get("account_id", get_remote_address()))
        except:
            pass
    return get_remote_address()

limiter = Limiter(
    key_func=get_user_key,
    default_limits=["5 per minute"],
    storage_uri="memory://"
)
limiter.init_app(app)


app.register_blueprint(bp)

@app.get("/")
def home():
    return jsonify({"message": "Bank API with JWT + multi-currency is running"})

if __name__ == "__main__":
    app.run(debug=True)

