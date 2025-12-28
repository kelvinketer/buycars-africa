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
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount), 
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": f"Payment for {account_reference}"
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {"error": str(e)}