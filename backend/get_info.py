from dotenv import load_dotenv
import os
import requests


load_dotenv()
API_KEY_LAT_LONG = os.getenv('API_KEY_LAT_LONG')


def get_lat_long(address):
    """
    Fetches latitude and longitude for a given address using the Geoapify
    Geocoding API. Returns a tuple containing (latitude, longitude) if the
    address is found, otherwise None.
    """

    url = "https://api.geoapify.com/v1/geocode/search"

    # Define the parameters for the API request
    params = {
        "text": address,
        "apiKey": API_KEY_LAT_LONG
    }

    # Send a GET request to the Geoapify API
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        # Check if any results were returned
        if data['features']:
            # Extract latitude and longitude from the first result
            latitude = data['features'][0]['properties']['lat']
            longitude = data['features'][0]['properties']['lon']
            return latitude, longitude
        else:
            print("No results found for the given address.")
            return None
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def main():
    address = "Lietzenburger Straße 91, Emmendorf, Germany"
    coordinates = get_lat_long(address)
    print(coordinates)
    if coordinates:
        print(f"Latitude: {coordinates[0]}, Longitude: {coordinates[1]}")


if __name__ == "__main__":
    main()