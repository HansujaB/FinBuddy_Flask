from flask import Flask, request, jsonify
import requests
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# WhatsApp API Configuration
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

class ExpenseCategorizer:
    """Rule-based expense categorizer using keyword matching"""
    
    def __init__(self):
        self.categories = {
            '🍔 Food': [
                'food', 'restaurant', 'cafe', 'coffee', 'lunch', 'dinner', 'breakfast',
                'pizza', 'burger', 'sandwich', 'meal', 'eat', 'hungry', 'kitchen',
                'zomato', 'swiggy', 'dominos', 'mcdonalds', 'kfc', 'subway', 'starbucks',
                'delivery', 'takeaway', 'dine', 'buffet', 'snack', 'grocery store',
                'supermarket', 'vegetables', 'fruits', 'milk', 'bread'
            ],
            '🛒 Shopping': [
                'shopping', 'amazon', 'flipkart', 'myntra', 'clothes', 'shirt', 'shoes',
                'buy', 'purchase', 'order', 'mall', 'store', 'shop', 'retail',
                'electronics', 'mobile', 'laptop', 'headphones', 'gadget',
                'cosmetics', 'makeup', 'perfume', 'jewelry', 'watch', 'bag',
                'online', 'ecommerce', 'delivery', 'cart', 'checkout'
            ],
            '🚕 Transport': [
                'uber', 'ola', 'taxi', 'cab', 'auto', 'rickshaw', 'bus', 'metro',
                'train', 'flight', 'travel', 'transport', 'commute', 'ride',
                'petrol', 'diesel', 'fuel', 'gas', 'parking', 'toll',
                'vehicle', 'car', 'bike', 'scooter', 'maintenance', 'service'
            ],
            '💡 Bills': [
                'electricity', 'water', 'gas', 'internet', 'wifi', 'mobile bill',
                'phone bill', 'utility', 'bill', 'payment', 'recharge',
                'broadband', 'cable', 'tv', 'netflix', 'spotify', 'subscription',
                'insurance', 'premium', 'emi', 'loan', 'credit card'
            ],
            '🏠 Rent': [
                'rent', 'house', 'apartment', 'flat', 'home', 'accommodation',
                'landlord', 'deposit', 'maintenance', 'society', 'housing'
            ],
            '✈️ Travel': [
                'vacation', 'trip', 'holiday', 'hotel', 'resort', 'booking',
                'airbnb', 'flight', 'ticket', 'visa', 'passport', 'tour',
                'sightseeing', 'tourism', 'adventure', 'beach', 'mountain'
            ],
            '📚 Books': [
                'book', 'kindle', 'novel', 'magazine', 'newspaper', 'education',
                'course', 'learning', 'study', 'library', 'bookstore',
                'stationery', 'pen', 'notebook', 'academic'
            ],
            '🏥 Healthcare': [
                'doctor', 'hospital', 'medicine', 'pharmacy', 'medical',
                'health', 'checkup', 'treatment', 'clinic', 'dentist',
                'prescription', 'vitamins', 'supplements'
            ],
            '🎮 Entertainment': [
                'movie', 'cinema', 'theater', 'game', 'gaming', 'concert',
                'party', 'club', 'bar', 'pub', 'entertainment', 'fun',
                'sports', 'gym', 'fitness', 'membership'
            ]
        }
    
    def extract_amount(self, text):
        """Extract amount from text using regex"""
        # Look for patterns like: 250, ₹250, Rs 250, Rs. 250, $250, 250/-
        amount_patterns = [
            r'₹\s?(\d+(?:\.\d{2})?)',  # ₹250 or ₹ 250
            r'rs\.?\s?(\d+(?:\.\d{2})?)',  # Rs 250 or Rs. 250
            r'\$\s?(\d+(?:\.\d{2})?)',  # $250
            r'(\d+)\s?/-',  # 250/-
            r'(\d+(?:\.\d{2})?)\s?rupees?',  # 250 rupees
            r'(\d+(?:\.\d{2})?)\s?dollars?',  # 250 dollars
            r'(?:spent|paid|cost|worth)\s+(\d+(?:\.\d{2})?)',  # spent 250
            r'(\d+(?:\.\d{2})?)'  # Just numbers (fallback)
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))
        
        return None
    
    def categorize(self, text):
        """Categorize expense based on keywords"""
        text_lower = text.lower()
        
        # Extract amount
        amount = self.extract_amount(text)
        
        # Score each category
        category_scores = {}
        
        for category, keywords in self.categories.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight based on keyword specificity
                    if len(keyword) > 5:  # Longer keywords get higher weight
                        score += 2
                    else:
                        score += 1
            category_scores[category] = score
        
        # Find best category
        best_category = max(category_scores, key=category_scores.get)
        
        # If no keywords match, classify as Others
        if category_scores[best_category] == 0:
            best_category = '📝 Others'
        
        return {
            'category': best_category,
            'amount': amount,
            'confidence': category_scores.get(best_category, 0)
        }

# Initialize categorizer
categorizer = ExpenseCategorizer()

def send_whatsapp_message(to_number, message):
    """Send message via WhatsApp Cloud API"""
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'messaging_product': 'whatsapp',
        'to': to_number,
        'type': 'text',
        'text': {'body': message}
    }
    
    response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
    return response.json()

def format_expense_response(result, original_text):
    """Format the categorized expense response"""
    category = result['category']
    amount = result['amount']
    
    if amount:
        response = f"💰 **Expense Categorized!**\n\n"
        response += f"📊 **Category:** {category}\n"
        response += f"💵 **Amount:** ₹{amount}\n"
        response += f"📝 **Description:** {original_text}\n\n"
        response += f"✅ Your expense has been recorded!"
    else:
        response = f"🤔 **Expense Detected**\n\n"
        response += f"📊 **Category:** {category}\n"
        response += f"📝 **Description:** {original_text}\n\n"
        response += f"ℹ️ Tip: Include amount like '₹250' for better tracking!"
    
    return response

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verify webhook for WhatsApp"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("Webhook verified successfully!")
            return challenge
        else:
            return "Forbidden", 403
    return "Bad Request", 400

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle incoming WhatsApp messages"""
    try:
        data = request.get_json()
        
        if data.get('object') == 'whatsapp_business_account':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        messages = change.get('value', {}).get('messages', [])
                        
                        for message in messages:
                            # Extract message details
                            from_number = message.get('from')
                            message_type = message.get('type')
                            
                            if message_type == 'text':
                                text_body = message.get('text', {}).get('body', '')
                                
                                print(f"Received message from {from_number}: {text_body}")
                                
                                # Categorize the expense
                                result = categorizer.categorize(text_body)
                                
                                # Format response
                                response_message = format_expense_response(result, text_body)
                                
                                # Send response back to user
                                send_response = send_whatsapp_message(from_number, response_message)
                                print(f"Sent response: {send_response}")
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "WhatsApp Expense Bot"}), 200

@app.route('/test', methods=['POST'])
def test_categorizer():
    """Test endpoint for categorizer"""
    data = request.get_json()
    text = data.get('text', '')
    
    if text:
        result = categorizer.categorize(text)
        return jsonify(result), 200
    else:
        return jsonify({"error": "No text provided"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)