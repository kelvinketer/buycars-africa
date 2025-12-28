import requests
import json
import base64
import africastalking
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from requests.auth import HTTPBasicAuth

from .models import MpesaTransaction  # Ensure your model is named MpesaTransaction
from users.models import DealerProfile

# --- HELPER: SEND SMS (AFRICA'S TALKING) ---
def send_sms_notification(phone_number, message):
    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    
    try:
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS
        
        # Format phone for SMS
        if phone_number.startswith('0'):
            phone_number = '+254' + phone_number[1:]
        elif phone_number.startswith('254'):
            phone_number = '+' + phone_number
            
        sms.send(message, [phone_number])
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")

# --- HELPER: GENERATE ACCESS TOKEN ---
def get_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_URL = settings.MPESA_ACCESS_TOKEN_URL

    try:
        r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        r.raise_for_status()
        return r.json()['access_token']
    except Exception as e:
        print(f"Error generating token: {str(e)}")
        return None

# --- HELPER: TRIGGER STK PUSH (FIXED) ---
def stk_push_request(phone_number, amount, user, plan_type):
    access_token = get_access_token()
    if not access_token:
        return {'error': 'Failed to generate access token'}

    # 1. ROBUST PHONE SANITIZATION (Fixes "Invalid PhoneNumber" Error)
    # Remove spaces, dashes, plus signs
    phone_number = str(phone_number).strip().replace(" ", "").replace("-", "").replace("+", "")
    
    # Ensure it starts with 254
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    
    # Final validation
    if not phone_number.isdigit() or len(phone_number) != 12:
        return {'error': f'Invalid phone format: {phone_number}. Use 0712345678.'}
    
    # 2. Generate Timestamp & Password
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    passkey = settings.MPESA_PASSKEY
    shortcode = settings.MPESA_SHORTCODE
    
    password_str = shortcode + passkey + timestamp
    password_b64 = base64.b64encode(password_str.encode()).decode()

    # 3. Define Payload
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
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"BuyCars {plan_type}",
        "TransactionDesc": f"Upgrade to {plan_type}"
    }

    try:
        response = requests.post(settings.MPESA_EXPRESS_URL, json=payload, headers=headers)
        response_data = response.json()
        
        # 4. DATABASE SAFETY (Fixes "Duplicate Key" Error)
        # Only save if Safaricom actually accepted the request (ResponseCode == 0)
        if response_data.get('ResponseCode') == '0':
            MpesaTransaction.objects.create(
                user=user,
                phone_number=phone_number,
                amount=amount,
                checkout_request_id=response_data['CheckoutRequestID'],
                status='PENDING',
                description=f'Subscription for {plan_type}'
            )
        
        return response_data
    except Exception as e:
        return {'error': str(e)}

# --- VIEW 1: SHOW CHECKOUT PAGE ---
@login_required
def initiate_payment(request, plan_type):
    """
    Renders the checkout.html page where user enters phone number.
    """
    PRICES = {
        'LITE': 1000,
        'PRO': 2500
    }
    
    amount = PRICES.get(plan_type.upper())
    if not amount:
        messages.error(request, "Invalid Plan Selected")
        return redirect('dealer_dashboard')

    # Pre-fill phone if available
    phone = request.user.dealer_profile.phone_number or ''

    context = {
        'plan_type': plan_type,
        'plan_name': f"{plan_type.title()} Plan",
        'amount': amount,
        'phone_number': phone
    }
    return render(request, 'payments/checkout.html', context)

# --- VIEW 2: PROCESS FORM & TRIGGER STK ---
@login_required
def process_payment(request):
    """
    Receives POST from checkout.html, sanitizes phone, triggers STK.
    """
    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        plan_type = request.POST.get('plan_type')
        
        # Define Prices again for safety
        PRICES = {'LITE': 1000, 'PRO': 2500}
        amount = PRICES.get(plan_type, 2500)

        # Trigger STK Push
        response = stk_push_request(phone, amount, request.user, plan_type)
        
        # Check Result
        if response.get('ResponseCode') == '0':
            # Success: Redirect to Dashboard with instruction
            messages.success(request, f"STK Push sent to {phone}. Please enter your M-PESA PIN.")
            return redirect('dealer_dashboard')
        else:
            # Failure: Show error and go back to checkout
            error_msg = response.get('errorMessage', 'Connection failed')
            # Handle nested error details if present
            if 'details' in response: 
                error_msg = response['details']
                
            messages.error(request, f"Payment Failed: {error_msg}")
            return redirect('initiate_payment', plan_type=plan_type)

    return redirect('dealer_dashboard')

# --- VIEW 3: CALLBACK HANDLER (WEBHOOK) ---
@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            stk_callback = body.get('Body', {}).get('stkCallback', {})
            
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc', 'No description')
            
            # Find the transaction
            transaction = MpesaTransaction.objects.filter(checkout_request_id=checkout_request_id).first()
            
            if transaction:
                if result_code == 0:
                    # --- SUCCESSFUL PAYMENT ---
                    transaction.status = 'SUCCESS'
                    transaction.description = 'Payment confirmed'
                    
                    # Extract Receipt Number
                    items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                    for item in items:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            transaction.mpesa_receipt_number = item.get('Value')
                    
                    transaction.save()
                    
                    # --- UPGRADE USER ---
                    profile = DealerProfile.objects.get(user=transaction.user)
                    
                    new_plan_name = "Free"
                    if transaction.amount >= 2500:
                        profile.plan_type = 'PRO'
                        new_plan_name = "Pro"
                    elif transaction.amount >= 1000:
                        profile.plan_type = 'LITE'
                        new_plan_name = "Lite"
                        
                    profile.subscription_expiry = timezone.now() + timedelta(days=30)
                    profile.save()

                    # --- SEND CONFIRMATION SMS ---
                    msg = f"Confirmed! We received KES {transaction.amount}. You are now on the {new_plan_name} Plan. Start selling on BuyCars Africa!"
                    send_sms_notification(transaction.phone_number, msg)
                    
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

# --- VIEW 4: PAYMENT STATUS POLLING (OPTIONAL) ---
@login_required
def check_payment_status(request):
    transaction = MpesaTransaction.objects.filter(user=request.user).order_by('-created_at').first()
    if transaction:
        return JsonResponse({
            'status': transaction.status, 
            'description': transaction.description
        })
    return JsonResponse({'status': 'PENDING', 'description': 'No transaction found'})