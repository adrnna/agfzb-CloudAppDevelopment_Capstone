import requests
import json
from .models import CarDealer, DealerReview
from requests.auth import HTTPBasicAuth
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_watson.natural_language_understanding_v1 import Features,SentimentOptions
import time


# Create a `get_request` to make HTTP GET requests
# e.g., response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
#                                     auth=HTTPBasicAuth('apikey', api_key))
def get_request(url, **kwargs):
    # If argument contains API key
    api_key = kwargs.get("api_key")
    print("GET from {} ".format(url))
    
    response = None  # Set initial value for response
    
    try:
        if api_key:
            params = dict()
            params["text"] = kwargs["text"]
            params["version"] = kwargs["version"]
            params["features"] = kwargs["features"]
            params["return_analyzed_text"] = kwargs["return_analyzed_text"]
            response = requests.get(url, params=params, headers={'Content-Type': 'application/json'},
                                    auth=HTTPBasicAuth('apikey', api_key))
        else:
            # Call get method of requests library with URL and parameters
            response = requests.get(url, headers={'Content-Type': 'application/json'},
                                    params=kwargs)
    except:
        # If any error occurs
        print("Network exception occurred")
        return None  # Return None when exception occurs

    if response is not None:
        status_code = response.status_code
        print("With status {} ".format(status_code))
        json_data = json.loads(response.text)
        return json_data
    else:
        return None



# Create a `post_request` to make HTTP POST requests
# e.g., response = requests.post(url, params=kwargs, json=payload)
def post_request(url, payload, **kwargs):
    print(kwargs)
    print("POST to {} ".format(url))
    print(payload)
    response = requests.post(url, params=kwargs, json=payload)
    status_code = response.status_code
    print("With status {} ".format(status_code))
    json_data = json.loads(response.text)
    return json_data

# Create a get_dealers_from_cf method to get dealers from a cloud function
# def get_dealers_from_cf(url, **kwargs):
# - Call get_request() with specified arguments
# - Parse JSON results into a CarDealer object list
def get_dealers_from_cf(url, **kwargs):
    results = []
    state = kwargs.get("st")
    #print(state)
    dealer_id = kwargs.get("id")
    #print(dealer_id)
    if state:
        json_result = get_request(url, state = state)
    elif dealer_id:
        json_result = get_request(url, dealerId=dealer_id)
    else:
        json_result = get_request(url)
    # Call get_request with a URL parameter
    #json_result = get_request(url)
    if json_result:
        #print(json_result)
        # Get the row list in JSON as dealers
        #print(json_result)
        dealers = json_result#["body"]
        # For each dealer object
        for dealer in dealers:
            # Get its content in `doc` object
            dealer_doc = dealer#["doc"]
            # Create a CarDealer object with values in `doc` object
            dealer_obj = CarDealer(address=dealer_doc["address"], city=dealer_doc["city"], full_name=dealer_doc["full_name"],
                                   id=dealer_doc["id"], lat=dealer_doc["lat"], long=dealer_doc["long"],
                                   short_name=dealer_doc["short_name"],
                                   st=dealer_doc["st"], zip=dealer_doc["zip"])
            results.append(dealer_obj)
    return results

# Create a get_dealer_reviews_from_cf method to get reviews by dealer id from a cloud function
# def get_dealer_by_id_from_cf(url, dealerId):
# - Call get_request() with specified arguments
# - Parse JSON results into a DealerView object list

def get_dealer_by_id(url, dealer_id):
    # Append the dealer_id to the URL
    url = f"{url}?id={dealer_id}"
    
    # Call get_request with the modified URL and additional parameters
    json_result = get_request(url, dealerId=dealer_id)
    
    if json_result:
        # Get the dealer object from the JSON response
        dealer = json_result#["body"]
        
        # Get the content in the dealer object
        dealer_doc = dealer
        
        # Create a CarDealer object with values in the dealer object
        dealer_obj = CarDealer(
            address=dealer_doc["address"],
            city=dealer_doc["city"],
            full_name=dealer_doc["full_name"],
            id=dealer_doc["id"],
            lat=dealer_doc["lat"],
            long=dealer_doc["long"],
            short_name=dealer_doc["short_name"],
            st=dealer_doc["st"],
            zip=dealer_doc["zip"]
        )
        
        return dealer_obj
    
    return None


def get_dealer_reviews_from_cf(url, dealer_id):
    results = []
    if dealer_id:
        json_result = get_request(url, dealerId=dealer_id)
    if json_result:
        if "error" in json_result:
            # No reviews found for the given dealerId
            return []
        reviews = json_result  # Assuming reviews is a list of review objects
        for dealer_review in reviews:
            # Process the review object
            review_obj = DealerReview(dealership=dealer_review["dealership"],
                                      name=dealer_review["name"],
                                      purchase=dealer_review["purchase"],
                                      review=dealer_review["review"],
                                      purchase_date="",
                                      car_make="",
                                      car_model="",
                                      car_year="",
                                      sentiment="",
                                      id=dealer_review["id"])
            if "purchase_date" in dealer_review:
                review_obj.purchase_date = dealer_review["purchase_date"]
            if "car_make" in dealer_review:
                review_obj.car_make = dealer_review["car_make"]
            if "car_model" in dealer_review:
                review_obj.car_model = dealer_review["car_model"]
            if "car_year" in dealer_review:
                review_obj.car_year = dealer_review["car_year"]
            
            sentiment = analyze_review_sentiments(review_obj.review)
            review_obj.sentiment = sentiment
            results.append(review_obj)

    return results



# Create an `analyze_review_sentiments` method to call Watson NLU and analyze text
# def analyze_review_sentiments(text):
# - Call get_request() with specified arguments
# - Get the returned sentiment label such as Positive or Negative
def analyze_review_sentiments(dealerreview):
    url = "https://api.au-syd.natural-language-understanding.watson.cloud.ibm.com/instances/53ad00c4-a0ad-46a0-8026-5d79bc73c404/v1/analyze?version=2020-08-01"
    api_key = "qru5mU2inbdfwrQ0QVa3VYFb2dAnPtZBftgFKMT4Xe-x"
    
    if len(dealerreview) < 20:
        return {"error": "Not enough text for sentiment analysis"}
    
    response = get_request(url, text=dealerreview, api_key=api_key, version='2020-08-01', features={'sentiment'}, return_analyzed_text=True)
    
    if response and "error" not in response:
        sentiment = response["sentiment"]["document"]["label"]
        return sentiment
    elif response and "error" in response:
        error_message = response["error"]
        return {"error": error_message}
    else:
        return {"error": "Sentiment analysis request failed"}

    #API_KEY=""
    #NLU_URL='https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/b916e718-dd11-4cbc-ba5e-17d01c165a7f'
    #params = json.dumps({"text": dealerreview, "features": {"sentiment": {}}})
    #response = requests.post(NLU_URL,data=params,headers={'Content-Type':'application/json'},auth=HTTPBasicAuth("apikey", API_KEY))
    
    #print(response.json())
    #try:
    #    sentiment=response.json()['sentiment']['document']['label']
    #    return sentiment
    #except:
    #    return "neutral"
