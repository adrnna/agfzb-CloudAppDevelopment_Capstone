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
            #return render(request, 'djangoapp/index.html', context)
            url = "https://us-south.functions.appdomain.cloud/api/v1/web/832fded6-63ea-4e95-8f65-b5cd7ce11246/dealership-package/get-dealership"
        # Get dealers from the URL 
        dealerships = get_dealers_from_cf(url, **kwargs)
        # Concat all dealer's short name
        dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Return a list of dealer short name
        return HttpResponse(dealer_names)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        url = f"https://us-south.functions.appdomain.cloud/api/v1/web/832fded6-63ea-4e95-8f65-b5cd7ce11246/dealership-package/get-review/review?dealerId={dealer_id}"
        # Get dealer reviews from the URL
        dealer_reviews = get_dealer_reviews_from_cf(url, dealer_id)
        if dealer_reviews:
            reviews = []
            for review in dealer_reviews:
                review_info = f"Review: {review.review}\nSentiment: {review.sentiment}"
                reviews.append(review_info)
            response = "\n\n".join(reviews)
            return HttpResponse(response)
        else:
            # If no reviews found for the given dealer, return a 404 response
            return HttpResponse("No reviews found for this dealer.", status=404)


# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    if request.method == "POST":
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Create the review data
        review = {
            "time": datetime.utcnow().isoformat(),
            "name": request.user.username,
            "dealership": dealer_id,
            "review": request.POST.get("review"),
            "purchase": request.POST.get("purchase")
            # Add any other attributes as needed
        }
        
        # Create the JSON payload
        json_payload = {
            "review": review
        }
        
        # Prepare the URL for the review-post cloud function
        url = f"https://us-south.functions.appdomain.cloud/api/v1/web/832fded6-63ea-4e95-8f65-b5cd7ce11246/dealership-package/review-post/review"
        
        # Make the POST request to add the review
        response = post_request(url, json_payload, dealerId=dealer_id)
        
        # Check the response and return an appropriate HTTP response
        if response.get("error"):
            return JsonResponse({"error": response["error"]}, status=400)
        else:
            return JsonResponse({"message": "Review added successfully"}, status=201)
    
    # Return a 405 Method Not Allowed if the request method is not POST
    return HttpResponseNotAllowed(["POST"])

