from datetime import datetime
import json
import os
import requests
from Api.NotifyEventsApi import NotifyEventsApi


DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
HEADERS = {
        'Authorization': f'Bot {DISCORD_TOKEN}',
        'Content-Type': 'application/json',
    }

def run(event):
    api= NotifyEventsApi()
    user_id = event['user_id']
    event_name = event['event_name']
    event_time = event['event_time']
    notifyEvent(user_id, event_name, event_time)
    api.deleteEvent(user_id, event_name)
    


def notifyEvent(user_id, event_name, event_time):
    output_data = datetime.fromisoformat(event_time).strftime('%H:%M')
    message = f"📅Ricordati di: '{event_name}' alle ore {output_data} (dovrebbe essere proprio ora😉)"
     # Crea un canale DM con l'utente
    dm_payload = json.dumps({'recipient_id': user_id})
    dm_response = requests.post("https://discord.com/api/v8/users/@me/channels", data=dm_payload, headers=HEADERS)
    if dm_response.status_code != 200:
        print(f"Errore nella creazione del canale DM: {dm_response.text}")   #TODO: da loggare
        return
    dm_channel= dm_response.json()
     # Invia il DM
    message_payload = json.dumps({'content': message})
    message_url = f"https://discord.com/api/v8/channels/{dm_channel['id']}/messages"
    message_response = requests.post(message_url, data=message_payload, headers=HEADERS)  #TODO: potenzialmente loggare la risposta