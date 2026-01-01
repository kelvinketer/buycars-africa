import requests
import json
import base64
from datetime import datetime
from django.conf import settings
from requests.auth import HTTPBasicAuth

class MpesaClient:
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.access_token_url = settings.MPESA_ACCESS_TOKEN_URL
        self.stk_push_url = settings.MPESA_EXPRESS_URL
        self.callback_url = settings.MPESA_CALLBACK_URL
        self.transaction_type = settings.MPESA_TRANSACTION_TYPE
        
        # --- CRITICAL UPDATE: SEPARATING STORE VS TILL ---
        # 1. Store Number (Identity): Used for Password generation
        self.shortcode = settings.MPESA_SHORTCODE 
        
        # 2. Till Number (Wallet): Where the money actually goes
        self.till_number = settings.MPESA_TILL_NUMBER 
        
        self.passkey = settings.MPESA_PASSKEY

    def get_access_token(self):
        """
        Authenticates with Safaricom and returns an Access Token.
        """
        try:
            response = requests.get(
                self.access_token_url, 
                auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret)
            )
            response.raise_for_status()
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
        
        # --- PASSWORD GENERATION ---
        # ALWAYS use the Store Number (Shortcode) for the password, NOT the Till Number.
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode('utf-8')

        # --- PHONE NUMBER SANITIZATION ---
        phone_number = str(phone_number).strip().replace(" ", "").replace("-", "").replace("+", "")
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        
        if not phone_number.isdigit() or len(phone_number) != 12:
            return {"error": f"Invalid phone format: {phone_number}. Use 0712345678."}

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # --- PAYLOAD ---
        payload = {
            "BusinessShortCode": self.shortcode,      # Authenticates as Store Owner
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": self.transaction_type, # 'CustomerBuyGoodsOnline'
            "Amount": int(amount), 
            "PartyA": phone_number,                   # Customer Phone
            
            # --- THE FIX: MONEY GOES TO TILL NUMBER ---
            "PartyB": self.till_number,               # Destination Wallet
            # ------------------------------------------
            
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": f"Payment for {account_reference}"
        }

        try:
            response = requests.post(self.stk_push_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"STK Push Error: {e}")
            if e.response:
                print(f"Response: {e.response.text}") # Helpful for debugging
            return {"error": str(e)}