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

        print(categorize_vendors(vendors))


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