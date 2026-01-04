from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import Wallet, Transaction, PayoutRequest
from decimal import Decimal

@login_required
def dealer_wallet(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        phone = request.POST.get('phone')
        
        if amount > wallet.balance:
            messages.error(request, "Insufficient balance.")
        elif amount < 500:
            messages.error(request, "Minimum withdrawal is KES 500.")
        else:
            # Create Payout Request
            PayoutRequest.objects.create(wallet=wallet, amount=amount, mpesa_number=phone)
            
            # Deduct from Wallet immediately (to prevent double withdraw)
            wallet.balance -= amount
            wallet.save()
            
            # Record Debit Transaction
            Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type='DEBIT',
                description="Payout Request",
                reference="Pending Approval"
            )
            messages.success(request, "Withdrawal request received! We will process it shortly.")
            return redirect('dealer_wallet')

    return render(request, 'dealer/wallet.html', {
        'wallet': wallet,
        'transactions': transactions
    })