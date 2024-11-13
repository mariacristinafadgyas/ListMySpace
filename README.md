# List My Space

**ListMySpace** is an innovative platform that seamlessly connects property owners with potential buyers or tenants. This app serves as a direct marketplace where property owners can list their properties. This makes it easier for people all over the world to find their ideal home, commercial space or land. By simplifying this process, ListMySpace aims to make the search and purchase of real estate more accessible and efficient for everyone involved.<br>
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
- **User Update with Authorization**: Users can only update their own information, ensuring enhanced security and compliance.
- **Property Management**: Owners can manage their properties, including residential, commercial, and land listings.
- **Image Upload**: Supports uploading images with size limits.
- **Secure Password Storage**: Passwords are hashed and verified securely.
- **Dynamic Property Features**: Add and associate features with properties for a rich listing experience.
- **Geocoding Integration**: Automatically retrieves latitude and longitude based on provided addresses using Geoapify.
- **Error Handling**: Comprehensive error handling to manage validation and database integrity errors.
## Technologies Used

- **Backend**: Python, Flask
- **Database**: SQLite (configurable to other SQL databases)
- **Environment Management**: `dotenv` for managing secret keys
- **Websocket**: Flask-Sock for real-time updates
- **ORM**: SQLAlchemy
- **Migration**: Flask-Migrate
- **Security**: JWT for authentication
- **Image Handling**: Secure upload and storage of property images
- **Geocoding**: Integration with the `Geoapify API` for location services

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
## API Endpoints

1. **Register a New User**
- Endpoint: **/api/register**
- Method: **POST**
- Description:  Handles the addition of new users (Owner or Customer) to the database.
- Error Handling:<br>
  - `400`: Invalid role or missing username/password.
  - `404`: Username or email already exists in the database.
  - `500`: Internal server error if a database error occurs.
- Postman example:
```
localhost:5000/api/register
```
- Request Body:
```
{
  "username": "john_doe",
  "password": "securePassword123",
  "role": "owner",
  "name": "John Doe",
  "phone": "1234567890",
  "email": "john.doe@example.com",
  "company_name": "Doe Estates"  // Optional for owners
}

```
- Response (if successful):
```
{
"message": "Owner: john_doe successfully created!"
}
```
2.  **Get All Registered Users**
- Endpoint: **/api/get_all_users**
- Method: **GET**
- Roles Required: **Admin**, Authentication Required: **Yes, JWT-based** 
- Description:  Retrieves all registered users.
- Error Handling:<br>
  - `500`: Internal server error if a database error occurs.
- Postman example:
```
localhost:5000/api/get_all_users
```
- Headers
```
Authorization: Bearer <JWT_TOKEN>
```
- Response (if successful):
```
[
  {
    "user_id": 1,
    "username": "john_doe",
    "role": "OWNER",
    "is_active": true
  },
  ...
]
```
3. **User Login**
- Endpoint: **/api/login**
- Method: **POST**
- Description: Authenticates users and returns a JWT token.
- Error Handling:<br>
  - `400`: Missing username/password.
  - `401`: Invalid username or password.
  - `500`: Internal server error if a database error occurs.
- Postman example:
```
localhost:5000/api/login
```
- Request Body:
```
{
  "username": "john_doe",
  "password": "securePassword123"
}
```
- Response:
```
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI..."
}
```
4. **Delete a User**
- Endpoint: **/api/delete_user/<user_id>**
- Method: **DELETE**
- Roles Required: **Admin**, Authentication Required: **Yes, JWT-based** 
- Description: Deletes a user by user_id. 
- Error Handling:<br>
  - `404`: User not found.
  - `500`: Internal server error if a database error occurs.
- Postman example:
```
localhost:5000/api/delete_user/2
```
- Headers
```
Authorization: Bearer <JWT_TOKEN>
```
- Response:
```
{
  "message": "User and related data successfully deleted"
}
```
5. **List Properties Owned by an Owner**
- Endpoint: **/api/properties/<owner_id>**
- Method: **GET**
- Roles Required: **All**, Authentication Required: **Yes, JWT-based** 
- Description: Lists all properties (residential, commercial, and land) owned by a specific owner.
- Error Handling:<br>
  - `500`: Internal server error if a database error occurs.
- Postman example:
```
localhost:5000/api/properties/5
```
- Headers
```
Authorization: Bearer <JWT_TOKEN>
```
- Response:
```
{
  "owner": {
    "id": 5,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "1234567890",
    "company_name": "Doe Estates"
  },
  "residences": [
    {"id": 101, "title": "Cozy Apartment"},
    {"id": 102, "title": "Beachfront Condo"}
  ],
  "commercials": [
    {"id": 201, "title": "Downtown Office Space"}
  ],
  "land": [
    {"id": 301, "title": "5-Acre Plot"}
  ]
}
```
6. **Update an Existing User**
- Endpoint: **/api/users/<int:user_id>**
- Method: **PUT**
- Roles Required: **All**, Authentication Required: **Yes, JWT-based** 
- Description: Allows a user to update their own information securely.
- Error Handling:<br>
  - `403`: Unauthorized if the user tries to update another user's information. 
  - `404`: User not found.
  - `500`: Internal server error if a database error occurs.
- Postman example:
```
localhost:5000/api/users/5
```
- Headers
```
Authorization: Bearer <JWT_TOKEN>
```
- Request body: 
```
{
  "username": "new_username",
  "password": "new_password",
  "role": "CUSTOMER",
  "is_active": true
}
```
- Response:
```
{
  "message": "User updated successfully"
}
```
7. **Add a New Property**
- Endpoint: **/api/properties**
- Method: **POST**
- Roles Required: **Admin** or **Owner**, Authentication Required: **Yes, JWT-based** 
- Description: Allows an owner or admin to add a new property (residential, commercial, or land) with optional features and images (max 10). Unable to fetch latitude and longitude for the provided address
- Error Handling:<br>
  - `400`: No images part in the request. 
  - `400`: Maximum of 10 images can be uploaded. 
  - `400`: Invalid property type; choose either 'residence', 'commercial', or 'land'. 
  - `400`: Invalid owner ID
  - `400`: Unable to fetch latitude and longitude for the provided address
  - `500`: Internal server error if a database error occurs.
- Postman example:
```
localhost:5000/api/properties
```
- Headers
```
Authorization: Bearer <your_jwt_token>
Content-Type: multipart/form-data
```
- Request body: <br>

| Key           |      | Value                                |
|---------------|------|--------------------------------------|
| property_type | Text | residence                            |
| owner_id | Text | 2                                    |
| ad_action | Text | sale                                 |
| ad_title | Text | Beautiful Villa                      |
| ad_description | Text | Spacious villa with modern amenities |
| street_address | Text | 123 Main St                          |
| city | Text | Springfield                          |
| state | Text | USA                                  |
| zip_code | Text | 62704                                |
| price | Text | 350000                               |
| features | Text | pool,garden                          |
| images | File | Beautiful_Villa_1.jpeg               |
| images | File | Beautiful_Villa_2.jpeg               |
| images | File | Beautiful_Villa_3.jpeg               |
| images | File | Beautiful_Villa_4.jpeg               |
| images | File | Beautiful_Villa_5.jpeg               |
| images | File | Beautiful_Villa_6.jpeg               |
| images | File | Beautiful_Villa_7.jpeg               |
| images | File | Beautiful_Villa_8.jpeg               |
| images | File | Beautiful_Villa_9.jpeg               |
| images | File | Beautiful_Villa_10.jpeg              |

- Response:
```
{
  "message": "Residence 'Beautiful Villa' added successfully with images and features!"
}
```
