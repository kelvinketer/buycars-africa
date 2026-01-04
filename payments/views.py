import json
import africastalking
from datetime import timedelta
from decimal import Decimal 
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
# FIXED: Imported Booking instead of CarBooking
from cars.models import Booking 
from wallet.models import Wallet, Transaction 

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
    # FIXED: Using Booking model
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
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
                # FIXED: Using Booking model
                booking_obj = get_object_or_404(Booking, id=booking_id)
                amount = int(booking_obj.total_price) # Ensure integer (Note: field is total_price in new model)
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

# --- API: M-PESA CALLBACK (UPDATED WITH WALLET LOGIC) ---
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

                    # LOGIC 2: Handle Car Booking & Wallet Credit
                    if payment.booking:
                        payment.booking.status = 'PAID'
                        payment.booking.save()
                        
                        # --- WALLET LOGIC STARTS HERE ---
                        try:
                            car = payment.booking.car
                            dealer = car.dealer
                            
                            # 1. Get or Create Wallet for Dealer
                            wallet, created = Wallet.objects.get_or_create(user=dealer)
                            
                            # 2. Calculate Commission (e.g., 10%)
                            total_amount = Decimal(payment.amount)
                            commission_rate = Decimal('0.10') 
                            commission = total_amount * commission_rate
                            dealer_share = total_amount - commission
                            
                            # 3. Credit Wallet
                            wallet.balance += dealer_share
                            wallet.total_earned += dealer_share
                            wallet.save()
                            
                            # 4. Record Transaction
                            Transaction.objects.create(
                                wallet=wallet,
                                amount=dealer_share,
                                transaction_type='CREDIT',
                                description=f"Rental Income: {car.year} {car.make} {car.model}",
                                reference=f"Booking #{payment.booking.id}"
                            )
                            
                            # Notify Dealer
                            dealer_phone = dealer.dealer_profile.phone_number
                            msg = f"You earned KES {dealer_share:,.0f} from a new booking! Wallet Bal: KES {wallet.balance:,.0f}"
                            send_sms_notification(dealer_phone, msg)
                            
                        except Exception as w_err:
                            print(f"Wallet Credit Error: {w_err}")
                        # --- WALLET LOGIC ENDS HERE ---

                        # Notify Customer
                        send_sms_notification(payment.phone_number, f"Booking Confirmed! Receipt: {payment.mpesa_receipt_number}")

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