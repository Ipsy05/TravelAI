# Importing necessary functions from the 'functions_travel' module
from functions_travel import initialize_conversation, initialize_conv_reco, get_chat_model_completions, moderation_check, intent_confirmation_layer, dictionary_present, compare_travel_destinations_with_user, recommendation_validation

# Importing the 'openai' module for accessing OpenAI's APIs
import openai

# Reading the OpenAI API key from a file and setting it as the API key for authentication
openai.api_key = open("GPT_API_key.txt", "r").read().strip()

# Function to manage the dialogue between the user and the assistant
def dialogue_management_system():
    conversation = initialize_conversation()  # Initialize conversation with system message
    introduction = get_chat_model_completions(conversation)  # Generate introduction message using OpenAI's Chat Completion API
    print(introduction + '\n')  # Print the introduction message
    top_3_destinations = None  # Initialize variable to store top 3 destinations
    user_input = ''  # Initialize variable to store user input

    # Loop to continue dialogue until the user inputs 'exit'
    while(user_input.lower() != "exit"):
        user_input = input("")  # Get user input from the command line

        # Check if user input is flagged for moderation
        moderation = moderation_check(user_input)
        if moderation == 'Flagged':
            print("Sorry, this message has been flagged. Please restart your conversation.")
            break  # Exit the loop if user input is flagged

        # If top 3 destinations are not yet fetched
        if top_3_destinations is None:
            conversation.append({"role": "user", "content": user_input})  # Append user input to conversation

            response_assistant = get_chat_model_completions(conversation)  # Generate assistant's response using OpenAI's Chat Completion API

            # Check if assistant's response is flagged for moderation
            moderation = moderation_check(response_assistant)
            if moderation == 'Flagged':
                print("Sorry, this message has been flagged. Please restart your conversation.")
                break  # Exit the loop if assistant's response is flagged

            confirmation = intent_confirmation_layer(response_assistant)  # Confirm intent of assistant's response

            # Check if confirmation is flagged for moderation
            moderation = moderation_check(confirmation)
            if moderation == 'Flagged':
                print("Sorry, this message has been flagged. Please restart your conversation.")
                break  # Exit the loop if confirmation is flagged

            # If confirmation is negative, proceed with assistant's response
            if "No" in confirmation:
                conversation.append({"role": "assistant", "content": response_assistant})
                print("\n" + response_assistant + "\n")  # Print assistant's response
                print('\n' + confirmation + '\n')  # Print confirmation
            else:
                print("\n" + response_assistant + "\n")  # Print assistant's response
                print('\n' + confirmation + '\n')  # Print confirmation
                response = dictionary_present(response_assistant)  # Extract dictionary from assistant's response

                # Check if response is flagged for moderation
                moderation = moderation_check(response)
                if moderation == 'Flagged':
                    print("Sorry, this message has been flagged. Please restart your conversation.")
                    break  # Exit the loop if response is flagged

                print('\n' + response + '\n')  # Print extracted dictionary
                print("Thank you for providing all the information. Kindly wait, while I fetch the destinations: \n")  # Print acknowledgement message
                top_3_destinations = compare_travel_destinations_with_user(response)  # Compare travel destinations with user preferences

                # If no destinations match user preferences, print message and exit loop
                if top_3_destinations is None:
                    print("We are currently updating our data. Please check back later for travel recommendations.")
                    break

                validated_reco = recommendation_validation(top_3_destinations)  # Validate destination recommendations

                # If no validated recommendations, print message and exit loop
                if len(validated_reco) == 0:
                    print("Sorry, we do not have destinations that match your preferences. Please refine your preferences.")
                    break

                conversation_reco = initialize_conv_reco(validated_reco)  # Initialize conversation for recommendations
                recommendation = get_chat_model_completions(conversation_reco)  # Generate recommendations using OpenAI's Chat Completion API

                # Check if recommendation is flagged for moderation
                moderation = moderation_check(recommendation)
                if moderation == 'Flagged':
                    print("Sorry, this message has been flagged. Please restart your conversation.")
                    break  # Exit the loop if recommendation is flagged

                conversation_reco.append({"role": "user", "content": "This is my user profile" + response})  # Append user profile to conversation
                conversation_reco.append({"role": "assistant", "content": recommendation})  # Append recommendations to conversation

                print(recommendation + '\n')  # Print recommendations

        # If top 3 destinations are already fetched
        else:
            conversation_reco.append({"role": "user", "content": user_input})  # Append user input to conversation

            response_asst_reco = get_chat_model_completions(conversation_reco)  # Generate assistant's response using OpenAI's Chat Completion API

            # Check if assistant's response is flagged for moderation
            moderation = moderation_check(response_asst_reco)
            if moderation == 'Flagged':
                print("Sorry, this message has been flagged. Please restart your conversation.")
                break  # Exit the loop if assistant's response is flagged

            print('\n' + response_asst_reco + '\n')  # Print assistant's response
            conversation.append({"role": "assistant", "content": response_asst_reco})  # Append assistant's response to conversation

# Call the dialogue management system function to start the conversation
dialogue_management_system()
