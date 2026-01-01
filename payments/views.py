import json
import africastalking
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .models import Payment
from .mpesa import MpesaClient
from users.models import DealerProfile

# --- HELPER: SEND SMS (AFRICA'S TALKING) ---
def send_sms_notification(phone_number, message):
    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    
    if not api_key or not username or username == 'sandbox':
        print("Africa's Talking credentials missing or in sandbox mode.")
        # In production, remove this return to ensure SMS sends
        if settings.DEBUG: return 

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

# --- VIEW 1: TRIGGER STK PUSH (AJAX) ---
@login_required
@csrf_exempt
def initiate_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan_type = data.get('plan_type') # 'LITE' or 'PRO'
            phone_number = data.get('phone_number')

            # 1. Define Prices (Server-Side Validation)
            PRICES = {'STARTER': 1500, 'LITE': 5000, 'PRO': 12000}
            amount = PRICES.get(plan_type)
            
            if not amount:
                return JsonResponse({'status': 'error', 'message': 'Invalid Plan Selected'})

            # 2. Trigger M-PESA STK Push using our Class
            client = MpesaClient()
            response = client.stk_push(
                phone_number=phone_number,
                amount=amount, 
                account_reference=f"BuyCars {plan_type.title()}"
            )

            # 3. Handle M-Pesa Response
            if response.get('ResponseCode') == '0':
                # Success! Save Pending Payment
                Payment.objects.create(
                    user=request.user,
                    phone_number=phone_number,
                    amount=amount,
                    checkout_request_id=response['CheckoutRequestID'],
                    merchant_request_id=response.get('MerchantRequestID'),
                    plan_type=plan_type,
                    status='PENDING',
                    description=f"Upgrade to {plan_type} Plan"
                )
                return JsonResponse({
                    'status': 'success', 
                    'message': 'STK Push sent! Check your phone to enter PIN.'
                })
            else:
                # M-Pesa rejected it (e.g., wrong number format)
                return JsonResponse({
                    'status': 'error', 
                    'message': response.get('errorMessage', 'Failed to initiate payment.')
                })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

# --- VIEW 2: M-PESA CALLBACK (WEBHOOK) ---
@csrf_exempt
def mpesa_callback(request):
    """
    Safaricom hits this URL when the user enters their PIN (or cancels).
    """
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            stk_callback = body.get('Body', {}).get('stkCallback', {})
            
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc', 'No description')
            
            # Find the transaction
            payment = Payment.objects.filter(checkout_request_id=checkout_request_id).first()
            
            if payment:
                if result_code == 0:
                    # --- SUCCESSFUL PAYMENT ---
                    payment.status = 'SUCCESS'
                    payment.description = 'Payment confirmed'
                    
                    # Extract Receipt Number
                    items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                    for item in items:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            payment.mpesa_receipt_number = item.get('Value')
                    
                    payment.save()
                    
                    # --- UPGRADE DEALER LOGIC ---
                    try:
                        profile = DealerProfile.objects.get(user=payment.user)
                        
                        # Apply Plan Upgrade
                        profile.plan_type = payment.plan_type
                        
                        # Set Expiry to 30 days from NOW
                        profile.subscription_expiry = timezone.now() + timedelta(days=30)
                        profile.save()

                        # Send SMS
                        msg = f"Confirmed! Your {payment.plan_type} Plan is active. Receipt: {payment.mpesa_receipt_number}. Happy selling!"
                        send_sms_notification(payment.phone_number, msg)
                        
                    except DealerProfile.DoesNotExist:
                        print(f"Error: DealerProfile not found for user {payment.user.id}")

                else:
                    # --- FAILED/CANCELLED PAYMENT ---
                    payment.status = 'FAILED'
                    payment.description = result_desc
                    payment.save()
            
            return JsonResponse({'status': 'OK'})
            
        except Exception as e:
            print(f"Callback Error: {e}")
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Only POST allowed'}, status=400)

# --- VIEW 3: CHECK STATUS (POLLING) ---
@login_required
def check_payment_status(request):
    """
    Frontend calls this every 2 seconds to check if payment is complete.
    """
    # Get the most recent transaction for this user
    payment = Payment.objects.filter(user=request.user).order_by('-created_at').first()
    
    if payment:
        return JsonResponse({
            'status': payment.status, 
            'description': payment.description
        })
    return JsonResponse({'status': 'PENDING', 'description': 'No transaction found'})