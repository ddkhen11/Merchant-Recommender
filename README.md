# Merchant Recommender

## Overview

Merchant Recommender is a web application that integrates with the Open Banking API from Mastercard, allowing users to securely log into their bank accounts and retrieve their transaction histories. The highlight of our project is the utilization of the OpenAI API, which analyzes users' transaction histories to provide an AI-tailored list of recommended vendors. The program also offers a dashboard feature that presents a summary of users' transactions based on the vendors they've frequented and the number of times they've shopped there.

## Features

- **Open Banking Integration:** Connect securely to your bank account using the Open Banking API from Mastercard.
  
- **AI-Tailored Vendor Recommendations:** Get personalized vendor recommendations based on your transaction history, powered by OpenAI.

- **Interactive Dashboard:** Gain insights into your spending habits with a dashboard that showcases your transaction history, highlighting vendors you've shopped with and the frequency of your visits.

## Getting Started

### Prerequisites

- Python 3.x
- An active account with Mastercard's Open Banking API and OpenAI (for API keys).

### Installation

1. Clone the repository.
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the main application:
   ```
   python main.py
   ```

## Usage

1. Navigate to the login page and login with your credentials. Create an account if you don't have one yet.
2. Once your logged in, ensure that the first thing you do is connect your bank account.
3. Explore your transaction history and get AI-powered vendor recommendations.
4. Check out the dashboard for an overview of your transactions.

## Contributing

If you'd like to contribute to Merchant Recommender, please fork the repository and submit a pull request. We appreciate all contributions!
