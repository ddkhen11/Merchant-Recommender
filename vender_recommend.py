import openai
import os
from main import fetch_transactions
from flask import jsonify

OPENAI_KEY = os.environ.get("OPENAI_KEY")

def categorize_vendors(vendors):
    openai.key = OPENAI_KEY
    response = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo",
    messages = [
        {"role": "system", "content": "I am the world's most intelligent categorizer. Given a set of the names of payees, I can put every payee into one of ten categories. I will come up with those ten categories for every set of payees I am given."},
        {"role": "user", "content": "I am giving you a set of payees. I want you to create 10 categories that these payees can be put into, and then give me back a list of those categories in this format (ignoring the pointy brackets): <[category_1, category_2, ... , category_10]>. Do not output anything other than the list of categories in a code window. Here is the set of payees: {}".format(vendors)}
        ]
    )
    return response['choices'][0]['message']['content']

def categories_to_vendors(categories):
    openai.key = OPENAI_KEY
    response = openai.ChatCompletion.create(
    model = "gpt-3.5-turbo",
    messages = [
        {"role": "system", "content": "I am the world's most intelligent vendor recommender. Given a list of categories, I can recommend the best vendors that fit in these categories (e.g. if a category is Luxury Clothing, I might recommend Louis Vuitton)."},
        {"role": "user", "content": "I am giving you a list of categories. I want you to recommend one vendor/brand/store for each category, and then give me back a list of those vendors/brands/stores in this format (ignoring the pointy brackets): <[vendor_1, vendor_2, ... , vendor_10]>. Do not output anything other than the list of vendors in a code window. Here is the list of categories: {}".format(categories)}
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
        vendors = set()

        for i in len(transactions_data):
            vendor = transactions_data["transactions"][i].get("normalizedPayeeName")
            vendors.add(vendor)

        categories = categorize_vendors(vendors)
        print(categories)

        recommended_vendors = categories_to_vendors(categories)
        print(recommended_vendors)

        # Return the list of recommended vendors as JSON

        return jsonify({"recommended_vendors": recommended_vendors})

    else:
        return jsonify({"error": "Failed to fetch transactions"}), transactions_response.status_code