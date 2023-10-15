from flask import Flask, render_template, redirect, jsonify, request, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash # new
import os
import json
import time
import requests
import sys
import xml.etree.ElementTree as ET
from supabase import create_client
import openai
from dotenv import load_dotenv
from functools import lru_cache
import logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib


app = Flask(__name__)
app.secret_key = 'secret_string'.encode('utf8')


# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.DEBUG)

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


@app.route('/create_acct', methods=['POST'])
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
    # but we need username to login?

    password = request.form['password']
    # salts and hashes plain text password
    hashed_password = generate_password_hash(password)


    # Customer data to be sent in the request
    customer_data = {
        "username": username,                      # Use the generated unique username
        "firstName": request.form['firstName'],    # Get first name from the form
        "lastName": request.form['lastName'],      # Get last name from the form
        "phone": request.form['phone'],            # Get phone from the form
        "email": request.form['email'],            # Get email from the form
    }
    print(customer_data)

    # salts and hashes plaintext password
    # hashed_password = generate_password_hash(customer_data.password)
    # customer_data["hashed_password"] = hashed_password # adds to customer_data object

    # implement temporary user ids now
    # example_temp_id = 123456789
    # customer_data["temp_user_id"] = example_temp_id # adds to customer_data object

    # insert data into database
    data = supabase.table("user_info").insert({"first_name":customer_data['firstName'], "last_name":customer_data['lastName'],\
                                               "username":customer_data['username'], "phone_number":customer_data['phone'], "email":customer_data['email'],\
                                                "hashed_password":hashed_password}).execute()
    ## to view 'user_info' database
    # data = supabase.table("user_info").select("*").execute()

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

                session['user_id'] = customer_id # can access session vars on any page 
                session['full_name'] = customer_data['firstName'] + ' ' + customer_data['lastName']
                session['username'] = customer_data['username']
                return render_template('target_page.html', user_id=session['user_id'], username=session['username'], full_name=session['full_name']) # return with session id

                # return f"Testing customer created. Customer ID: {customer_id}", 201
            else:
                return f"Error: Missing 'id' element in the XML response. Status code: {response.status_code}", 500
        except ET.ParseError:
            # Handle the case where the response is not valid XML
            return f"Error: Invalid XML response from the API. Status code: {response.status_code}", 500
    else:
        # Handle the error case
        return f"Error creating testing customer. Status code: {response.status_code}", 500
        

@app.route('/show_create_customer_form', methods=['GET'])
def show_create_customer_form():
    return render_template('create_customer.html')

@app.route('/login', methods=['GET'])
def show_login():
    return render_template('login.html')
    
@app.route('/check_login', methods=['POST', 'GET'])
def check_login():
    username = request.form['username_input']
    password_guess = request.form['password_input']

    # find password corresponding to given username
    returned_password = supabase.table("user_info").select("hashed_password").eq("username", f"{username}").execute()
    as_list = list(returned_password)
    db_password = as_list[0][1][0]['hashed_password']

    if check_password_hash(db_password, password_guess):
        #get first name
        returned_firstname = supabase.table("user_info").select("first_name").eq("username", f"{username}").execute()
        as_list = list(returned_firstname)
        first_name = as_list[0][1][0]['first_name']

        #get last name
        returned_lastname = supabase.table("user_info").select("last_name").eq("username", f"{username}").execute()
        as_list = list(returned_lastname)
        last_name = as_list[0][1][0]['last_name']

        user_id = 7006562263 ## !! ASSIGN USER ID TO SESSION VARIABLE !!
        session['username'] = username
        session['user_id'] = user_id
        session['full_name'] = first_name + ' ' + last_name
        
        print('\nLogin Successful\n')
        return render_template('target_page.html', user_id=session['user_id'], username=session['username'], full_name=session['full_name'])
    else: ## error occurs because indexing sql query returns out of bounds... fix needed
        print("\nPassword or username incorrect. Try again\n")
        return render_template('index.html')
        

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect_to_connect_to_bank', methods=['POST', 'GET'])
def connect_to_connect_to_bank():
    user_id = session['user_id']
    return redirect(url_for('connect_to_bank', customer_id=user_id))

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

@app.route('/connect_to_fetch_transactions', methods=['POST', 'GET'])
def connect():
    customer_id = session['user_id']
    return redirect(url_for('fetch_transactions', customer_id=customer_id))

@app.route('/connect_to_recommendations', methods=['POST', 'GET'])
def connect_to_recommendations():
    customer_id = session['user_id']
    return redirect(url_for('recommend_vendors', customer_id=customer_id))

def _fetch_transactions(customer_id): # HELPER METHOD
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

            print(f"API Response Status: {response.status_code}")
            print(f"API Response Content: {response.text}")

            # here
            if response.status_code == 200:
                # testing...
                # print('response text:', response.text, file=sys.stderr)
                
                transactions = parse_xml_transactions(response.text) # returns a list of dictionaries
                # print(type(transactions[0]))
                # print(transactions[1]['normalizedPayeeName'])

                # df = pd.DataFrame(transactions) # doesnt work
                session['transaction'] = transactions # scary hours
            
                return transactions
            else:
                # Capture and print the response content for debugging
                error_message = response.text
                print(f"Failed to fetch transactions. Response content: {error_message}")

                return jsonify({"error": "Failed to fetch transactions"}), response.status_code

@app.route('/fetch_transactions/<customer_id>', methods=['GET'])
def fetch_transactions(customer_id):
    transactions = _fetch_transactions(customer_id)
    return jsonify(transactions)

openai.api_key = OPENAI_KEY

@lru_cache(maxsize=100)
def categorize_vendors(vendors):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": ("I am the world's most intelligent categorizer. Given a set of the names "
                            "of payees, I can put every payee into one of ten categories. I will come "
                            "up with those ten categories for every set of payees I am given.")
            },
            {
                "role": "user",
                "content": f"I am giving you a set of payees. I want you to create 10 categories that these payees "
                           f"can be put into, and then give me back a list of those categories in this format "
                           f"(ignoring the pointy brackets): <[category_1, category_2, ... , category_10]>. Do not "
                           f"output anything other than the list of categories in a code window. Here is the set of "
                           f"payees: {set(vendors)}"
            }
        ]
    )

    if response and response.get('choices'):
        return response['choices'][0]['message']['content']
    else:
        return "Error: Invalid response from OpenAI"

@lru_cache(maxsize=100)
def categories_to_vendors(categories):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": ("I am the world's most intelligent vendor recommender. Given a list of categories, I can "
                            "recommend the best vendors that fit in these categories (e.g. if a category is Luxury "
                            "Clothing, I might recommend Louis Vuitton).")
            },
            {
                "role": "user",
                "content": f"I am giving you a list of categories. I want you to recommend one vendor/brand/store for "
                           f"each category, and then give me back a list of those vendors/brands/stores in this format "
                           f"(ignoring the pointy brackets): <[vendor_1, vendor_2, ... , vendor_10]>. Do not output "
                           f"anything other than the list of vendors in a code window. Here is the list of categories: "
                           f"{categories}"
            }
        ]
    )

    if response and response.get('choices'):
        return response['choices'][0]['message']['content']
    else:
        return "Error: Invalid response from OpenAI"

    
@app.route('/recommend_vendors/<customer_id>', methods=['GET'])
def recommend_vendors(customer_id):
    # Fetch the customer's transactions
    transactions = _fetch_transactions(customer_id)

    # Extract vendors from the transactions
    vendors = tuple({transaction.get("normalizedPayeeName") for transaction in transactions})

    # Categorize vendors using OpenAI
    categories = categorize_vendors(vendors)

    # Get recommended vendors based on the categories
    recommended_vendors = categories_to_vendors(categories)

    # Extract list from the string
    recommended_vendors_list = recommended_vendors.strip("<>").split(",")
    recommended_vendors_list = [vendor.strip().strip('"').strip('[').strip(']') for vendor in recommended_vendors_list]  
    return jsonify({"recommended_vendors": recommended_vendors_list})
            

@app.route('/dashboard', methods=['POST', 'GET'])
def load_dashboard():
    data = session['transaction']
    df = pd.DataFrame(columns=['Vendor', 'Amount'])
    for transaction in data:
        df.loc[len(df.index)] = [transaction['amount'], transaction['normalizedPayeeName']]

    # print(df)
    # print(df.shape) # 111, 2
    # print(df.columns) # Index(['Vendor', 'Amount'], dtype='object')
    # print(df['Amount'].value_counts(sort=False)) # good
    # print(df['Amount'].value_counts(sort=False)[0])
    # print(df['Amount'].unique())

    data_to_plot = pd.DataFrame([df['Amount'].value_counts(sort=False), df['Amount'].unique()])


    matplotlib.use('agg')
    fig = plt.figure(figsize=(20,20))
    # ''''''
    plt.subplot(221)
    plt.tight_layout()
    counts = df['Amount'].value_counts()
    ax = counts.iloc[:10].plot(kind="barh")
    ax.invert_yaxis()
    plt.title('Frequency of Vendors')
    plt.ylabel("Most common vendors")
    plt.xlabel("Frequency")
    # return plt.show()'''

    plt.subplot(222)
    plt.tight_layout()
    # labels_ = [[1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]]
    sorted_ = df.sort_values(by='Vendor', ascending=False, key=lambda col: col.astype(float).abs())
    print(sorted_)
    # plt.bar(labels_, sorted_.iloc[:10])
    ax=sorted_.iloc[:10].plot(kind="bar")
    plt.title("Largest transactions")
    plt.xlabel('Vendors')
    plt.ylabel('Amount (USD)')

    
    plt.savefig('static/vendor_freq.png')
    
    

    return render_template('plot.html')


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
    app.run(debug=True, threaded=True)