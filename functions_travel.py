# Importing necessary libraries
import pandas as pd  # For data manipulation and analysis
import json  # For working with JSON data
import re  # For regular expressions
import ast  # For safely evaluating strings containing Python expressions
import openai  # For interacting with the OpenAI API

def initialize_conversation():
    '''
    Returns a list [{"role": "system", "content": system_message}]
    '''
    
    delimiter = "####"
    example_user_req = {'Number of Travelers': '2','Duration of Stay': '5 days','Interests': 'Adventure, Beaches'}

    # System message providing instructions and examples for user interaction
    system_message = f"""
    Welcome to TravelAI! Your intelligent travel assistant for exploring the best destinations in India.
    
    As your travel assistant, my goal is to help you plan the perfect trip based on your preferences and requirements.
    
    Your journey with TravelAI begins by providing me with some key information about your travel preferences. We will then use this information to tailor personalized recommendations just for you.
    
    Your input will help us create a profile that includes the following details:
    - Number of Travelers: The total number of people traveling with you.
    - Duration of Stay: The number of days you plan to stay at your destination.
    - Interests: Your interests or preferred activities during your trip (e.g., Adventure, Beaches, Cultural Exploration, Wildlife Safari, etc.).
    
    Here are some instructions to ensure we provide you with the best recommendations:
    {delimiter}
    - Provide accurate information to help us personalize your recommendations.
    - Feel free to share any specific preferences or requirements you have for your trip.
    {delimiter}
    
    To assist you effectively, we'll follow a structured approach:
    {delimiter} Thought 1: Gathering your travel preferences and requirements.
    We'll start by understanding the number of travelers, duration of stay, and your interests or preferred activities during the trip.
    Once we have this information, we can proceed to the next step.
    {delimiter}
    
    {delimiter}Thought 2: Recommending destinations based on your preferences.
    Using the information gathered in the first step, we'll suggest destinations that align with your interests and other requirements.
    You'll have the opportunity to review and provide feedback on these recommendations.
    {delimiter}
    
    {delimiter}Thought 3: Refining recommendations and finalizing your travel itinerary.
    After receiving your feedback, we'll refine our recommendations further to ensure they meet your expectations.
    You can ask questions or request modifications to tailor the itinerary according to your preferences.
    {delimiter}
    
    Your journey with TravelAI begins now! Please provide the requested information to get started.
    
    Here is a sample conversation to give you an idea of how our interaction will proceed:
    User: "Hi, I'm planning a trip to India."
    Assistant: "Welcome! I'm excited to help you plan your trip. To get started, could you please provide me with some details, such as the number of travelers, duration of stay, and your interests or preferred activities during the trip?"
    User: "Sure, there will be two travelers, we plan to stay for 7 days, and we're interested in adventure activities and exploring cultural sites."
    Assistant: "{example_user_req}"
    {delimiter}
    
    Let's begin your travel journey! Please share your travel preferences, and we'll take it from there.
    """

    conversation = [{"role": "system", "content": system_message}]  # Initializing conversation list with system message
    return conversation


def get_chat_model_completions(messages):
    # Function to generate bot response using OpenAI's Chat Completion API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0,  # Degree of randomness of the model's output
        max_tokens=300  # Maximum number of tokens in the response
    )
    return response.choices[0].message["content"]


def moderation_check(user_input):
    # Function to check moderation of user input using OpenAI's Moderation API
    response = openai.Moderation.create(input=user_input)
    moderation_output = response["results"][0]
    if moderation_output["flagged"] == True:
        return "Flagged"  # Return "Flagged" if input is flagged for moderation
    else:
        return "Not Flagged"  # Return "Not Flagged" if input is not flagged


def intent_confirmation_layer(response_assistant):
    # Function to confirm intent of assistant's response using a predefined prompt
    delimiter = "####"
    prompt = f"""
    You are a senior evaluator with an eye for detail.
    You are provided with an input from the TravelAI system and need to evaluate whether it contains the necessary keys and their values are filled correctly.
    The keys to be evaluated are: 'City', 'Ratings', 'Best_time_to_visit', 'City_desc' (from city.csv) and 'Place', 'Ratings', 'Distance', 'Place_desc' (from places.csv).
    The values for all keys should be appropriate based on the context of a travel destination.
    Output 'Yes' if the input contains the dictionary with the values correctly filled for all keys. Otherwise, output 'No'.

    Here is the input: {response_assistant}
    Provide a one-word output: Yes/No.
    """

    confirmation = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        temperature=0  # Temperature parameter controls randomness of the model's output
    )

    return confirmation["choices"][0]["text"]


def dictionary_present(response):
    # Function to extract and return the travel destination dictionary from the input using a predefined prompt
    delimiter = "####"
    user_req = {'City': 'Sample City', 'Ratings': '4.5', 'Best_time_to_visit': 'Spring', 'City_desc': 'Description of the city', 'Place': 'Sample Place', 'Distance': '50 km', 'Place_desc': 'Description of the place'}
    prompt = f"""You are a travel expert analyzing TravelAI's output.
            You need to check if a dictionary representing travel destination details is present in the input.
            The dictionary should have the following keys and corresponding values: {user_req}.
            Your task is to extract and return only the travel destination dictionary from the input.
            The output should match the format specified in the prompt.
            Ensure that the output contains the exact keys and values as present in the input.

            Here are some sample input-output pairs for better understanding:
            {delimiter}
            input: - City: Sample City - Ratings: 4.5 - Best_time_to_visit: Spring - City_desc: Description of the city - Place: Sample Place - Distance: 50 km - Place_desc: Description of the place
            output: {{'City': 'Sample City', 'Ratings': '4.5', 'Best_time_to_visit': 'Spring', 'City_desc': 'Description of the city', 'Place': 'Sample Place', 'Distance': '50 km', 'Place_desc': 'Description of the place'}}

            input: {{'City': Sample City, 'Ratings': 4.5, 'Best_time_to_visit': Spring, 'City_desc': Description of the city, 'Place': Sample Place, 'Distance': 50 km, 'Place_desc': Description of the place}}
            output: {{'City': 'Sample City', 'Ratings': '4.5', 'Best_time_to_visit': 'Spring', 'City_desc': 'Description of the city', 'Place': 'Sample Place', 'Distance': '50 km', 'Place_desc': 'Description of the place'}}

            input: Here is your destination details - City: Sample City, Ratings: 4.5, Best_time_to_visit: Spring, City_desc: Description of the city, Place: Sample Place, Distance: 50 km, Place_desc: Description of the place
            output: {{'City': 'Sample City', 'Ratings': '4.5', 'Best_time_to_visit': 'Spring', 'City_desc': 'Description of the city', 'Place': 'Sample Place', 'Distance': '50 km', 'Place_desc': 'Description of the place'}}
            {delimiter}

            Input: {response}

            """
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=2000
        # temperature=0.3,
        # top_p=0.4
    )
    return response["choices"][0]["text"]

# Function to extract dictionary from a string using regular expressions and safe evaluation
def extract_dictionary_from_string(string):
    regex_pattern = r"\{[^{}]+\}"  # Regular expression pattern to match a dictionary

    dictionary_matches = re.findall(regex_pattern, string)  # Find all matches of dictionary pattern in the string

    # Extract the first dictionary match and convert it to lowercase
    if dictionary_matches:
        dictionary_string = dictionary_matches[0]
        dictionary_string = dictionary_string.lower()

        # Convert the dictionary string to a dictionary object using ast.literal_eval()
        dictionary = ast.literal_eval(dictionary_string)
    return dictionary

def compare_travel_destinations_with_user(user_req_string):
    # Load the datasets
    city_df = pd.read_csv('dataset/city.csv')  # Load city dataset
    places_df = pd.read_csv('dataset/places.csv')  # Load places dataset

    # Filter destinations based on user requirements (if applicable)
    user_requirements = extract_dictionary_from_string(user_req_string)  # Extract user requirements from string
    filtered_cities = city_df.copy()  # Initialize filtered cities dataframe
    filtered_places = places_df.copy()  # Initialize filtered places dataframe

    # Filter city dataframe based on user requirements
    for key, value in user_requirements.items():
        if key in filtered_cities.columns:
            filtered_cities = filtered_cities[filtered_cities[key] == value]
        if key in filtered_places.columns:
            filtered_places = filtered_places[filtered_places[key] == value]

    # Combine the filtered datasets
    combined_destinations = pd.concat([filtered_cities, filtered_places], ignore_index=True)

    # Convert combined destinations dataframe to JSON format
    return combined_destinations.to_json(orient='records')

# Function to validate destination recommendations based on predefined criteria
def recommendation_validation(destination_recommendation):
    data = json.loads(destination_recommendation)  # Load JSON data
    data1 = []  # Initialize list for validated recommendations
    for i in range(len(data)):
        if data[i]['Ratings'] == '4.5' and 'Best_time_to_visit' in data[i] and 'Place_desc' in data[i]:
            data1.append(data[i])  # Append recommendation to validated recommendations list if criteria are met

    return data1

def initialize_conv_reco(destinations):
    # Function to initialize conversation for destination recommendations
    system_message = f"""
    Welcome to TravelAI! 🌍✈️🧳

    You are now connected to TravelAI, your ultimate travel companion.
    TravelAI is here to assist you with information about various travel destinations.
    We have a diverse range of destinations in our catalogue.
    
    Let's get started! Please feel free to ask about any destination, and I'll provide you with detailed information to make your travel decisions easier.
    """
    conversation = [{"role": "system", "content": system_message }]  # Initializing conversation with system message
    return conversation
