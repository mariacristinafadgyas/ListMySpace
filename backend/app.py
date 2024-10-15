from data_models import *
import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, request, flash
from functools import wraps
from get_info import get_lat_long
import jwt
import os
from werkzeug.utils import secure_filename


# Loads and sets the environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
FLASH_KEY = os.getenv('FLASH_KEY')

app = Flask(__name__)
app.secret_key = FLASH_KEY

base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(base_dir, "../data", "list_my_space_db.sqlite")}'


# Set the folder where images will be stored (local or a cloud service)
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed image formats
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size


# Add configuration for the app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

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


def allowed_file(filename):
    """Helper function to check if the uploaded file is an allowed image type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/properties', methods=['POST'])
def add_property():
    """Allows an owner to add a new property (residential, commercial, or land) with
    up to 10 images and optional features."""

    # Check if the post request has the 'files' part for images
    if 'images' not in request.files:
        return jsonify({"error": "No images part in the request"}), 400

    images = request.files.getlist('images')  # Get the list of uploaded images
    if len(images) > 10:
        return jsonify({"error": "You can upload a maximum of 10 images."}), 400

    # Handle other property data (JSON)
    user_data = request.form.to_dict()  # Use form for multipart data
    property_type = user_data.get('property_type').lower()  # Property type: 'residence', 'commercial', 'land'

    # Validate the property type
    if property_type not in ['residence', 'commercial', 'land']:
        return jsonify({"error": "Invalid property type. Choose either 'residence', 'commercial', or 'land'."}), 400

    # Extract common property fields
    owner_id = user_data.get('owner_id')
    ad_action = user_data.get('ad_action')
    ad_title = user_data.get('ad_title')
    ad_description = user_data.get('ad_description')
    street_address = user_data.get('street_address')
    city = user_data.get('city')
    state = user_data.get('state')
    zip_code = user_data.get('zip_code')
    price = user_data.get('price')

    # Optional: Get the list of features (as a comma-separated string)
    features = user_data.get('features')  # Example: 'balcony,garden,parking space'
    feature_list = [f.strip().lower() for f in features.split(',')] if features else []

    # Build full address for geocoding
    full_address = f"{street_address}, {city}, {state}, {zip_code}"

    # Get latitude and longitude using the Geoapify API
    lat_long = get_lat_long(full_address)
    if lat_long is None:
        return jsonify({"error": "Unable to fetch latitude and longitude for the provided address."}), 400

    latitude, longitude = lat_long

    try:
        # Add property based on the type
        if property_type == 'residence':
            new_property = Residence(
                owner_id=owner_id,
                ad_action=ad_action,
                ad_title=ad_title,
                ad_description=ad_description,
                street_address=street_address,
                city=city,
                state=state,
                zip_code=zip_code,
                latitude=latitude,
                longitude=longitude,
                price=price,
                rooms_count=user_data.get('rooms_count'),
                floor_number=user_data.get('floor_number'),
                surface_area=user_data.get('surface_area'),
                land_area=user_data.get('land_area'),
            )
            db.session.add(new_property)
            db.session.commit()  # Commit to get the property ID

            # Associate features with residence
            for feature_name in feature_list:
                feature = Feature.query.filter_by(name=feature_name).first()
                if not feature:
                    # If the feature doesn't exist, create it
                    feature = Feature(name=feature_name)
                    db.session.add(feature)
                    db.session.commit()  # Commit to get the feature_id

                # Add feature association to residence
                residence_feature = ResidenceFeature(residence_id=new_property.residence_id,
                                                     feature_id=feature.feature_id)
                db.session.add(residence_feature)

            # Save uploaded images
            for image in images:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(filepath)  # Save the file to the upload folder

                    # Add the image record to the Image table
                    new_image = Image(residence_id=new_property.residence_id, url=filepath)
                    db.session.add(new_image)

        elif property_type == 'commercial':
            new_property = Commercial(
                owner_id=owner_id,
                ad_action=ad_action,
                ad_title=ad_title,
                ad_description=ad_description,
                street_address=street_address,
                city=city,
                state=state,
                zip_code=zip_code,
                latitude=latitude,
                longitude=longitude,
                price=price,
                commercial_category=user_data.get('commercial_category'),  # Specific to commercial properties
                surface_area=user_data.get('surface_area'),
                land_area=user_data.get('land_area'),
                floor_number=user_data.get('floor_number'),
            )
            db.session.add(new_property)
            db.session.commit()  # Commit to get the property ID

            # Associate features with commercial
            for feature_name in feature_list:
                feature = Feature.query.filter_by(name=feature_name).first()
                if not feature:
                    feature = Feature(name=feature_name)
                    db.session.add(feature)
                    db.session.commit()

                commercial_feature = CommercialFeature(commercial_id=new_property.commercial_id,
                                                       feature_id=feature.feature_id)
                db.session.add(commercial_feature)

            # Save uploaded images
            for image in images:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(filepath)

                    new_image = Image(commercial_id=new_property.commercial_id, url=filepath)
                    db.session.add(new_image)

        elif property_type == 'land':
            new_property = Land(
                owner_id=owner_id,
                ad_action=ad_action,
                ad_title=ad_title,
                ad_description=ad_description,
                street_address=street_address,
                city=city,
                state=state,
                zip_code=zip_code,
                latitude=latitude,
                longitude=longitude,
                price=price,
                land_type=user_data.get('land_type'),  # Specific to land
                land_category=user_data.get('land_category'),
                land_area=user_data.get('land_area'),
            )
            db.session.add(new_property)
            db.session.commit()  # Commit to get the property ID

            # Associate features with land
            for feature_name in feature_list:
                feature = Feature.query.filter_by(name=feature_name).first()
                if not feature:
                    feature = Feature(name=feature_name)
                    db.session.add(feature)
                    db.session.commit()

                land_feature = LandFeature(land_id=new_property.land_id, feature_id=feature.feature_id)
                db.session.add(land_feature)

            # Save uploaded images
            for image in images:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(filepath)

                    new_image = Image(land_id=new_property.land_id, url=filepath)
                    db.session.add(new_image)

        db.session.commit()  # Commit all the features and images

        return jsonify(
            {"message": f"{property_type.capitalize()} '{ad_title}' added successfully with images and features!"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# # Creates the tables defined in the models
# with app.app_context():
#     db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
