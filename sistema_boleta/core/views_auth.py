from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Usuario o contraseña incorrecto, vuelve a ingresar")
            return redirect('login')
        
    # Si ya se esta logueado, redirigir al home
    if request.user.is_authenticated:
        return redirect('home')
        
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')