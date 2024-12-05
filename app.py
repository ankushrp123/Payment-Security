from flask import Flask, request, jsonify, render_template
from cryptography.fernet import Fernet
import uuid
def luhn_check(card_number):
    card_number = card_number[::-1]  # Reverse the card number
    total = 0

    for i, digit in enumerate(card_number):
        n = int(digit)
        if i % 2 == 1:  # Double every second digit
            n *= 2
            if n > 9:  # If the result is greater than 9, subtract 9
                n -= 9
        total += n

    return total % 10 == 0  # Valid if total modulo 10 is 0
from datetime import datetime

def validate_expiry_date(expiry_date):
    try:
        exp_month, exp_year = map(int, expiry_date.split("/"))
        exp_year += 2000  # Convert to full year (e.g., 24 -> 2024)
        expiry = datetime(exp_year, exp_month, 1)
        return expiry > datetime.now()
    except ValueError:
        return False
    
def get_card_type(card_number):
    if card_number.startswith("4"):
        return "Visa"
    elif card_number.startswith(("51", "52", "53", "54", "55")) or card_number.startswith(tuple(map(str, range(2221, 2721)))):
        return "MasterCard"
    elif card_number.startswith(("34", "37")):
        return "American Express"
    else:
        return "Unknown"
app = Flask(__name__)

# Generate encryption key (store securely in production)
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

@app.route("/")
def index():
    return render_template("payment_form.html")  # Ensure the form file is named 'payment_form.html'

@app.route("/process-payment", methods=["POST"])
def process_payment():
    card_number = request.form.get("cardNumber")
    expiry_date = request.form.get("expiryDate")
    cvv = request.form.get("cvv")

    # Validate card number (Luhn algorithm)
    if not luhn_check(card_number):
        return jsonify({"error": "Invalid card number"}), 400

    # Validate expiry date
    if not validate_expiry_date(expiry_date):
        return jsonify({"error": "Invalid expiry date"}), 400

    # Identify card type
    card_type = get_card_type(card_number)

    # Encrypt the card number
    encrypted_card_number = cipher_suite.encrypt(card_number.encode())

    # Generate a token
    token = str(uuid.uuid4())

    return jsonify({
        "message": "Payment processed successfully!",
        "cardType": card_type,
        "encryptedCardNumber": encrypted_card_number.decode(),
        "token": token
    })

if __name__ == "__main__":
    app.run(debug=True, ssl_context="adhoc")  # Use an SSL certificate in production
