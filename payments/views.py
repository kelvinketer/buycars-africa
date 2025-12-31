import json
import base64
import requests
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

from .models import MpesaTransaction
from users.models import DealerProfile

# --- HELPER: SEND SMS (AFRICA'S TALKING) ---
def send_sms_notification(phone_number, message):
    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    
    if not api_key or not username:
        print("Africa's Talking credentials missing.")
        return

    try:
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS
        
        # Format phone for SMS (Must be +254...)
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

# --- HELPER: TRIGGER STK PUSH ---
def stk_push_request(phone_number, amount, user, plan_type):
    access_token = get_access_token()
    if not access_token:
        return {'error': 'Failed to generate access token'}

    # 1. ROBUST PHONE SANITIZATION
    phone_number = str(phone_number).strip().replace(" ", "").replace("-", "").replace("+", "")
    
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    
    if not phone_number.isdigit() or len(phone_number) != 12:
        return {'error': f'Invalid phone format: {phone_number}'}
    
    # 2. Generate Timestamp & Password
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    passkey = settings.MPESA_PASSKEY
    shortcode = settings.MPESA_SHORTCODE # This is the Store Number
    
    password_str = shortcode + passkey + timestamp
    password_b64 = base64.b64encode(password_str.encode()).decode()

    # 3. Define Payload
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Use setting for Transaction Type (Paybill vs Buy Goods)
    transaction_type = getattr(settings, 'MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline')

    # Determine PartyB (Destination)
    # If using a Till Number, PartyB is the Till Number.
    # If using Paybill, PartyB is the Shortcode.
    party_b = getattr(settings, 'MPESA_TILL_NUMBER', shortcode)

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password_b64,
        "Timestamp": timestamp,
        "TransactionType": transaction_type,
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": party_b,   # Updated to use Till Number if set
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"BuyCars{plan_type}", 
        "TransactionDesc": f"Upgrade to {plan_type}"
    }

    try:
        response = requests.post(settings.MPESA_EXPRESS_URL, json=payload, headers=headers)
        response_data = response.json()
        
        # 4. DATABASE SAFETY
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
    # Updated 3-Tier Pricing
    PRICES = {
        'STARTER': 1500,
        'LITE': 5000,
        'PRO': 12000
    }
    
    amount = PRICES.get(plan_type.upper())
    if not amount:
        messages.error(request, "Invalid Plan Selected")
        return redirect('dealer_dashboard')

    phone = request.user.dealer_profile.phone_number or ''

    context = {
        'plan_type': plan_type.upper(),
        'plan_name': f"{plan_type.title()} Plan",
        'amount': amount,
        'phone_number': phone
    }
    return render(request, 'payments/checkout.html', context)

# --- VIEW 2: PROCESS FORM & TRIGGER STK ---
@login_required
def process_payment(request):
    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        plan_type = request.POST.get('plan_type')
        
        # Updated 3-Tier Pricing
        PRICES = {'STARTER': 1500, 'LITE': 5000, 'PRO': 12000}
        amount = PRICES.get(plan_type, 1500) # Default to Starter

        response = stk_push_request(phone, amount, request.user, plan_type)
        
        if response.get('ResponseCode') == '0':
            # SUCCESS: Direct to pending page to wait for PIN
            return render(request, 'dealer/payment_pending.html', {'phone': phone})
        else:
            # ERROR: Show Safaricom error message
            error_msg = response.get('errorMessage', 'Connection failed')
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
            
            transaction = MpesaTransaction.objects.filter(checkout_request_id=checkout_request_id).first()
            
            if transaction:
                if result_code == 0:
                    # --- SUCCESSFUL PAYMENT ---
                    transaction.status = 'SUCCESS'
                    transaction.description = 'Payment confirmed'
                    
                    items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                    for item in items:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            transaction.mpesa_receipt_number = item.get('Value')
                    
                    transaction.save()
                    
                    # --- UPGRADE USER (UPDATED 3-TIER LOGIC) ---
                    try:
                        profile = DealerProfile.objects.get(user=transaction.user)
                        
                        amt = int(transaction.amount)
                        new_plan_name = "Free"
                        
                        if amt >= 12000:
                            profile.plan_type = 'PRO'
                            new_plan_name = "Pro"
                        elif amt >= 5000:
                            profile.plan_type = 'LITE'
                            new_plan_name = "Lite"
                        elif amt >= 1500:
                            profile.plan_type = 'STARTER'
                            new_plan_name = "Starter"
                            
                        # Set Expiry to 30 days from NOW
                        profile.subscription_expiry = timezone.now() + timedelta(days=30)
                        profile.save()

                        # --- SEND SMS ---
                        msg = f"Confirmed! We received KES {transaction.amount}. Your {new_plan_name} Plan is active. Happy selling!"
                        send_sms_notification(transaction.phone_number, msg)
                        
                    except DealerProfile.DoesNotExist:
                        print(f"Error: DealerProfile not found for user {transaction.user.id}")

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

# --- VIEW 4: PAYMENT STATUS POLLING ---
@login_required
def check_payment_status(request):
    """
    Used by the frontend (AJAX) to check if the payment went through.
    """
    # Get the most recent transaction for this user
    transaction = MpesaTransaction.objects.filter(user=request.user).order_by('-created_at').first()
    
    if transaction:
        return JsonResponse({
            'status': transaction.status, 
            'description': transaction.description
        })
    return JsonResponse({'status': 'PENDING', 'description': 'No transaction found'})