from db_constraints import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import Enum
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()  # Creates a db object


class User(db.Model):
    """Represents a user in the application."""

    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False, unique=True, index=True)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(Enum(RoleEnum), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships (Owner or Customer, depending on the role)
    owner = db.relationship('Owner', backref='user', uselist=False)  # One-to-One with Owner
    customer = db.relationship('Customer', backref='user', uselist=False)  # One-to-One with Customer

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def save(self):
        db.session.add(self)
        db.commit()

    def __repr__(self):
        return f"{self.username}"


class Owner(db.Model):
    """ Represents the property owners table in the database."""

    __tablename__ = 'owners'

    owner_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    company_name = db.Column(db.String(255), nullable=True)
    account_creation_date = db.Column(db.Date, nullable=False, default=db.func.current_date())

    # Foreign key linking to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    # Relationships with properties
    residences = db.relationship('Residence', backref='owner', lazy='dynamic')
    commercials = db.relationship('Commercial', backref='owner', lazy='dynamic')
    land = db.relationship('Land', backref='owner', lazy='dynamic')

    def __repr__(self):
        """Returns a string representation of the Property Owner object."""
        return f"Owner: {self.name},  ID: {self.owner_id}"


class Customer(db.Model):
    """ Represents a customer record in the 'customers' table."""

    __tablename__ = 'customers'

    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    account_creation_date = db.Column(db.Date, nullable=False, default=db.func.current_date())

    # Foreign key linking to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    def __repr__(self):
        """Returns a string representation of the Customer object."""
        return f"Customer {self.name}, ID: {self.customer_id}"


class Image(db.Model):
    """Represents the 'images' table in the database,
        storing file paths of images uploaded by property owners."""

    __tablename__ = 'images'

    image_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    residence_id = db.Column(db.Integer, db.ForeignKey('residences.residence_id'), nullable=True)
    commercial_id = db.Column(db.Integer, db.ForeignKey('commercials.commercial_id'), nullable=True)
    land_id = db.Column(db.Integer, db.ForeignKey('land.land_id'), nullable=True)
    url = db.Column(db.String(1024), nullable=False)

    def __repr__(self):
        """Returns a string representation of the Image object."""
        return f"<Image(image_id={self.image_id}, residence_id={self.residence_id}, url='{self.url}')>"


class Residence(db.Model):
    """Defines the structure of the 'residences' table in the database,
    representing real estate listings with attributes for various property details."""

    __tablename__ = 'residences'

    residence_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.owner_id'), nullable=False)
    ad_action = db.Column(Enum(ActionEnum), nullable=False)
    ad_title = db.Column(db.String(50), nullable=False)
    ad_description = db.Column(db.Text, nullable=False)
    images = db.relationship('Image', backref='residence', lazy=True)
    rooms_count = db.Column(db.Integer, nullable=False)
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    surface_area = db.Column(db.Float, nullable=False)
    land_area = db.Column(db.Float, nullable=True)
    floor_number = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Integer, nullable=False)
    ad_creation_date = db.Column(db.Date, nullable=False, default=db.func.current_date())

    def __repr__(self):
        """Returns a string representation of the Residence object."""
        return f"Residence {self.ad_title} for {self.ad_action}."


class Commercial(db.Model):
    """Defines the structure of the 'commercials' table in the database,
    representing commercial real estate listings with various property attributes."""

    __tablename__ = 'commercials'

    commercial_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.owner_id'), nullable=False)
    ad_action = db.Column(Enum(ActionEnum), nullable=False)
    commercial_category = db.Column(Enum(CommercialCategoryEnum), nullable=False)
    ad_title = db.Column(db.String(50), nullable=False)
    ad_description = db.Column(db.Text, nullable=False)
    images = db.relationship('Image', backref='commercial', lazy=True)
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    surface_area = db.Column(db.Float, nullable=False)
    land_area = db.Column(db.Float, nullable=False)
    floor_number = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Integer, nullable=False)
    ad_creation_date = db.Column(db.Date, nullable=False, default=db.func.current_date())

    def __repr__(self):
        """Returns a string representation of the Commercial object."""
        return f"Commercial {self.ad_title} for {self.ad_action}."


class Land(db.Model):
    """Defines the structure of the 'land' table in the database,
    representing real estate listings specifically for land properties."""

    __tablename__ = 'land'

    land_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.owner_id'), nullable=False)
    ad_action = db.Column(Enum(ActionEnum), nullable=False)
    land_type = db.Column(Enum(LandTypeEnum), nullable=False)
    land_category = db.Column(Enum(LandCategoryEnum), nullable=False)
    ad_title = db.Column(db.String(50), nullable=False)
    ad_description = db.Column(db.Text, nullable=False)
    images = db.relationship('Image', backref='land', lazy=True)
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    surface_area = db.Column(db.Float, nullable=True, default=0)
    land_area = db.Column(db.Float, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    ad_creation_date = db.Column(db.Date, nullable=False, default=db.func.current_date())

    def __repr__(self):
        """Returns a string representation of the Land object."""
        return f"Land {self.ad_title} for {self.ad_action}."


class Feature(db.Model):
    """Represents a feature that can be associated with properties."""

    __tablename__ = 'features'

    feature_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    residences = db.relationship('ResidenceFeature', backref='feature', lazy=True)
    commercials = db.relationship('CommercialFeature', backref='feature', lazy=True)
    land = db.relationship('LandFeature', backref='feature', lazy=True)


class ResidenceFeature(db.Model):
    """Association table for residences and features."""

    __tablename__ = 'residence_features'

    residence_id = db.Column(db.Integer, db.ForeignKey('residences.residence_id'), primary_key=True)
    feature_id = db.Column(db.Integer, db.ForeignKey('features.feature_id'), primary_key=True)


class CommercialFeature(db.Model):
    """Association table for commercials and features."""

    __tablename__ = 'commercial_features'

    commercial_id = db.Column(db.Integer, db.ForeignKey('commercials.commercial_id'), primary_key=True)
    feature_id = db.Column(db.Integer, db.ForeignKey('features.feature_id'), primary_key=True)


class LandFeature(db.Model):
    """Association table for land and features."""

    __tablename__ = 'land_features'

    land_id = db.Column(db.Integer, db.ForeignKey('land.land_id'), primary_key=True)
    feature_id = db.Column(db.Integer, db.ForeignKey('features.feature_id'), primary_key=True)


class Message(db.Model):
    """ Represents a message exchanged between a customer and an owner."""

    __tablename__ = 'messages'

    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.owner_id'), nullable=False)
    sender_type = db.Column(db.String(50), nullable=False)  # 'customer' or 'owner'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.now())
    customer = db.relationship('Customer', backref='messages_from_customer', lazy=True)
    owner = db.relationship('Owner', backref='messages_from_owner', lazy=True)

    def __repr__(self):
        """Returns a string representation of the Message object."""
        return f"Message from {self.sender_type} on {self.timestamp}: {self.content[:30]}..."


class Review(db.Model):
    """Represents a review given by a customer."""

    __tablename__ = 'reviews'

    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('owners.owner_id'), nullable=False)
    property_id = db.Column(db.Integer, nullable=False)  # Could be Residence, Commercial, or Land
    rating = db.Column(db.Integer, nullable=False)  # e.g., 1-5
    comments = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"{self.customer_id}, rating={self.rating}"


class Favorite(db.Model):
    """Represents a favorite property for a customer."""

    __tablename__ = 'favorites'

    favorite_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    property_id = db.Column(db.Integer, nullable=False)  # Stores the ID of the property
    # Stores the type of property (Residence, Commercial, Land)
    property_type = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"The preferred property of {self.customer_id} is {self.property_id}."


class Notification(db.Model):
    """Represents a notification for a customer."""

    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)  # Track if the notification has been read

    def __repr__(self):
        return f"{self.message[:30]}... sent to {self.customer_id}"
