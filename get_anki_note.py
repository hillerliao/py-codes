import requests
import json
import random
import re
import time
from datetime import datetime, timedelta
import configparser

# get pushplus token
def get_pushplus_config():
    """
    Reads the 'config.ini' file to retrieve the pushplus token and URL.

    Returns:
        Tuple: A tuple containing the pushplus token and pushplus URL.
    """    
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['pushplus']['pushplus_token'], config['pushplus']['pushplus_url']
pushplus_token, pushplus_url = get_pushplus_config()


def remove_html_tags(text):
    """
    Removes HTML tags from the given text.

    Parameters:
        text (str): The text containing HTML tags.

    Returns:
        str: The text with HTML tags removed.
    """    
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def make_request(url, data):
    """
    Makes a request to the provided URL with the given data.

    Parameters:
        url (str): The URL to make the request to.
        data (dict): The JSON data to send in the request.

    Returns:
        dict or None: The JSON response from the request if successful, None otherwise.
    """    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print('Error making request:', e)
        return None

def find_cards(anki_api_url):
    """
    Finds cards based on the Anki API URL provided.

    Parameters:
        anki_api_url (str): The URL of the Anki API.

    Returns:
        list or None: The response data from the Anki API for finding cards.
    """
    find_cards_data = {
        'action': 'findNotes',
        'version': 6,
        'params': {
            'query': 'deck:0_JLPT'
        }
    }
    return make_request(anki_api_url, find_cards_data)

def get_random_card_id(cards):
    """
    Get a random card ID from a list of cards.

    Parameters:
        cards (list): A list of cards. 
    Returns:
        str or None: A randomly chosen card ID from the list of cards, or None if the list is empty.
    """    
    if cards:
        return random.choice(cards)
    else:
        return None

def get_card_data(anki_api_url, card_id):
    """
    Retrieves the data of a specific card from the Anki API.

    Parameters:
        anki_api_url (str): The URL of the Anki API.
        card_id (str): The ID of the card to retrieve.

    Returns:
        dict or None: The data of the card if the card_id is provided, None otherwise.
    """    
    if card_id:
        notes_info_data = {
            'action': 'notesInfo',
            'version': 6,
            'params': {
                'notes': [card_id],
            },
        }
        return make_request(anki_api_url, notes_info_data)
    else:
        return None

def send_notification(card_content_stripped):
    """
    Sends a notification with the given card content stripped.

    Parameters:
        card_content_stripped (str): The stripped content of the card.

    Returns:
        None
    """    
    payload = {
        "token": pushplus_token,
        "content": card_content_stripped,
        "template": "txt",
        "topic": "",
        "version": "personal"
    }
    response = requests.post(pushplus_url, json=payload)
    if response.status_code == 200:
        print("Notification sent successfully")
    else:
        print(f"Failed to send notification. Status code: {response.status_code}")



def fetch_and_display_card():
    """
    Fetches a random card from the Anki API. And then send the front content to PushPlus.

    Parameters:
        None

    Returns:
        None

    Raises:
        Exception: If there is an error fetching or displaying the card.
    """    
    anki_api_url = 'http://localhost:8765'
    try:
        cards_response = find_cards(anki_api_url)
        card_id = get_random_card_id(cards_response.get('result', []))
        card_data_response = get_card_data(anki_api_url, card_id)

        if card_data_response:
            # check if card is buried. If so, fetch another one.
            card_tags = card_data_response['result'][0]['tags']
            if card_tags and '1' in card_tags:
                card_id = get_random_card_id(cards_response.get('result', []))
                card_data_response = get_card_data(anki_api_url, card_id)
                if not card_data_response:
                    print('No card data found after retrying')
                    return

            card_content = card_data_response['result'][0]['fields']['Front']['value']
            card_content_stripped = remove_html_tags(card_content)
            send_notification(card_content_stripped)
        else:
            print('No card data found')
    except Exception as e:
        print('Error fetching and displaying card:', e)

fetch_and_display_card()