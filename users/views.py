from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm  # Checks for phone_number

def signup_view(request):
    if request.method == 'POST':
        # This form now expects username, email, AND phone_number
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # Go straight to dashboard to upload their first car
            return redirect('dealer_dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # IMPROVEMENT: If they were trying to go somewhere specific, send them there.
            if 'next' in request.GET:
                return redirect(request.GET.get('next'))
            
            # Otherwise, go to dashboard
            return redirect('dealer_dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')