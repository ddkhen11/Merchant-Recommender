from flask import Flask, render_template, redirect, jsonify, request
from flask_session import Session 
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash # new
import os
import json
import time
import requests
import xml.etree.ElementTree as ET
# from dotenv import load_dotenv
import pandas as pd

# new
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
key_override = os.environ.get("SUPABASE_KEY_OVERRIDE")

supabase = create_client(url, key_override)

# # to display data
# try:
#     data = supabase.table("user_info").select("*").execute()
#     print(data)
# except Exception as e:
#     print(f"Error: {str(e)}")

# to insert data
# data = supabase.table("user_info").insert({"first_name":"Tony", "last_name":"Gonzalez"}).execute()
data = supabase.table("user_info").select("hashed_password").eq("username", "no").execute()

list_data = list(data)

# if(check_password_hash(list_data[0][1][0]['hashed_password'], '123')):
    # print('\nSUCCESS\n')

# print(list_data[0][1][0]['hashed_password'])


r = pd.to_datetime(1607450357)
print(r)

url = 'https://api.finicity.com/aggregation/v3/customers/7006562263/transactions?fromDate=1607450357&toDate=1607450357&start=1&limit=1&sort=desc'
response = requests.get(url)

print(response.text)
# data = response.json()
# print(jsonify(data))



# ______________________________________________________
'''
app = Flask(__name__)

## Setting up Subabase DB -->
DB_PASSWORD = 'DanielKhen123!' # Dont touch
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:{DB_PASSWORD}@db.zwyjalcsnvikahllbkxm.supabase.co:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)
db = SQLAlchemy(app)

class users(db.Model):
    __tablename__ = 'user_info'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    username = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.Unicode(255), nullable=True)
    hashed_password = db.Column(db.String(255), nullable=False)
    
    def __init__(self, first_name, last_name, username, email, phone_number, hashed_password):
        self.first_name = first_name
        self.last_name = last_name        
        self.username = username
        self.email = email
        self.phone_number = phone_number
        self.hashed_password = hashed_password
    
    def __repr__(self):
        return f'<User: {self.username}'

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


@app.route('/create_testing_customer', methods=['POST'])
def create_testing_customer():
    # Fetch the Finicity-App-Token
    APP_TOKEN = fetch_app_token()

    # Headers for the create testing customer request
    headers = {
        "Content-Type": "application/json",
        "Finicity-App-Token": APP_TOKEN,
        "Finicity-App-Key": APP_KEY,
    }

    # Generate a unique username using a timestamp
    username = f"customer_{int(time.time())}"

    # Customer data to be sent in the request
    customer_data = {
        "username": username,      # Use the generated unique username
        "firstName": request.form['firstName'],    # Get first name from the form
        "lastName": request.form['lastName'],      # Get last name from the form
        "phone": request.form['phone'],            # Get phone from the form
        "email": request.form['email'],            # Get email from the form
    }

    # Endpoint for creating a testing customer
    CREATE_TESTING_CUSTOMER_ENDPOINT = "https://api.finicity.com/aggregation/v2/customers/testing"

    # Make a POST request to create the testing customer
    response = requests.post(CREATE_TESTING_CUSTOMER_ENDPOINT, headers=headers, json=customer_data)

    # Check the response status code
    if response.status_code == 201:
        try:
            # Try to parse the XML response
            root = ET.fromstring(response.content)
            # Check if the root element has the "id" element
            customer_id_element = root.find("id")
            if customer_id_element is not None:
                customer_id = customer_id_element.text
                return f"Testing customer created. Customer ID: {customer_id}", 201
            else:
                return f"Error: Missing 'id' element in the XML response. Status code: {response.status_code}", 500
        except ET.ParseError:
            # Handle the case where the response is not valid XML
            return f"Error: Invalid XML response from the API. Status code: {response.status_code}", 500
    else:
        # Handle the error case
        return f"Error creating testing customer. Status code: {response.status_code}", 500
    
@app.route('/create_active_customer', methods=['POST'])
def create_active_customer():
    # Fetch the Finicity-App-Token
    APP_TOKEN = fetch_app_token()

    # Headers for the create active customer request
    headers = {
        "Content-Type": "application/json",
        "Finicity-App-Token": APP_TOKEN,
        "Finicity-App-Key": APP_KEY,
    }

    # Customer data to be sent in the request
    customer_data = {
        "username": request.form['username'],
        "firstName": request.form['firstName'],
        "lastName": request.form['lastName'],
        "phone": request.form['phone'],
        "email": request.form['email'],
        "password": request.form['password'],
        "applicationId": "123456789"  # Include the applicationId as required
    }

    # salts and hashes plaintext password
    hashed_password = generate_password_hash(customer_data.password)
    customer_data["hashed_password"] = hashed_password

    user_info_entry = user_info(customer_data.first_name, customer_data.last_name, customer_data.username, \
            customer_data.email, customer_data.phone_number, customer_data.hashed_password)

    ##!! From here on (to end of function) is for creating an active user; This is a PAID feature of this API that we wont use for this project
    ##      Using data from demo customers that Mastercard provides
    ##      We are still adding functionaility for users to create accounts above

    # Endpoint for creating an active customer
    CREATE_ACTIVE_CUSTOMER_ENDPOINT = "https://api.finicity.com/aggregation/v2/customers/active"

    # Make a POST request to create the active customer
    response = requests.post(CREATE_ACTIVE_CUSTOMER_ENDPOINT, headers=headers, json=customer_data)
        # this gives back customer_id

    # Check the response status code
    if response.status_code == 201:
        # Active customer was successfully created
        # Parse the JSON response to extract the customer ID
        response_data = response.json()
        customer_id = response_data.get('id')
        return f"Active customer created. Customer ID: {customer_id}", 201
    else:
        # Handle the error case
        return f"Error creating active customer. Status code: {response.status_code}. " \
               f"Message: {response.text}", 500
    


if __name__ == '__main__':
    app.run(debug=True)

'''