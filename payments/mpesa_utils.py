import requests
import base64
from datetime import datetime
from django.conf import settings
from requests.auth import HTTPBasicAuth

def get_access_token():
    """
    Authenticates with Safaricom to get a temporary access token.
    """
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_URL = settings.MPESA_ACCESS_TOKEN_URL

    try:
        r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        r.raise_for_status() # Raise error for bad status codes
        json_response = r.json()
        return json_response['access_token']
    except Exception as e:
        print(f"Error getting Access Token: {e}")
        return None

def generate_password(formatted_time):
    """
    Generates the base64 encoded password required for STK Push.
    Formula: Base64(BusinessShortCode + Passkey + Timestamp)
    
    NOTE: For Till Numbers, BusinessShortCode here MUST be the STORE NUMBER (Head Office),
    not the Till Number itself.
    """
    data_to_encode = settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + formatted_time
    encoded_string = base64.b64encode(data_to_encode.encode())
    return encoded_string.decode('utf-8')

def initiate_stk_push(phone_number, amount, account_reference, transaction_desc):
    """
    Triggers the M-Pesa prompt on the user's phone.
    Supports both Paybill and Buy Goods (Till Number) modes.
    """
    access_token = get_access_token()
    if not access_token:
        return {"error": "Failed to get access token"}

    # 1. Generate Timestamp & Password
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = generate_password(timestamp)
    
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }

    # 2. Sanitize Phone Number (Must be 254...)
    phone_number = str(phone_number).strip().replace(" ", "").replace("-", "").replace("+", "")
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif phone_number.startswith('+254'):
        phone_number = phone_number[1:]

    # 3. Determine PartyB (Destination)
    # If using a Till Number, PartyB is the Till Number.
    # If using Paybill, PartyB is the Shortcode.
    party_b = getattr(settings, 'MPESA_TILL_NUMBER', settings.MPESA_SHORTCODE)
    
    # 4. Determine Transaction Type
    # Default to PayBill if not specified, but settings should have 'CustomerBuyGoodsOnline' for Tills
    transaction_type = getattr(settings, 'MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline')

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE, # Always the Store Number / Head Office
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": transaction_type, 
        "Amount": int(amount),
        "PartyA": phone_number,             # Phone sending money
        "PartyB": party_b,                  # Till Number (Where money goes)
        "PhoneNumber": phone_number,        # Phone receiving the PIN prompt
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }

    try:
        response = requests.post(settings.MPESA_EXPRESS_URL, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}