import requests
import json
import base64
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from requests.auth import HTTPBasicAuth

from .models import MpesaTransaction
from users.models import DealerProfile

# --- HELPER: GENERATE ACCESS TOKEN ---
def get_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_URL = settings.MPESA_ACCESS_TOKEN_URL

    try:
        r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        r.raise_for_status() # Raise error if failed
        return r.json()['access_token']
    except Exception as e:
        print(f"Error generating token: {str(e)}")
        return None

# --- HELPER: TRIGGER STK PUSH ---
def stk_push_request(phone_number, amount, user):
    access_token = get_access_token()
    if not access_token:
        return {'error': 'Failed to generate access token'}

    # 1. Format the phone number (Must be 254...)
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif phone_number.startswith('+254'):
        phone_number = phone_number[1:]
    
    # 2. Generate Timestamp & Password
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    passkey = settings.MPESA_PASSKEY
    shortcode = settings.MPESA_SHORTCODE
    
    password_str = shortcode + passkey + timestamp
    password_b64 = base64.b64encode(password_str.encode()).decode()

    # 3. Define the Payload
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password_b64,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL + "/payments/callback/", # Ensure slash matches urls.py
        "AccountReference": f"User_{user.id}",
        "TransactionDesc": "Plan Upgrade"
    }

    try:
        response = requests.post(settings.MPESA_EXPRESS_URL, json=payload, headers=headers)
        response_data = response.json()
        
        # 4. Save Initial Transaction to DB
        MpesaTransaction.objects.create(
            user=user,
            phone_number=phone_number,
            amount=amount,
            checkout_request_id=response_data.get('CheckoutRequestID', 'FAILED'),
            status='PENDING',
            description='STK Push Initiated'
        )
        
        return response_data
    except Exception as e:
        return {'error': str(e)}

# --- VIEW: BUTTON CLICK HANDLER ---
@login_required
def initiate_payment(request, plan_type):
    # Define Prices
    PRICES = {
        'LITE': 1000,
        'PRO': 2500
    }
    
    amount = PRICES.get(plan_type.upper())
    if not amount:
        return JsonResponse({'error': 'Invalid Plan'}, status=400)

    # Get User Phone
    phone = request.user.phone_number
    if not phone:
        # Fallback to profile phone or dummy if missing
        phone = request.user.dealer_profile.phone_number or '254700000000'

    # Trigger Push
    response = stk_push_request(phone, amount, request.user)
    
    if 'ResponseCode' in response and response['ResponseCode'] == '0':
        # Success logic: Redirect to a "Check your phone" page
        return render(request, 'dealer/payment_pending.html', {'phone': phone})
    else:
        # Debugging: Show the error if Safaricom refuses
        return JsonResponse({'error': 'STK Push Failed', 'details': response})

# --- VIEW: CALLBACK HANDLER (WEBHOOK) ---
@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            stk_callback = body['Body']['stkCallback']
            
            checkout_request_id = stk_callback['CheckoutRequestID']
            result_code = stk_callback['ResultCode']
            result_desc = stk_callback.get('ResultDesc', 'No description')
            
            # Find the transaction
            transaction = MpesaTransaction.objects.filter(checkout_request_id=checkout_request_id).first()
            
            if transaction:
                if result_code == 0:
                    # --- SUCCESSFUL PAYMENT ---
                    transaction.status = 'SUCCESS'
                    transaction.description = 'Payment confirmed'
                    
                    # Extract Receipt Number from Metadata
                    items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                    for item in items:
                        if item['Name'] == 'MpesaReceiptNumber':
                            transaction.mpesa_receipt_number = item['Value']
                    
                    transaction.save()
                    
                    # --- UPGRADE USER ---
                    profile = DealerProfile.objects.get(user=transaction.user)
                    
                    if transaction.amount >= 2500:
                        profile.plan_type = 'PRO'
                    elif transaction.amount >= 1000:
                        profile.plan_type = 'LITE'
                        
                    # Set Expiry (30 Days)
                    profile.subscription_expiry = timezone.now() + timedelta(days=30)
                    profile.save()
                    
                else:
                    # --- FAILED PAYMENT ---
                    transaction.status = 'FAILED'
                    transaction.description = result_desc
                    transaction.save()
                    
            return JsonResponse({'status': 'OK'})
            
        except Exception as e:
            print(f"Callback Error: {e}")
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Only POST allowed'}, status=400)

# --- NEW: PAYMENT STATUS CHECK (POLLING) ---
@login_required
def check_payment_status(request):
    """
    Polls the database to check if the latest transaction was successful.
    """
    # Get the most recent transaction for the logged-in user
    transaction = MpesaTransaction.objects.filter(user=request.user).order_by('-created_at').first()
    
    if transaction:
        return JsonResponse({
            'status': transaction.status, 
            'description': transaction.description
        })
    
    return JsonResponse({'status': 'PENDING', 'description': 'No transaction found'})