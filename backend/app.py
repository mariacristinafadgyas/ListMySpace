from data_models import *
from flask import Flask
import os

app = Flask(__name__)

base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(base_dir, "../data", "list_my_space_db.sqlite")}'
db.init_app(app)

# Creates the tables defined in the models
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)