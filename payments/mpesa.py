import requests
import json
import base64
from datetime import datetime
from django.conf import settings

class MpesaClient:
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.access_token_url = settings.MPESA_ACCESS_TOKEN_URL
        self.stk_push_url = settings.MPESA_EXPRESS_URL
        self.callback_url = settings.MPESA_CALLBACK_URL
        self.transaction_type = settings.MPESA_TRANSACTION_TYPE

    def get_access_token(self):
        """
        Authenticates with Safaricom and returns an Access Token.
        """
        try:
            response = requests.get(
                self.access_token_url, 
                auth=(self.consumer_key, self.consumer_secret)
            )
            response.raise_for_status() # Raise error for 400/500 codes
            json_response = response.json()
            return json_response['access_token']
        except Exception as e:
            print(f"Error generating Access Token: {str(e)}")
            return None

    def stk_push(self, phone_number, amount, account_reference="BuyCars Subscription"):
        """
        Trigger the M-PESA pin prompt on the user's phone.
        """
        access_token = self.get_access_token()
        if not access_token:
            return {"error": "Failed to authenticate with M-PESA"}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Generate the Password
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode('utf-8')

        # --- FIX: ROBUST PHONE NUMBER SANITIZATION ---
        # 1. Convert to string and strip spaces/dashes/plus signs
        phone_number = str(phone_number).strip().replace(" ", "").replace("-", "").replace("+", "")

        # 2. Convert 07... or 01... to 2547...
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        
        # 3. Ensure it is exactly 12 digits
        if not phone_number.isdigit() or len(phone_number) != 12:
            return {"error": f"Invalid phone format: {phone_number}. Use 0712345678."}
        # ---------------------------------------------

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": self.transaction_type, # Uses settings.py config
            "Amount": int(amount), 
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": f"Payment for {account_reference}"
        }

        try:
            response = requests.post(self.stk_push_url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            print(f"STK Push Error: {str(e)}")
            return {"error": str(e)}