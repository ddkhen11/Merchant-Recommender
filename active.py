@app.route('/get_customer/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    # Fetch the Finicity-App-Token
    APP_TOKEN = fetch_app_token()

    # Headers for the GET request
    headers = {
        "Content-Type": "application/json",
        "Finicity-App-Token": APP_TOKEN,
        "Finicity-App-Key": APP_KEY
    }

    # Define the Finicity API endpoint for retrieving a customer by ID
    CUSTOMER_ENDPOINT = f"https://api.finicity.com/aggregation/v1/customers/{customer_id}"

    # Make the GET request to retrieve the customer
    response = requests.get(CUSTOMER_ENDPOINT, headers=headers)

    if response.status_code == 200:
        customer_data = response.json()
        return jsonify(customer_data)
    else:
        return jsonify({"error": "Failed to retrieve customer"}), response.status_code
    


@app.route('/modify_customer/<customer_id>', methods=['PUT'])
def modify_customer(customer_id):
    # Fetch the Finicity-App-Token
    APP_TOKEN = fetch_app_token()

    # Headers for the PUT request
    headers = {
        "Content-Type": "application/json",
        "Finicity-App-Token": APP_TOKEN,
        "Finicity-App-Key": APP_KEY
    }

    # Extract firstName and lastName from the JSON request body
    data = request.json
    first_name = data.get('firstName')
    last_name = data.get('lastName')

    if not first_name and not last_name:
        return jsonify({"error": "You must specify either firstName, lastName, or both"}), 400

    # Create a dictionary with the fields to be updated
    update_data = {}
    if first_name:
        update_data["firstName"] = first_name
    if last_name:
        update_data["lastName"] = last_name

    # Define the Finicity API endpoint for modifying a customer by ID
    CUSTOMER_ENDPOINT = f"https://api.finicity.com/aggregation/v1/customers/{customer_id}"

    # Make the PUT request to modify the customer
    response = requests.put(CUSTOMER_ENDPOINT, headers=headers, json=update_data)

    if response.status_code == 204:
        return "", 204  # Empty response with HTTP status 204 for success
    else:
        return jsonify({"error": "Failed to modify customer"}), response.status_code
    

@app.route('/delete_customer/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    # Fetch the Finicity-App-Token
    APP_TOKEN = fetch_app_token()

    # Headers for the DELETE request
    headers = {
        "Content-Type": "application/json",
        "Finicity-App-Token": APP_TOKEN,
        "Finicity-App-Key": APP_KEY
    }

    # Define the Finicity API endpoint for deleting a customer by ID
    CUSTOMER_ENDPOINT = f"https://api.finicity.com/aggregation/v1/customers/{customer_id}"

    # Make the DELETE request to delete the customer
    response = requests.delete(CUSTOMER_ENDPOINT, headers=headers)

    if response.status_code == 204:
        return "", 204  # Empty response with HTTP status 204 for success
    else:
        return jsonify({"error": "Failed to delete customer"}), response.status_code

@app.route('/get_customers', methods=['GET'])
def get_customers():
    # Fetch the Finicity-App-Token
    APP_TOKEN = fetch_app_token()

    # Parse query parameters from the request URL
    username = request.args.get('username')
    customer_type = request.args.get('type')
    search_text = request.args.get('search')
    start = request.args.get('start', '1')
    limit = request.args.get('limit', '10')

    # Headers for the GET request
    headers = {
        "Content-Type": "application/json",
        "Finicity-App-Token": APP_TOKEN,
        "Finicity-App-Key": APP_KEY
    }

    # Define the Finicity API endpoint for getting customers
    CUSTOMERS_ENDPOINT = "https://api.finicity.com/aggregation/v1/customers"

    # Define query parameters for the request
    params = {
        "username": username,
        "type": customer_type,
        "search": search_text,
        "start": start,
        "limit": limit
    }

    # Make the GET request to get customers
    response = requests.get(CUSTOMERS_ENDPOINT, headers=headers, params=params)

    if response.status_code == 200:
        customers_data = response.json()
        return jsonify(customers_data)
    else:
        return jsonify({"error": "Failed to fetch customers"}), response.status_code