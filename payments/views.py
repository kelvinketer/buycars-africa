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
from django.contrib import messages  # Added: Missing in your original code

from .models import Payment
from .forms import PaymentForm
from .mpesa import MpesaClient
from users.models import DealerProfile
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

# --- HELPER: SHARED SUCCESS LOGIC (Used by M-Pesa & Card) ---
def process_successful_payment(payment):
    """
    Credits dealer wallet and updates booking/subscription status
    regardless of payment method (M-Pesa or Card).
    """
    # 1. Handle Dealer Subscription
    if payment.plan_type:
        try:
            profile = DealerProfile.objects.get(user=payment.user)
            profile.plan_type = payment.plan_type
            profile.subscription_expiry = timezone.now() + timedelta(days=30)
            profile.save()
            send_sms_notification(payment.phone_number, f"Plan Active! Ref: {payment.checkout_request_id}")
        except Exception as e:
            print(f"Subscription Error: {e}")

    # 2. Handle Car Booking & Wallet Credit
    if payment.booking:
        payment.booking.status = 'PAID'
        payment.booking.save()
        
        try:
            car = payment.booking.car
            dealer = car.dealer
            
            # A. Get or Create Wallet for Dealer
            wallet, created = Wallet.objects.get_or_create(user=dealer)
            
            # B. Calculate Commission (10%)
            total_amount = Decimal(payment.amount)
            commission_rate = Decimal('0.10') 
            commission = total_amount * commission_rate
            dealer_share = total_amount - commission
            
            # C. Credit Wallet
            wallet.balance += dealer_share
            wallet.total_earned += dealer_share
            wallet.save()
            
            # D. Record Transaction
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

        # Notify Customer
        send_sms_notification(payment.phone_number, f"Booking Confirmed! Ref: {payment.checkout_request_id}")


# --- VIEW: CHECKOUT PAGE ---
@login_required
def checkout(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    if booking.status == 'PAID':
        messages.info(request, "This booking is already paid for.")
        return redirect('home')

    form = PaymentForm()
    return render(request, 'payments/checkout.html', {
        'booking': booking,
        'form': form,
        # Pass user info for Flutterwave pre-fill
        'user_email': request.user.email,
        'user_phone': request.user.dealer_profile.phone_number if hasattr(request.user, 'dealer_profile') else ''
    })


# --- NEW: FLUTTERWAVE VERIFICATION VIEW ---
@login_required
def verify_flutterwave(request):
    """
    Handles the redirect from Flutterwave after card payment.
    """
    status = request.GET.get('status')
    tx_ref = request.GET.get('tx_ref')
    transaction_id = request.GET.get('transaction_id')

    if status == 'successful':
        try:
            # tx_ref format is "BC-{timestamp}-{booking_id}"
            parts = tx_ref.split('-')
            booking_id = parts[-1] 
            
            booking = Booking.objects.get(id=booking_id)
            
            # Prevent double payment recording
            if Payment.objects.filter(checkout_request_id=tx_ref).exists():
                messages.info(request, "Payment already recorded.")
                return redirect('renter_dashboard') # Assuming you have this URL
            
            # Create Payment Record
            payment = Payment.objects.create(
                user=request.user,
                booking=booking,
                amount=booking.total_price, # Assuming full payment
                phone_number=request.user.dealer_profile.phone_number if hasattr(request.user, 'dealer_profile') else '0000000000',
                checkout_request_id=tx_ref, # Use tx_ref as unique ID
                merchant_request_id=str(transaction_id),
                status='SUCCESS',
                description='Paid via Card (Flutterwave)'
            )
            
            # Execute Shared Logic (Credit Wallet, Update Booking)
            process_successful_payment(payment)
            
            messages.success(request, "Payment Successful! Your booking is confirmed.")
            return redirect('home') # Or dashboard

        except Exception as e:
            print(f"Card Verify Error: {e}")
            messages.error(request, "Error verifying payment. Please contact support.")
            return redirect('home')
    else:
        messages.error(request, "Payment cancelled or failed.")
        return redirect('home')


# --- API: TRIGGER STK PUSH (Unchanged logic, just cleaner) ---
@login_required
@csrf_exempt
def initiate_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            plan_type = data.get('plan_type') 
            booking_id = data.get('booking_id')

            amount = 0
            account_ref = "BuyCars"
            description = ""
            booking_obj = None

            if plan_type:
                PRICES = {'STARTER': 1500, 'LITE': 5000, 'PRO': 12000}
                amount = PRICES.get(plan_type)
                account_ref = f"Plan {plan_type}"
                description = f"Upgrade to {plan_type}"
            
            elif booking_id:
                booking_obj = get_object_or_404(Booking, id=booking_id)
                amount = int(booking_obj.total_price)
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
                Payment.objects.create(
                    user=request.user,
                    booking=booking_obj,
                    phone_number=phone_number,
                    amount=amount,
                    checkout_request_id=response['CheckoutRequestID'],
                    merchant_request_id=response.get('MerchantRequestID'),
                    plan_type=plan_type,
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


# --- API: M-PESA CALLBACK (Refactored to use shared logic) ---
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
                    
                    # CALL SHARED LOGIC (Credits Wallet, Updates Booking)
                    process_successful_payment(payment)

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