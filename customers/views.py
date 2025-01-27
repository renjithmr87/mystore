from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from . models import Customer
from django.views.decorators.csrf import csrf_exempt

# Logout
def signout(request):
    logout(request) 
    return redirect('login')

# Account
@csrf_exempt
def show_account(request):
    context={}
    if request.POST and 'register' in request.POST:
        context['register'] = True
        try:
            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')
            address = request.POST.get('address')
            phone = request.POST.get('phone')
            # Creates User Accounts
            user = User.objects.create_user(
                username = username,
                password = password,
                email = email
            )
            user.save()
            
            # Creates Customer Account
            customer = Customer.objects.create(
                user = user,
                firstname = firstname,
                lastname = lastname,
                phone = phone,
                address = address,
            )
            if customer:
                customer.save()
                success_message = "User Registered Successfully"
                messages.success(request, success_message)
                return redirect('home')
        except Exception as e:
            error_message = "Username already taken"
            messages.error(request, error_message)
 
    elif request.POST and 'login' in request.POST:
        context['register'] = False
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username,password=password)
        if user:
            login(request,user)
            print("Redirecting to home...")  # Debugging

            return redirect('home')
        else:
            message_login="Invalid Credentials"
            messages.error(request,message_login)
    # print(request.POST)
    return render(request, 'account.html',context)

# Edit Customer Account
# @login_required('login/')
@csrf_exempt
def edit_profile(request, pk):
    customer_to_be_edited = Customer.objects.get(pk)

    context={}
    if request.POST and 'edit_profile' in request.POST:
        # context['register'] = True
        try:
            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')
            address = request.POST.get('address')
            phone = request.POST.get('phone')

            # Edit User
            user = User.objects.create(
                username = username,
                password = password,
                email = email
            )
            user.save()
            
            # Edit Customer Account
            customer = Customer.objects.create(
                user = user,
                firstname = firstname,
                lastname = lastname,
                phone = phone,
                address = address,
            )
            if customer:
                customer_to_be_edited.user = user 
                customer_to_be_edited.first_name = firstname
                customer_to_be_edited.last_name_name = lastname
                customer_to_be_edited.phonee = phone
                customer_to_be_edited.address = address
                customer_to_be_edited.save()
                success_message = "Profile Updated Successfully"
                messages.success(request, success_message)
                return redirect('home')
        except Exception as e:
            error_message = "Username already taken"
            messages.error(request, error_message)
 
    return render(request, 'edit_account.html',context)
