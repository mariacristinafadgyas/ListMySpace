from data_models import *
import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from functools import wraps
import jwt
import os


# Loads and sets the environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')

app = Flask(__name__)

base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(base_dir, "../data", "list_my_space_db.sqlite")}'
db.init_app(app)


def token_required(f):
    """ Middleware (decorator) to protect routes by requiring a valid JWT token.
    Checks the 'Authorization' header for a valid token, verifies its signature,
    and ensures it's not expired. If invalid or missing, responds with 401 Unauthorized.
    Passes the decoded token payload to the route handler if valid."""
    @wraps(f)
    def decorated(*args, **kwargs):
        """The decorated function is the inner function that will actually wrap around
        the protected route. It receives the same arguments (*args, **kwargs) that the
        protected route would have received."""

        # Extracts the JWT from the Authorization header of the incoming request
        token = request.headers.get('Authorization')
        # print(f"Token received: {token}")

        if not token or not token.startswith('Bearer '):
            return jsonify({'message': 'Token is missing or invalid format'}), 401

        if token.startswith('Bearer '):
            token = token.split(' ')[1]  # Extract the token part only

        try:
            # Decode the JWT token
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        # Pass the payload to the route function
        return f(payload, *args, **kwargs)

    return decorated


@app.route('/api/login', methods=['POST'])
def login():
    """Login endpoint to authenticate users and return a JWT."""

    auth_data = request.get_json()
    username = auth_data.get('username')
    password = auth_data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    try:
        # Check if the user exists in the database
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            return jsonify({'message': 'Invalid username or password'}), 401

        # JWT payload creation
        payload = {
            'username': user.username,
            'role': user.role.name,  # Assuming RoleEnum
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=3)  # Token expires in 3 hours
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'token': token}), 200

    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


# # Creates the tables defined in the models
# with app.app_context():
#     db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
