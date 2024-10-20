from data_models import *
import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, request, flash
from flask_migrate import Migrate
from flask_sock import Sock
from functools import wraps
from get_info import get_lat_long
import json
import jwt
import os
from sqlalchemy import desc, func  # Import func to use ilike
from werkzeug.utils import secure_filename


# Loads and sets the environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
FLASH_KEY = os.getenv('FLASH_KEY')

app = Flask(__name__)
app.secret_key = FLASH_KEY

sock = Sock(app)

# Store connected users with their WebSocket connections
connected_users = {}

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

migrate = Migrate(app, db)


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

        # Check if the user role is passed in the payload (assuming it is included during login)
        user_role = payload.get('role')
        if not user_role:
            return jsonify({'message': 'User role not found in token'}), 403

        # Pass the payload to the route function
        return f(payload, *args, **kwargs)

    return decorated


def admin_required(f):
    """Middleware to protect admin routes."""

    @wraps(f)
    def decorated(payload, *args, **kwargs):
        user_role = payload.get('role')
        if user_role != 'ADMIN':
            return jsonify({'message': 'Access forbidden: Admins only'}), 403
        return f(payload, *args, **kwargs)

    return decorated


def owner_or_admin_required(f):
    """Middleware to protect routes for owners or admins."""

    @wraps(f)
    def decorated(payload, *args, **kwargs):
        user_role = payload.get('role')
        if user_role not in ['OWNER', 'ADMIN']:
            return jsonify({'message': 'Access forbidden: Owners or Admins only'}), 403
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
@token_required
@admin_required
def get_all_users(payload):
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


@app.route('/api/delete_user/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(payload, user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    try:
        # If user is an owner, delete associated properties (cascading should handle it)
        if user.role == RoleEnum.OWNER:
            owner = Owner.query.filter_by(user_id=user.user_id).first()
            print(f"Prop to delete: {owner}")
            if owner:
                # Automatic deletion of the associated residences, businesses
                # and properties based on the cascade settings
                db.session.delete(owner)
                print(f"Deleted Owner: {owner.name}, ID: {owner.owner_id} and related properties.")

        # If user is a customer, delete associated favorites, messages, reviews, and notifications (cascade takes care)
        elif user.role == RoleEnum.CUSTOMER:
            customer = Customer.query.filter_by(user_id=user.user_id).first()
            if customer:
                db.session.delete(customer)
                print(f"Deleted Customer: {customer.name}, ID: {customer.customer_id} and related data.")

        # Finally, delete the user record itself
        db.session.delete(user)
        db.session.commit()
        print(f"Deleted User: {user.username}, ID: {user.user_id}")

        return jsonify({"message": "User and related data successfully deleted"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/properties/<int:owner_id>', methods=['GET'])
@token_required
def list_owner_properties(payload, owner_id):
    """Allows an owner to list all their properties (residential, commercial, and land)."""

    try:
        owner = Owner.query.get_or_404(owner_id)  # This will raise 404 if the owner doesn't exist

        # Fetch all property types
        residences = Residence.query.filter_by(owner_id=owner_id).all()
        commercials = Commercial.query.filter_by(owner_id=owner_id).all()
        land = Land.query.filter_by(owner_id=owner_id).all()

        # Ensured that the 'owner' can be serialized; if not, convert to a dictionary or use a serialize method.
        owner_data = {
            "id": owner.owner_id,
            "name": owner.name,
            "email": owner.email,
            "phone": owner.phone,
            "company_name": owner.company_name
        }

        # Prepare response data
        properties = {
            "owner": owner_data,
            "residences": [{"id": res.residence_id, "title": res.ad_title} for res in residences],
            "commercials": [{"id": com.commercial_id, "title": com.ad_title} for com in commercials],
            "land": [{"id": la.land_id, "title": la.ad_title} for la in land]
        }

        return jsonify(properties), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(payload, user_id):
    # Get the user by ID
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Parse the request data
    data = request.get_json()

    # Update the user fields (only if provided)
    if 'username' in data:
        user.username = data['username']

    if 'password' in data:
        user.set_password(data['password'])  # Use the set_password method to hash the password

    if 'role' in data:
        # Check if the role is valid
        if data['role'] in RoleEnum.value2member_map_:
            user.role = RoleEnum(data['role'])
        else:
            return jsonify({"error": "Invalid role"}), 400

    if 'is_active' in data:
        user.is_active = data['is_active']

    try:
        # Save the changes to the database
        db.session.commit()
        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def allowed_file(filename):
    """Helper function to check if the uploaded file is an allowed image type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/properties', methods=['POST'])
@token_required
@owner_or_admin_required
def add_property(payload):
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

    # Check if owner_id exists in the database
    owner = Owner.query.get(owner_id)
    if not owner:
        return jsonify({"error": "Invalid owner ID. The specified owner does not exist."}), 400

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


@app.route('/api/properties', methods=['GET'])
def get_properties():
    # Retrieve query parameters
    ad_action = request.args.get('ad_action')  # sale, rent
    city = request.args.get('city')
    state = request.args.get('state')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    min_surface_area = request.args.get('min_surface_area', type=float)
    max_surface_area = request.args.get('max_surface_area', type=float)
    min_land_area = request.args.get('min_land_area', type=float)
    max_land_area = request.args.get('max_land_area', type=float)
    features = request.args.getlist('features')  # List of features e.g., ['balcony', 'parking']
    property_type = request.args.get('property_type')  # Optional: 'residence', 'commercial', or 'land'
    page = request.args.get('page', 1, type=int)

    # Prepare an empty query list to combine results if property_type is not provided
    queries = []

    # Determine which property model(s) to query
    if property_type == 'residence' or property_type is None:
        residence_query = Residence.query
        if ad_action:
            residence_query = residence_query.filter(
                func.lower(Residence.ad_action) == ad_action.lower())
        if city:
            residence_query = residence_query.filter(func.lower(Residence.city) == city.lower())
        if state:
            residence_query = residence_query.filter(func.lower(Residence.state) == state.lower())
        if min_price is not None:
            residence_query = residence_query.filter(Residence.price >= min_price)
        if max_price is not None:
            residence_query = residence_query.filter(Residence.price <= max_price)
        if min_surface_area is not None:
            residence_query = residence_query.filter(Residence.surface_area >= min_surface_area)
        if max_surface_area is not None:
            residence_query = residence_query.filter(Residence.surface_area <= max_surface_area)
        # Land area filters apply here if available
        if min_land_area is not None:
            residence_query = residence_query.filter(Residence.land_area >= min_land_area)
        if max_land_area is not None:
            residence_query = residence_query.filter(Residence.land_area <= max_land_area)

        if features:
            residence_query = residence_query.join(ResidenceFeature).join(Feature).filter(Feature.name.in_(features))

        residence_query = residence_query.order_by(desc(Residence.ad_creation_date))
        queries.append(residence_query)

    if property_type == 'commercial' or property_type is None:
        commercial_query = Commercial.query
        if ad_action:
            commercial_query = commercial_query.filter(
                func.lower(Commercial.ad_action) == ad_action.lower())
        if city:
            commercial_query = commercial_query.filter(func.lower(Commercial.city) == city.lower())
        if state:
            commercial_query = commercial_query.filter(func.lower(Commercial.state) == state.lower())
        if min_price is not None:
            commercial_query = commercial_query.filter(Commercial.price >= min_price)
        if max_price is not None:
            commercial_query = commercial_query.filter(Commercial.price <= max_price)
        if min_surface_area is not None:
            commercial_query = commercial_query.filter(Commercial.surface_area >= min_surface_area)
        if max_surface_area is not None:
            commercial_query = commercial_query.filter(Commercial.surface_area <= max_surface_area)
        # Land area filters apply here if available
        if min_land_area is not None:
            commercial_query = commercial_query.filter(Commercial.land_area >= min_land_area)
        if max_land_area is not None:
            commercial_query = commercial_query.filter(Commercial.land_area <= max_land_area)

        if features:
            commercial_query = commercial_query.join(CommercialFeature).join(Feature).filter(Feature.name.in_(features))

        commercial_query = commercial_query.order_by(desc(Commercial.ad_creation_date))
        queries.append(commercial_query)

    if property_type == 'land' or property_type is None:
        land_query = Land.query
        if ad_action:
            land_query = land_query.filter(func.lower(Land.ad_action) == ad_action.lower())
        if city:
            land_query = land_query.filter(func.lower(Land.city) == city.lower())
        if state:
            land_query = land_query.filter(func.lower(Land.state) == state.lower())
        if min_price is not None:
            land_query = land_query.filter(Land.price >= min_price)
        if max_price is not None:
            land_query = land_query.filter(Land.price <= max_price)

        # Land area filter applies to land properties
        if min_land_area is not None:
            land_query = land_query.filter(Land.land_area >= min_land_area)
        if max_land_area is not None:
            land_query = land_query.filter(Land.land_area <= max_land_area)

        if features:
            land_query = land_query.join(LandFeature).join(Feature).filter(Feature.name.in_(features))

        land_query = land_query.order_by(desc(Land.ad_creation_date))
        queries.append(land_query)

    # Combine queries for all property types if no specific property type is selected
    if not property_type:
        from sqlalchemy import union_all
        combined_query = union_all(*[query.statement for query in queries])
        query = db.session.query(Residence).from_statement(combined_query).order_by(
            desc('ad_creation_date'))  # Adjusted sorting for combined results
    else:
        query = queries[0]  # If a specific property type is chosen, use its query directly

    # Pagination
    paginated_result = query.paginate(page=page, per_page=10, error_out=False)

    # Create the response with property data
    properties = []
    for property in paginated_result.items:
        property_data = {
            'id': getattr(property, 'residence_id',
                          getattr(property, 'commercial_id', getattr(property, 'land_id', None))),
            'title': property.ad_title,
            'description': property.ad_description,
            'city': property.city,
            'state': property.state,
            'price': property.price,
            # Include surface_area and land_area for all property types
            'surface_area': property.surface_area if hasattr(property, 'surface_area') else None,
            'land_area': property.land_area if hasattr(property, 'land_area') else None,
            'latitude': property.latitude,
            'longitude': property.longitude,
            'images': [image.url for image in property.images]
        }
        properties.append(property_data)

    # Response structure
    response = {
        'properties': properties,
        'page': paginated_result.page,
        'pages': paginated_result.pages,
        'total_properties': paginated_result.total
    }

    return jsonify(response)


@app.route('/api/delete_property', methods=['DELETE'])
@token_required
@owner_or_admin_required
def delete_property(payload):
    """
    Deletes a property from the database (Residence, Commercial, or Land) along with its
    associated features. The client should provide the property_type and property_id in
    the request."""

    # Extract property type and ID from the request
    data = request.json
    property_type = data.get('property_type')  # Should be either 'residence', 'commercial', or 'land'
    property_id = data.get('property_id')

    if not property_type or not property_id:
        return jsonify({"error": "Property type and property ID are required."}), 400

    try:
        # Depending on the property type, query the relevant table and delete associated features
        if property_type == 'residence':
            property_to_delete = Residence.query.get(property_id)
            if property_to_delete:
                # Delete associated residence features
                ResidenceFeature.query.filter_by(residence_id=property_id).delete()

        elif property_type == 'commercial':
            property_to_delete = Commercial.query.get(property_id)
            if property_to_delete:
                # Delete associated commercial features
                CommercialFeature.query.filter_by(commercial_id=property_id).delete()

        elif property_type == 'land':
            property_to_delete = Land.query.get(property_id)
            if property_to_delete:
                # Delete associated land features
                LandFeature.query.filter_by(land_id=property_id).delete()
        else:
            return jsonify({"error": "Invalid property type."}), 400

        # Check if the property exists
        if property_to_delete is None:
            return jsonify({"error": "Property not found."}), 404

        # If found, delete the property
        db.session.delete(property_to_delete)
        db.session.commit()

        return jsonify({"message": f"{property_type.capitalize()} with ID {property_id} and"
                                   f" its associated features have been deleted."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/properties/<string:property_type>/<int:property_id>', methods=['PUT'])
@token_required
@owner_or_admin_required
def update_property(payload, property_type, property_id):
    try:
        # Check if the request contains multipart/form-data
        if request.content_type.startswith('multipart/form-data'):
            # Extract data from form (similar to how it works in the POST route)
            data = request.form.to_dict()
            owner_id = data.get('owner_id')
        else:
            # Otherwise, handle as a regular JSON request
            data = request.json
            owner_id = data.get('owner_id')

        # Ensure owner_id exists
        if not owner_id:
            return jsonify({"error": "Owner ID is required"}), 400

        # Determine the property type
        if property_type == 'residence':
            property_obj = Residence.query.get_or_404(property_id)
        elif property_type == 'commercial':
            property_obj = Commercial.query.get_or_404(property_id)
        elif property_type == 'land':
            property_obj = Land.query.get_or_404(property_id)
        else:
            return jsonify({"error": "Invalid property type"}), 400

        # Check if the owner is the same
        if property_obj.owner_id != int(owner_id):
            return jsonify({"error": "Unauthorized action"}), 403

        # Update fields based on incoming data
        for key, value in data.items():
            if hasattr(property_obj, key):
                setattr(property_obj, key, value)

        # If updating images is required, handle file uploads (optional)
        if request.files:
            images = request.files.getlist('images')
            for image in images:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(filepath)
                    # Handle saving or updating the image in the database
                    new_image = Image(url=filepath)
                    # Link the image to the correct property type
                    if property_type == 'residence':
                        new_image.residence_id = property_obj.residence_id
                    elif property_type == 'commercial':
                        new_image.commercial_id = property_obj.commercial_id
                    elif property_type == 'land':
                        new_image.land_id = property_obj.land_id
                    db.session.add(new_image)

        db.session.commit()

        return jsonify({"message": f"{property_type.capitalize()} property updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@sock.route('/api/chat/<user_id>')
@token_required
def chat(payload, ws, user_id):
    """
    WebSocket route for real-time chat communication between users (Owners and Customers).
    This route allows users (either Owners or Customers) to send and receive messages in real-time.

    Parameters:
    - ws: The WebSocket connection object.
    - user_id: The ID of the user initiating the WebSocket connection.
    """

    # Fetch the user from the database (can be an owner or a customer)
    user = User.query.filter_by(user_id=user_id).first()

    if not user:
        ws.send(json.dumps({"error": "User not found"}))
        return

    # Store the WebSocket connection for the user
    connected_users[user_id] = ws

    try:
        while True:
            # Wait for a message from this user
            message = ws.receive()

            if message:
                # Parse the message
                message_data = json.loads(message)
                recipient_id = message_data['to']
                text = message_data['text']

                # Check if recipient exists in the database
                recipient_user = User.query.filter_by(user_id=recipient_id).first()
                if not recipient_user:
                    ws.send(json.dumps({"error": f"Recipient with ID {recipient_id} not found."}))
                    continue

                # Determine sender and recipient roles (Owner or Customer)
                if user.customer:
                    sender_role = 'customer'
                    customer_id = user.customer.customer_id
                    owner_id = recipient_user.owner.owner_id if recipient_user.owner else None
                elif user.owner:
                    sender_role = 'owner'
                    owner_id = user.owner.owner_id
                    customer_id = recipient_user.customer.customer_id if recipient_user.customer else None
                else:
                    ws.send(json.dumps({"error": "Invalid sender role."}))
                    continue

                if not (customer_id or owner_id):
                    ws.send(json.dumps({"error": "Invalid recipient role."}))
                    continue

                # Save the message to the database
                new_message = Message(
                    customer_id=customer_id,
                    owner_id=owner_id,
                    sender_type=sender_role,
                    content=text
                )
                db.session.add(new_message)
                db.session.commit()

                # Check if the recipient is connected via WebSocket
                if recipient_id in connected_users:
                    # Send the message to the recipient
                    connected_users[recipient_id].send(json.dumps({
                        "from": user_id,
                        "text": text,
                        "timestamp": new_message.timestamp.isoformat()
                    }))
                else:
                    # Notify the sender that the recipient is not connected
                    ws.send(json.dumps({"error": f"User {recipient_id} is not connected."}))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Remove the user from connected_users when the connection closes
        if user_id in connected_users:
            del connected_users[user_id]


# # Creates the tables defined in the models
# with app.app_context():
#     db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
