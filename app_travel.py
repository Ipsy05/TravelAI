# Importing necessary libraries
from flask import Flask, redirect, url_for, render_template, request
from functions_travel import initialize_conversation, initialize_conv_reco, get_chat_model_completions, moderation_check, intent_confirmation_layer, dictionary_present, compare_travel_destinations_with_user, recommendation_validation
import openai
import time  # Importing the time module for rate limit handling

# Setting up the OpenAI API key
openai.api_key = open("GPT_API_key.txt", "r").read().strip()

# Creating a Flask web application instance
app = Flask(__name__)

# Initializing conversation variables
conversation_bot = []  # Stores conversation messages for display
conversation = initialize_conversation()  # Initializes the conversation list
introduction = get_chat_model_completions(conversation)  # Generates initial response from the chatbot
conversation_bot.append({'bot': introduction})  # Appends initial bot response to the conversation display
top_3_destinations = None  # Initializes top destinations variable

# Route for the home page
@app.route("/")
def default_func():
    global conversation_bot, conversation, top_3_destinations
    return render_template("index_invite_travel.html", name_xyz=conversation_bot)

# Route for ending the conversation
@app.route("/end_conv", methods=['POST', 'GET'])
def end_conv():
    global conversation_bot, conversation, top_3_destinations
    # Resetting conversation variables
    conversation_bot = []
    conversation = initialize_conversation()
    introduction = get_chat_model_completions(conversation)
    conversation_bot.append({'bot': introduction})
    top_3_destinations = None
    return redirect(url_for('default_func'))

# Route for processing user input and interacting with the chatbot
@app.route("/invite", methods=['POST'])
def invite():
    global conversation_bot, conversation, top_3_destinations, conversation_reco

    # Getting user input from the form
    user_input = request.form["user_input_message"]

    # Adding prompt for travel assistant for India
    prompt = 'Remember your system message and that you are a travel assistant for India. So, you only assist with travel-related queries for destinations in India.'

    try:
        # Handling rate limit error with a delay
        moderation = moderation_check(user_input)
    except openai.error.RateLimitError as e:
        # If RateLimitError is encountered, wait for 20 seconds and retry
        time.sleep(20)
        moderation = moderation_check(user_input)  # Retry the moderation check

    # Redirect to end conversation if message is flagged
    if moderation == 'Flagged':
        return redirect(url_for('end_conv'))

    # Handling user input and generating bot response
    if top_3_destinations is None:
        conversation.append({"role": "user", "content": user_input + prompt})
        conversation_bot.append({'user': user_input})

        response_assistant = get_chat_model_completions(conversation)

        moderation = moderation_check(response_assistant)
        if moderation == 'Flagged':
            return redirect(url_for('end_conv'))

        confirmation = intent_confirmation_layer(response_assistant)

        moderation = moderation_check(confirmation)
        if moderation == 'Flagged':
            return redirect(url_for('end_conv'))

        if "No" in confirmation:
            conversation.append({"role": "assistant", "content": response_assistant})
            conversation_bot.append({'bot': response_assistant})
        else:
            response = dictionary_present(response_assistant)

            moderation = moderation_check(response)
            if moderation == 'Flagged':
                return redirect(url_for('end_conv'))

            conversation_bot.append({'bot': "Thank you for providing all the information. Kindly wait, while I fetch the destinations: \n"})
            top_3_destinations = compare_travel_destinations_with_user(response)

            validated_reco = recommendation_validation(top_3_destinations)

            if len(validated_reco) == 0:
                conversation_bot.append({'bot': "Sorry, we do not have destinations that match your preferences. Please refine your preferences."})

            conversation_reco = initialize_conv_reco(validated_reco)
            recommendation = get_chat_model_completions(conversation_reco)

            moderation = moderation_check(recommendation)
            if moderation == 'Flagged':
                return redirect(url_for('end_conv'))

            conversation_reco.append({"role": "user", "content": "This is my user profile" + response})

            conversation_reco.append({"role": "assistant", "content": recommendation})
            conversation_bot.append({'bot': recommendation})

            print(recommendation + '\n')

    else:
        conversation_reco.append({"role": "user", "content": user_input})
        conversation_bot.append({'user': user_input})

        response_asst_reco = get_chat_model_completions(conversation_reco)

        moderation = moderation_check(response_asst_reco)
        if moderation == 'Flagged':
            return redirect(url_for('end_conv'))

        conversation.append({"role": "assistant", "content": response_asst_reco})
        conversation_bot.append({'bot': response_asst_reco})

    # Redirect to home page after processing user input
    return redirect(url_for('default_func'))

# Running the Flask app
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
