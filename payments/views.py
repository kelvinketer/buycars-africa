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
from django.contrib import messages

from .models import Payment
from .forms import PaymentForm
from .mpesa import MpesaClient
from users.models import DealerProfile
from cars.models import Booking 
from wallet.models import Wallet, Transaction 

# --- HELPER: SEND SMS ---
def send_sms_notification(phone_number, message):
    # Safe check: If phone is dummy or empty, skip SMS
    if not phone_number or phone_number == '0000000000':
        return

    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    if not api_key or not username or username == 'sandbox':
        return 
    try:
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS
        if phone_number.startswith('0'): phone_number = '+254' + phone_number[1:]
        elif phone_number.startswith('254'): phone_number = '+' + phone_number
        sms.send(message, [phone_number])
    except Exception as e: print(f"Error sending SMS: {str(e)}")

# --- HELPER: SHARED SUCCESS LOGIC ---
def process_successful_payment(payment):
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

    # 2. Handle Car Booking
    if payment.booking:
        payment.booking.status = 'PAID'
        payment.booking.save()
        
        # Credit Dealer Wallet
        try:
            car = payment.booking.car
            dealer = car.dealer
            wallet, _ = Wallet.objects.get_or_create(user=dealer)
            
            total_amount = Decimal(payment.amount)
            commission = total_amount * Decimal('0.10') 
            dealer_share = total_amount - commission
            
            wallet.balance += dealer_share
            wallet.total_earned += dealer_share
            wallet.save()
            
            Transaction.objects.create(
                wallet=wallet, amount=dealer_share, transaction_type='CREDIT',
                description=f"Rental: {car.make} {car.model}", reference=f"Pay #{payment.id}"
            )
            
            if hasattr(dealer, 'dealer_profile') and dealer.dealer_profile.phone_number:
                send_sms_notification(dealer.dealer_profile.phone_number, f"Earned KES {dealer_share:,.0f} from booking!")
        except Exception as w_err:
            print(f"Wallet Error: {w_err}")

        send_sms_notification(payment.phone_number, f"Booking Confirmed! Ref: {payment.checkout_request_id}")

# --- VIEW: BOOKING CHECKOUT ---
@login_required
def checkout(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    if booking.status == 'PAID':
        messages.info(request, "Already paid.")
        return redirect('home')
    
    # Safe Phone Extraction
    user_phone = ''
    if hasattr(request.user, 'dealer_profile') and request.user.dealer_profile.phone_number:
        user_phone = request.user.dealer_profile.phone_number

    return render(request, 'payments/checkout.html', {
        'booking': booking, 
        'user_phone': user_phone
    })

# --- VIEW: SUBSCRIPTION CHECKOUT ---
@login_required
def subscription_checkout(request, plan_type):
    PRICES = {'STARTER': 1500, 'LITE': 5000, 'PRO': 12000}
    amount = PRICES.get(plan_type.upper(), 0)
    
    if amount == 0:
        messages.error(request, "Invalid plan selected.")
        return redirect('pricing')
    
    # Safe Phone Extraction
    user_phone = ''
    if hasattr(request.user, 'dealer_profile') and request.user.dealer_profile.phone_number:
        user_phone = request.user.dealer_profile.phone_number

    return render(request, 'payments/checkout.html', {
        'plan_type': plan_type.upper(),
        'amount': amount,
        'plan_name': f"{plan_type.title()} Plan",
        'user_email': request.user.email,
        'user_phone': user_phone
    })

# --- NEW: VERIFY FLUTTERWAVE (FIXED PHONE LOGIC) ---
@login_required
def verify_flutterwave(request):
    status = request.GET.get('status')
    tx_ref = request.GET.get('tx_ref') # Format: TYPE-Timestamp-ID

    if status == 'successful':
        try:
            parts = tx_ref.split('-')
            payment_type = parts[0] # "BKG" or "SUB"
            
            # Check for Duplicate
            if Payment.objects.filter(checkout_request_id=tx_ref).exists():
                return redirect('dealer_dashboard' if payment_type == 'SUB' else 'home')

            booking = None
            plan_type = None
            amount = 0
            desc = ""
            
            if payment_type == 'BKG':
                ref_id = parts[-1]
                booking = Booking.objects.get(id=ref_id)
                amount = booking.total_price
                desc = 'Card Payment: Booking'
            elif payment_type == 'SUB':
                plan_type = parts[2] 
                PRICES = {'STARTER': 1500, 'LITE': 5000, 'PRO': 12000}
                amount = PRICES.get(plan_type, 0)
                desc = f'Card Payment: {plan_type} Plan'

            # --- CRITICAL FIX: Safe Phone Number ---
            # If profile exists AND has a number, use it. Otherwise, use dummy.
            safe_phone = '0000000000'
            if hasattr(request.user, 'dealer_profile') and request.user.dealer_profile.phone_number:
                safe_phone = request.user.dealer_profile.phone_number

            # Create Record
            payment = Payment.objects.create(
                user=request.user,
                booking=booking,
                plan_type=plan_type,
                amount=amount,
                phone_number=safe_phone, # <--- Now using the safe variable
                checkout_request_id=tx_ref,
                status='SUCCESS',
                description=desc
            )
            
            process_successful_payment(payment)
            messages.success(request, "Payment Successful!")
            return redirect('dealer_dashboard' if plan_type else 'home')

        except Exception as e:
            messages.error(request, f"Verification Error: {str(e)}")
            return redirect('home')
    else:
        messages.error(request, "Payment Failed.")
        return redirect('home')

# --- API: INITIATE STK PUSH (Unchanged) ---
@login_required
@csrf_exempt
def initiate_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone = data.get('phone_number')
            plan = data.get('plan_type')
            bid = data.get('booking_id')
            
            amount = 0
            ref = "BuyCars"
            booking = None

            if plan:
                PRICES = {'STARTER': 1500, 'LITE': 5000, 'PRO': 12000}
                amount = PRICES.get(plan)
                ref = f"Plan {plan}"
            elif bid:
                booking = get_object_or_404(Booking, id=bid)
                amount = int(booking.total_price)
                ref = f"CarHire {bid}"

            client = MpesaClient()
            res = client.stk_push(phone, amount, ref)

            if res.get('ResponseCode') == '0':
                Payment.objects.create(
                    user=request.user, booking=booking, plan_type=plan,
                    phone_number=phone, amount=amount,
                    checkout_request_id=res['CheckoutRequestID'],
                    status='PENDING', description=ref
                )
                return JsonResponse({'status': 'success', 'message': 'STK Push sent!'})
            return JsonResponse({'status': 'error', 'message': res.get('errorMessage')})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# --- API: MPESA CALLBACK (Unchanged) ---
@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            stk = body.get('Body', {}).get('stkCallback', {})
            pay = Payment.objects.filter(checkout_request_id=stk.get('CheckoutRequestID')).first()
            if pay:
                if stk.get('ResultCode') == 0:
                    pay.status = 'SUCCESS'
                    pay.save()
                    process_successful_payment(pay)
                else:
                    pay.status = 'FAILED'
                    pay.save()
            return JsonResponse({'status': 'OK'})
        except: pass
    return JsonResponse({'error': 'POST only'}, status=400)

@login_required
def check_payment_status(request):
    pay = Payment.objects.filter(user=request.user).order_by('-created_at').first()
    return JsonResponse({'status': pay.status if pay else 'PENDING'})