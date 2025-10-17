# Facebook Messenger Chatbot with OpenAI Integration
# This file contains the backend logic for the chatbot
# TODO: Install required packages:
# pip install flask requests openai python-dotenv

from flask import Flask, request, jsonify
import requests
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Environment variables for API keys
FACEBOOK_VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN')
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Global variable to store product info
product_info = ""


def load_product_info():
    """
    Load product information from docs/info.md file.
    This function reads the markdown file containing product details
    that will be used as context for the chatbot responses.
    """
    global product_info
    # TODO: Add logic to read the docs/info.md file
    # Example implementation:
    # try:
    #     with open('../docs/info.md', 'r', encoding='utf-8') as file:
    #         product_info = file.read()
    # except FileNotFoundError:
    #     print("Error: docs/info.md file not found")
    #     product_info = "Product information not available."
    pass


def send_message_to_facebook(recipient_id, message_text):
    """
    Send a message back to Facebook Messenger.
    
    Args:
        recipient_id (str): The recipient's Facebook ID
        message_text (str): The message text to send
    
    Returns:
        dict: Response from Facebook API
    """
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={FACEBOOK_PAGE_ACCESS_TOKEN}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()


def generate_openai_response(user_message, product_context):
    """
    Generate a response using OpenAI's API.
    
    Args:
        user_message (str): The user's message
        product_context (str): Product information context from docs/info.md
    
    Returns:
        str: Generated response from OpenAI
    """
    try:
        # Create a prompt that includes product context
        system_prompt = f"""You are a helpful customer service assistant for a cushion cover business.
        Use the following product information to answer customer questions:
        
        {product_context}
        
        Be friendly, professional, and provide accurate information based on the product details above."""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating OpenAI response: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again later."


@app.route('/', methods=['GET'])
def home():
    """Home endpoint to verify the server is running."""
    return "Facebook Messenger Chatbot is running!"


@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Webhook verification endpoint for Facebook.
    Facebook will send a GET request to verify the webhook.
    """
    # Parse params from the webhook verification request
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == 'subscribe' and token == FACEBOOK_VERIFY_TOKEN:
            # Respond with 200 OK and challenge token from the request
            print('Webhook verified successfully!')
            return challenge, 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            return 'Forbidden', 403
    
    return 'Bad Request', 400


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle incoming messages from Facebook Messenger.
    This endpoint receives POST requests when users send messages.
    """
    data = request.get_json()
    
    # Check if this is a page subscription
    if data.get('object') == 'page':
        # Iterate over each entry (there may be multiple if batched)
        for entry in data.get('entry', []):
            # Get the messaging events
            for messaging_event in entry.get('messaging', []):
                sender_id = messaging_event['sender']['id']
                
                # Check if this is a message event
                if messaging_event.get('message'):
                    # Extract the message text
                    message_text = messaging_event['message'].get('text', '')
                    
                    if message_text:
                        print(f"Received message from {sender_id}: {message_text}")
                        
                        # Load product info if not already loaded
                        if not product_info:
                            load_product_info()
                        
                        # Generate response using OpenAI
                        ai_response = generate_openai_response(message_text, product_info)
                        
                        # Send the response back to Facebook Messenger
                        send_message_to_facebook(sender_id, ai_response)
        
        # Return 200 OK to acknowledge receipt
        return 'OK', 200
    
    # Return 404 Not Found if the event is not from a page subscription
    return 'Not Found', 404


if __name__ == '__main__':
    # Load product information on startup
    load_product_info()
    
    # Run the Flask app
    app.run(debug=True, port=5000)
