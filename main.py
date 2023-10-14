from flask import Flask, render_template, redirect, jsonify
import os
import json
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve your credentials from the environment variables
PARTNER_ID = os.getenv("PARTNER_ID")
PARTNER_SECRET = os.getenv("PARTNER_SECRET")
APP_KEY = os.getenv("APP_KEY")

def fetch_app_token():
    AUTH_ENDPOINT = "https://api.finicity.com/aggregation/v2/partners/authentication"
    headers = {
        "Content-Type": "application/json",
        "Finicity-App-Key": APP_KEY,
        "Accept": "application/json"
    }
    data = {
        "partnerId": PARTNER_ID,
        "partnerSecret": PARTNER_SECRET
    }
    response = requests.post(AUTH_ENDPOINT, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get("token")
    else:
        raise ValueError(f"Failed to authenticate. Response: {response.text}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect_to_bank')
def connect_to_bank():
    # Fetch the Finicity-App-Token
    APP_TOKEN = fetch_app_token()

    # Headers for subsequent API requests
    headers = {
        "Content-Type": "application/json",
        "Finicity-App-Token": APP_TOKEN,
        "Finicity-App-Key": APP_KEY
    }

    # First, add a test customer
    ADD_CUSTOMER_ENDPOINT = "https://api.finicity.com/aggregation/v2/customers/testing"
    customer_data = {
        "username": "customerusername1ee212213123",  # Change this to a unique username
        "firstName": "John",
        "lastName": "Smith",
        "phone": "1-801-984-4200",
        "email": "myname@mycompany.com"
    }
    response = requests.post(ADD_CUSTOMER_ENDPOINT, headers=headers, json=customer_data)

    # Check if the response contains valid XML
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError:
        return f"Error: Invalid XML response from the API. Status code: {response.status_code}", 500

    # Check if the root element has the "id" element
    customer_id_element = root.find("id")
    if customer_id_element is not None:
        customer_id = customer_id_element.text
    else:
        return f"Error: Missing 'id' element in the XML response. Status code: {response.status_code}", 500

    # Generate the Connect URL for the test customer
    CONNECT_URL_ENDPOINT = "https://api.finicity.com/connect/v2/generate"
    data = {
        "partnerId": PARTNER_ID,
        "customerId": customer_id
    }
    response = requests.post(CONNECT_URL_ENDPOINT, headers=headers, json=data)

    # Check if the response contains valid JSON
    try:
        response_data = response.json()
    except json.JSONDecodeError:
        return f"Error: Invalid JSON response from the API. Status code: {response.status_code}", 500

    connect_url = response_data.get("link")

    # Redirect the user to the Connect URL
    return redirect(connect_url)


@app.route('/login', methods=['POST', 'GET'])
def login_user():

    login_success = True # default

    # login user
    

    if(login_success):
        return render_template('other_page.html')
    else:   #login failed
        print("\nPassword or username incorrect. Try again\n")
        return render_template('login.html')
    


if __name__ == '__main__':
    app.run(debug=True)