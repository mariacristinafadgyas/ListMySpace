from database_constraints import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import Enum

db = SQLAlchemy()  # Creates a db object


class User(db.Model):
    """Represents a user in the application."""

    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(Enum(RoleEnum), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships (Owner or Customer, depending on the role)
    owner = db.relationship('Owner', backref='user', uselist=False) # One-to-One with Owner
    customer = db.relationship('Customer', backref='user', uselist=False) # One-to-One with Customer

    def __repr__(self):
        return f"User: {self.username}, role{self.role}"


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


