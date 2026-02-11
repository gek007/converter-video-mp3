import datetime
import os

import jwt
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL

load_dotenv(".env")
load_dotenv(".env.local", override=True)


server = Flask(__name__)

# config mysql
server.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")
server.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.getenv("MYSQL_DB")
server.config["MYSQL_PORT"] = int(os.getenv("MYSQL_PORT") or 3306)

mysql = MySQL(server)


@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth:
        return jsonify({"error": "Missing credentials"}), 401

    cur = mysql.connection.cursor()
    try:
        res = cur.execute(
            "SELECT email, password FROM user WHERE email = %s", (auth.username,)
        )

        if res > 0:
            user_row = cur.fetchone()
            email = user_row[0]
            password = user_row[1]

            if auth.username != email or auth.password != password:
                return jsonify({"error": "Invalid credentials"}), 401
            
            token = create_jwt(auth.username, os.getenv("JWT_SECRET"), True)
            return jsonify({"token": token}), 200
        
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception:
        return jsonify({"error": "Database error"}), 500
    finally:
        cur.close()


@server.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers.get("Authorization")
    if not encoded_jwt:
        return jsonify({"error": "Missing credentials"}), 401

    try:
        encoded_jwt = encoded_jwt.split(" ")[1]
        decoded = jwt.decode(
            encoded_jwt, os.getenv("JWT_SECRET"), algorithms=["HS256"]
        )
        return jsonify(decoded), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    except IndexError:
        return jsonify({"error": "Invalid authorization header format"}), 401
    except Exception:
        return jsonify({"error": "Validation failed"}), 401


def create_jwt(username, secret, authz):
    """Create JWT token for authenticated user."""
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    return jwt.encode(
        {
            "username": username,
            "exp": now + datetime.timedelta(days=1),
            "iat": now,
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000, debug=True)
