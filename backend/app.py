from data_models import *
import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, request, flash
from functools import wraps
import jwt
import os


# Loads and sets the environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
FLASH_KEY = os.getenv('FLASH_KEY')

app = Flask(__name__)
app.secret_key = FLASH_KEY

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


@app.route('/api/register', methods=['POST'])
def register_user():
    """Handles the addition of new users to the database."""

    user_data = request.get_json()

    # Extract user details
    username = user_data.get('username')
    password = user_data.get('password')
    role = user_data.get('role').upper()  # Normalize to uppercase - Should be 'OWNER' or 'CUSTOMER'
    name = user_data.get('name')
    phone = user_data.get('phone')
    email = user_data.get('email')
    company_name = user_data.get('company_name', None)  # Optional for owners

    # Check if the role is valid
    if role not in ['OWNER', 'CUSTOMER']:
        return jsonify({'error': 'Invalid role! Choose either OWNER or CUSTOMER'}), 400

    # Check if the username or email already exists
    if User.query.filter_by(username=username).first():
        flash('An user with this username already exists.')
        return jsonify({'error': 'Username already exists!'}), 400
    if Owner.query.filter_by(email=email).first() or Customer.query.filter_by(email=email).first():
        flash('An user with this email already exists.')
        return jsonify({'error': 'Email already exists!'}), 400

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    # Create a new user object
    new_user = User(username=username, role=RoleEnum[role])
    new_user.set_password(password)  # Hash and set the password

    try:
        # Save the new user
        db.session.add(new_user)
        db.session.flush()  # Flush to get the user_id for the associated Owner/Customer

        if role.upper() == 'OWNER':
            new_owner = Owner(
                name=name,
                phone=phone,
                email=email,
                company_name=company_name,
                user_id=new_user.user_id  # Link to the created user
            )
            db.session.add(new_owner)

        elif role.upper() == 'CUSTOMER':
            new_customer = Customer(
                name=name,
                phone=phone,
                email=email,
                user_id=new_user.user_id  # Link to the created user
            )
            db.session.add(new_customer)

        db.session.commit()  # Commit both user and owner/customer
        flash(f"{new_user.role.name.capitalize()}: {new_user} successfully created!")

        return jsonify({"message": f'{new_user.role.name.capitalize()}: {new_user} successfully created!'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/get_all_users', methods=['GET'])
def get_all_users():
    """Fetch all registered users from the database."""

    try:
        # Query all users from the database
        users = User.query.all()

        # Create a list of user dictionaries
        all_users = [
            {
                'user_id': user.user_id,
                'username': user.username,
                'role': user.role.name,  # Assuming role is an Enum
                'is_active': user.is_active
            }
            for user in users
        ]

        # Return the list of users as JSON
        return jsonify(all_users), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve users', 'details': str(e)}), 500


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
