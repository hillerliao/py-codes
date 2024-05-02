import requests
import json
import random
import re
import time
from datetime import datetime, timedelta
import configparser

# get pushplus token
def get_pushplus_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['pushplus']['pushplus_token'], config['pushplus']['pushplus_url']
pushplus_token, pushplus_url = get_pushplus_config()


def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def make_request(url, data):
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print('Error making request:', e)
        return None

def find_cards(anki_api_url):
    find_cards_data = {
        'action': 'findNotes',
        'version': 6,
        'params': {
            'query': 'deck:0_JLPT'
            # 'query': 'deck:wrong'
        }
    }
    return make_request(anki_api_url, find_cards_data)

def get_random_card_id(cards):
    if cards:
        return random.choice(cards)
    else:
        return None

def get_card_data(anki_api_url, card_id):
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
    anki_api_url = 'http://localhost:8765'
    try:
        cards_response = find_cards(anki_api_url)
        card_id = get_random_card_id(cards_response.get('result', []))
        card_data_response = get_card_data(anki_api_url, card_id)
        if card_data_response:
            card_content = card_data_response['result'][0]['fields']['Front']['value']
            card_content_stripped = remove_html_tags(card_content)
            send_notification(card_content_stripped)
        else:
            print('No card data found')
    except Exception as e:
        print('Error fetching and displaying card:', e)

fetch_and_display_card()