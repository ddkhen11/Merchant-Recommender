from flask import Flask, render_template, redirect, jsonify, request
from flask_session import Session 
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash # new
import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from supabase import create_client
import openai
from dotenv import load_dotenv

app = Flask(__name__)

## Setting up Subabase DB -->
""" DB_PASSWORD = 'DanielKhen123!' # Dont touch
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
        return f'<User: {self.username}' """

# Load environment variables from .env file
load_dotenv()

# Retrieve your credentials from the environment variables
PARTNER_ID = os.getenv("PARTNER_ID")
PARTNER_SECRET = os.getenv("PARTNER_SECRET")
APP_KEY = os.getenv("APP_KEY")
OPENAI_KEY = os.getenv("OPENAI_KEY")

# database setup

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY") # for low level users (doesnt work right now)
key_override = os.environ.get("SUPABASE_KEY_OVERRIDE") # for master users 

supabase = create_client(url, key_override)


# Function to parse XML transactions
def parse_xml_transactions(xml_content):
    transactions = []
    try:
        root = ET.fromstring(xml_content)
        for transaction_element in root.findall('.//transaction'):
            # Parse normalizedPayeeName and amount from XML
            normalized_payee_name = transaction_element.find('.//categorization/normalizedPayeeName').text
            amount = float(transaction_element.find('.//amount').text)

            # Create a dictionary with the extracted data
            transaction_data = {
                "normalizedPayeeName": normalized_payee_name,
                "amount": amount
            }

            transactions.append(transaction_data)
    except ET.ParseError as e:
        print(f"Failed to parse XML transactions: {str(e)}")
    return transactions
    

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
        "password": request.form['password']       # Get password from form
    }

    # salts and hashes plaintext password
    hashed_password = generate_password_hash(customer_data.password)
    customer_data["hashed_password"] = hashed_password # adds to customer_data object

    # implement temporary user ids now
    example_temp_id = 123456789
    customer_data["temp_user_id"] = example_temp_id # adds to customer_data object

    # insert data into database
    data = supabase.table("user_info").insert({"temp_user_id":customer_data.temp_user_id, "first_name":customer_data.firstName, "last_name":customer_data.lastName,\
                                               "username":customer_data.username, "phone_number":customer_data.phone, "email":customer_data.email,\
                                                "password":customer_data.password, "hashed_password":customer_data.hashed_password}).execute()
    data = supabase.table("user_info").select("*").execute()
    print(data)

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
    
""" @app.route('/create_active_customer', methods=['POST'])
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
               f"Message: {response.text}", 500 """
    

@app.route('/show_create_customer_form', methods=['GET'])
def show_create_customer_form():
    return render_template('create_customer.html')
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect_to_bank/<customer_id>', methods=['GET'])
def connect_to_bank(customer_id):
    # Fetch the Finicity-App-Token
    APP_TOKEN = fetch_app_token()

    # Headers for subsequent API requests
    headers = {
        "Content-Type": "application/json",
        "Finicity-App-Token": APP_TOKEN,
        "Finicity-App-Key": APP_KEY
    }

    # Define the Finicity API endpoint for generating the Connect URL for the real customer
    CONNECT_URL_ENDPOINT = "https://api.finicity.com/connect/v2/generate"
    data = {
        "partnerId": PARTNER_ID,
        "customerId": customer_id  # Use the customerId of the existing real customer
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

@app.route('/fetch_transactions/<customer_id>', methods=['GET'])
def fetch_transactions(customer_id):
    # Fetch the Finicity-App-Token
    APP_TOKEN = fetch_app_token()

    # Headers for subsequent API requests
    headers = {
        "Content-Type": "application/json",
        "Finicity-App-Token": APP_TOKEN,
        "Finicity-App-Key": APP_KEY
    }

    # Define the Finicity API endpoint for checking if the customer exists
    CUSTOMER_EXISTS_ENDPOINT = f"https://api.finicity.com/aggregation/v1/customers/{customer_id}"

    # Make a GET request to check if the customer exists
    response = requests.get(CUSTOMER_EXISTS_ENDPOINT, headers=headers)

    # Check the response status code
    if response.status_code == 200:
        # Customer exists, proceed to refresh customer accounts
        # Define the endpoint for refreshing customer accounts
        REFRESH_ACCOUNTS_ENDPOINT = f"https://api.finicity.com/aggregation/v1/customers/{customer_id}/accounts"

        # Make a POST request to refresh customer accounts
        response = requests.post(REFRESH_ACCOUNTS_ENDPOINT, headers=headers, json={})

        # Check the response status code
        if response.status_code == 200:
            # Accounts were successfully refreshed, proceed to fetch transactions
            # Define the Finicity API endpoint for fetching transactions
            endpoint = f"https://api.finicity.com/aggregation/v3/customers/{customer_id}/transactions"

            # Define query parameters with default values
            fromDate_epoch = int(request.args.get('fromDate', default=1681529565))  # Default: 6 months ago
            toDate_epoch = int(request.args.get('toDate', default=1697254365))  # Default: yesterday
            includePending = request.args.get('includePending', default='false')
            sort = request.args.get('sort', default='desc')
            limit = request.args.get('limit', default=1000)  # Set your default limit value here

            # Define query parameters for the request
            params = {
                "fromDate": fromDate_epoch,
                "toDate": toDate_epoch,
                "includePending": includePending,
                "sort": sort,
                "limit": limit
            }

            # Make the GET request to fetch transactions
            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code == 200:
                transactions = parse_xml_transactions(response.text)
                return jsonify({"transactions": transactions})
            else:
                # Capture and print the response content for debugging
                error_message = response.text
                print(f"Failed to fetch transactions. Response content: {error_message}")

                return jsonify({"error": "Failed to fetch transactions"}), response.status_code
            

#######

def categorize_payee(payee_name):
    openai.key = OPENAI_KEY
    response = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo",
    messages = [
        {"role": "system", "content": "I am the world's most intelligent categorizer. Given the name of"},
        {"role": "user", "content": "Convert this following string into latex, with the mathematical portions of this string correctly converted into the proper mathematical formatting in LaTeX. Do not output anything other than the LaTeX code in a code window. I want the resulting LaTeX code as flawless as possible, so that I can copy and paste it into a section of an existing LaTeX code body and it will compile without problems while maintaining the perfect formatting. {}".format(answer)}
        ]
    )
    return response['choices'][0]['message']['content']
    
            
@app.route('/recommend_vendors/<customer_id>', methods=['GET'])
def recommend_vendors(customer_id):
    # Fetch the customer's transactions
    transactions_response = fetch_transactions(customer_id)

    if transactions_response.status_code == 200:
        transactions_data = transactions_response.json().get("transactions", [])

        # Analyze transactions and calculate category weights
        category_weights = {}
        category_vendors = {
            "Category1": ["Vendor1", "Vendor2", "Vendor3"],
            "Category2": ["Vendor4", "Vendor5", "Vendor6"],
            # Add more categories and vendors as needed
        }

        for transaction in transactions_data:
            normalized_payee_name = transaction.get("normalizedPayeeName")
            amount = transaction.get("amount")
            category = categorize_payee(normalized_payee_name)  # Implement your categorization logic

            if category:
                # Update the category weight
                if category in category_weights:
                    category_weights[category] += amount
                else:
                    category_weights[category] = amount

        # Sort categories by weight in descending order
        sorted_categories = sorted(category_weights.items(), key=lambda x: x[1], reverse=True)

        # Recommend vendors based on category weights
        recommended_vendors = []
        for category, _ in sorted_categories:
            if category in category_vendors:
                recommended_vendors.extend(category_vendors[category])

        # Return the list of recommended vendors as JSON
        return jsonify({"recommended_vendors": recommended_vendors})

    else:
        return jsonify({"error": "Failed to fetch transactions"}), transactions_response.status_code
            

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