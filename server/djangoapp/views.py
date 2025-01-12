from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotAllowed
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel, CarMake
from .restapis import post_request, get_dealers_from_cf, get_dealer_reviews_from_cf, get_dealer_by_id
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your views here.

# Create an `about` view to render a static about page
def about(request):
    return render(request, 'djangoapp/about.html')

# Create a `contact` view to return a static contact page
def contact(request):
    return render(request, 'djangoapp/contact.html')

# Create a `login_request` view to handle sign in request
def login_request(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            return redirect("djangoapp:index")

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    print("Log out the user '{}'".format(request.user.username))
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['lastname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.debug("{}is new user".format(username))
        if not user_exist:
            user = User.objects.create_user(
                username = username, first_name=first_name, last_name=last_name, password=password,)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request, **kwargs):
    context = {}
    if request.method == "GET":
        if 'id' in kwargs:
            # Retrieve a specific dealer by ID
            dealer_id = kwargs['id']
            url = f"https://us-south.functions.appdomain.cloud/api/v1/web/832fded6-63ea-4e95-8f65-b5cd7ce11246/dealership-package/get-dealership?id={dealer_id}"
        elif 'st' in kwargs:
            # Retrieve dealerships by state
            state = kwargs['st']
            url = f"https://us-south.functions.appdomain.cloud/api/v1/web/832fded6-63ea-4e95-8f65-b5cd7ce11246/dealership-package/get-dealership?st={state}"
        else:
            url = "https://us-south.functions.appdomain.cloud/api/v1/web/832fded6-63ea-4e95-8f65-b5cd7ce11246/dealership-package/get-dealership"
        # Get dealers from the URL 
        dealerships = get_dealers_from_cf(url, **kwargs)
        context['dealerships'] = dealerships
        # Concat all dealer's short name
        #dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Return a list of dealer short name
        #return HttpResponse(dealer_names)
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = f"https://us-south.functions.appdomain.cloud/api/v1/web/832fded6-63ea-4e95-8f65-b5cd7ce11246/dealership-package/get-review/review?dealerId={dealer_id}"
        # Get dealer reviews from the URL
        dealer_reviews = get_dealer_reviews_from_cf(url, dealer_id)
        #if dealer_reviews:
        url_to_get_name = f"https://us-south.functions.appdomain.cloud/api/v1/web/832fded6-63ea-4e95-8f65-b5cd7ce11246/dealership-package/get-dealership?id={dealer_id}"
        dealership_object = get_dealers_from_cf(url_to_get_name)
        dealership_name = dealership_object[0].full_name
        context['reviews'] = dealer_reviews
        context['dealership_name'] = dealership_name
        context['dealer_id'] = dealer_id
        #return HttpResponse(response)
        return render(request, 'djangoapp/dealer_details.html', context) 
    

# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    context = {}
    dealer_url = "https://us-south.functions.appdomain.cloud/api/v1/web/832fded6-63ea-4e95-8f65-b5cd7ce11246/dealership-package/get-dealership"    
    dealer = get_dealer_by_id(dealer_url, dealer_id)
    context["dealer"] = dealer
    if request.method == 'GET':
        # Get cars for the dealer
        cars = CarModel.objects.all()
        context["cars"] = cars
        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == 'POST':
        if request.user.is_authenticated:
            username = request.user.username
            car_id = request.POST.get("car")
            car = CarModel.objects.get(pk=car_id)

            payload = {
                "time": datetime.utcnow().isoformat(),
                "name": username,
                "dealership": dealer_id, #dealer.full_name,
                "id": car_id,
                "review": request.POST.get("content"),
                "purchase": request.POST.get("purchasecheck", False),
                "purchase_date": request.POST.get("purchasedate"),
                "car_make": car.make.name,
                "car_model": car.name,
                "car_year": int(car.year.strftime("%Y")),
                "sentiment":"",}

            new_payload = {"review": payload}            
            review_post_url = "https://us-south.functions.appdomain.cloud/api/v1/web/832fded6-63ea-4e95-8f65-b5cd7ce11246/dealership-package/post-review"
            post_request(review_post_url, new_payload, dealer_id=dealer_id)
            
            return redirect("djangoapp:dealer_details", dealer.id) #dealer_id=dealer_id)
