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
from .forms import PaymentForm
from .mpesa import MpesaClient
from users.models import DealerProfile
from cars.models import CarBooking  # <--- CRITICAL IMPORT

# --- HELPER: SEND SMS ---
def send_sms_notification(phone_number, message):
    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    
    if not api_key or not username or username == 'sandbox':
        if settings.DEBUG: print(f"Mock SMS to {phone_number}: {message}")
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

# --- VIEW: CHECKOUT PAGE ---
@login_required
def checkout(request, booking_id):
    booking = get_object_or_404(CarBooking, id=booking_id, customer=request.user)
    
    if booking.status == 'PAID':
        messages.info(request, "This booking is already paid for.")
        return redirect('home')

    form = PaymentForm()
    return render(request, 'payments/checkout.html', {
        'booking': booking,
        'form': form
    })

# --- API: TRIGGER STK PUSH ---
@login_required
@csrf_exempt
def initiate_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            
            # Scenario A: Dealer Subscription
            plan_type = data.get('plan_type') 
            
            # Scenario B: Car Booking
            booking_id = data.get('booking_id')

            amount = 0
            account_ref = "BuyCars"
            description = ""
            booking_obj = None

            if plan_type:
                # Subscription Logic
                PRICES = {'STARTER': 1500, 'LITE': 5000, 'PRO': 12000}
                amount = PRICES.get(plan_type)
                account_ref = f"Plan {plan_type}"
                description = f"Upgrade to {plan_type}"
            
            elif booking_id:
                # Booking Logic
                booking_obj = get_object_or_404(CarBooking, id=booking_id)
                amount = int(booking_obj.total_cost) # Ensure integer
                account_ref = f"CarHire {booking_id}"
                description = f"Rent {booking_obj.car.make} {booking_obj.car.model}"
            
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid Payment Type'})

            # Trigger M-PESA
            client = MpesaClient()
            response = client.stk_push(
                phone_number=phone_number,
                amount=amount, 
                account_reference=account_ref
            )

            if response.get('ResponseCode') == '0':
                # Create Payment Record
                Payment.objects.create(
                    user=request.user,
                    booking=booking_obj, # Link if it exists
                    phone_number=phone_number,
                    amount=amount,
                    checkout_request_id=response['CheckoutRequestID'],
                    merchant_request_id=response.get('MerchantRequestID'),
                    plan_type=plan_type, # Save if exists
                    status='PENDING',
                    description=description
                )
                return JsonResponse({
                    'status': 'success', 
                    'message': 'STK Push sent! Check your phone.'
                })
            else:
                return JsonResponse({
                    'status': 'error', 
                    'message': response.get('errorMessage', 'Failed to initiate payment.')
                })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# --- API: M-PESA CALLBACK ---
@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            stk_callback = body.get('Body', {}).get('stkCallback', {})
            
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc', 'No description')
            
            payment = Payment.objects.filter(checkout_request_id=checkout_request_id).first()
            
            if payment:
                if result_code == 0:
                    # --- SUCCESS ---
                    payment.status = 'SUCCESS'
                    payment.description = 'Payment confirmed'
                    
                    # Extract Receipt
                    items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                    for item in items:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            payment.mpesa_receipt_number = item.get('Value')
                    payment.save()
                    
                    # LOGIC 1: Handle Dealer Subscription
                    if payment.plan_type:
                        try:
                            profile = DealerProfile.objects.get(user=payment.user)
                            profile.plan_type = payment.plan_type
                            profile.subscription_expiry = timezone.now() + timedelta(days=30)
                            profile.save()
                            send_sms_notification(payment.phone_number, f"Plan Active! Receipt: {payment.mpesa_receipt_number}")
                        except: pass

                    # LOGIC 2: Handle Car Booking
                    if payment.booking:
                        payment.booking.status = 'PAID'
                        payment.booking.save()
                        
                        # Notify Customer
                        send_sms_notification(payment.phone_number, f"Booking Confirmed! You have hired the {payment.booking.car.make} {payment.booking.car.model}. Receipt: {payment.mpesa_receipt_number}")

                else:
                    # --- FAILED ---
                    payment.status = 'FAILED'
                    payment.description = result_desc
                    payment.save()
            
            return JsonResponse({'status': 'OK'})
            
        except Exception as e:
            print(f"Callback Error: {e}")
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Only POST allowed'}, status=400)

# --- API: CHECK STATUS (POLLING) ---
@login_required
def check_payment_status(request):
    # Get the most recent transaction for this user
    payment = Payment.objects.filter(user=request.user).order_by('-created_at').first()
    
    if payment:
        return JsonResponse({
            'status': payment.status, 
            'description': payment.description
        })
    return JsonResponse({'status': 'PENDING', 'description': 'No transaction found'})