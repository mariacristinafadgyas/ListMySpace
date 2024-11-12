# List My Space

ListMySpace is an innovative platform that seamlessly connects property owners with potential buyers or tenants. This app serves as a direct marketplace where property owners can list their properties. This makes it easier for people all over the world to find their ideal home, commercial space or land. By simplifying this process, ListMySpace aims to make the search and purchase of real estate more accessible and efficient for everyone involved.<br>
<br>
Developed as a web application using Flask, ListMySpace offers robust features for efficient user and property management. Key features include user registration, login and JWT-based authentication to ensure secure access. Users can perform CRUD (Create, Read, Update, Delete) operations on both users and properties, increasing the versatility of the application.<br>
<br>
The backend uses SQLAlchemy for ORM (Object-Relational Mapping), providing a powerful and flexible database interaction layer. In addition, Flask-Migrate is used for seamless schema management, enabling easy database migrations and updates. This setup ensures that the application remains scalable and maintainable as it evolves.<br>
<br>
ListMySpace is not only about functionality, but also about creating an intuitive and user-friendly experience. The [application's interface](https://) is designed to be simple and accessible, helping users navigate the platform effortlessly . The ultimate goal is to connect people with their dream properties, whether for residential, commercial or investment purposes, and to foster a global community where real estate transactions are simplified and accessible to all.

## Features

- **User Authentication**: Register and log in using a secure JWT token.
- **Role Management**: Users can be assigned roles (`OWNER`, `CUSTOMER`, or `ADMIN`) with access controlled by custom middleware.
- **Admin Dashboard**: Admins can retrieve, update, and delete user data.
- **Property Management**: Owners can manage their properties, including residential, commercial, and land listings.
- **Image Upload**: Supports uploading images with size limits.
- **Secure Password Storage**: Passwords are hashed and verified securely.

## Technologies Used

- **Backend**: Python, Flask
- **Database**: SQLite (configurable to other SQL databases)
- **Environment Management**: `dotenv` for managing secret keys
- **Websocket**: Flask-Sock for real-time updates
- **ORM**: SQLAlchemy
- **Migration**: Flask-Migrate
- **Security**: JWT for authentication

## Installation

1. **Clone the Repository**
```
git clone https://github.com/mariacristinafadgyas/ListMySpace
cd ListMySpace
```
2. **Create a Virtual Environment**
```
python -m venv venv
```
| macOS | Windows |
| ------------- | ------------- |
| ```source venv/bin/activate``` | ```source venv\Scripts\activate```  |

3. **Install Dependencies**
```
pip install -r requirements.txt
```
4. **Set Up Environment Variables**
Create a `.env` file in the root directory and add the following::
```
SECRET_KEY = your_secret_key_here
```
> 🛎️ **NOTE** 🛎️ <br>
> - **Purpose**: The `SECRET_KEY` is used for signing and verifying JWT tokens to secure user authentication.
> - **Usage**: This key should be unique and kept confidential to prevent unauthorized access.
> - **Expiration**: JWT tokens signed with this key expire after 3 hours, requiring users to log in again for a new token.

```
FLASH_KEY = your_flash_key_here
```
> 🛎️ **NOTE** 🛎️ <br>
> - **Purpose**: The `FLASH_KEY` is used for enabling secure session-based flash messages in Flask.
> - **Usage**: Set this key to enable the app to display notifications or status messages to the user.

```
API_KEY_LAT_LONG = your_api_key_here
```
> 🛎️ **NOTE** 🛎️ <br>
> - **Purpose**: The `API_KEY_LAT_LONG` is used for integrating with the Geoapify API for geocoding and retrieving latitude and longitude data.
> - **Usage**: Register at [Geoapify](https://myprojects.geoapify.com/login) to obtain your API key and paste it here.
> - **Requirement**: This is essential for any features involving location-based queries or services in the app.
 
5. **Run Database Migrations**
```
flask db upgrade
```
6. **Run the application**
```
python app.py
```
