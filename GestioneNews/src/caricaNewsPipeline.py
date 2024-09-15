from UploadNewsApi import UploadNewsApi
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import requests

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
HEADERS = {
        'Authorization': f'Bot {DISCORD_TOKEN}',
        'Content-Type': 'application/json',
    }

time_italy_now= datetime.now(ZoneInfo("Europe/Rome")).strftime('%H:%M')
embed={
    "title": f'**NOTIZIE FRESCHE FRESCHE DELLE {time_italy_now}!**',  # Titolo generale dell'embed
    "color": 3447003,  # Colore dell'embed
    "fields": []  # Lista vuota che sarà riempita con i campi delle notizie
    }

def run():
    api= UploadNewsApi()
    newsList= api.getNews()
    activeChannels= api.getActiveChannelsIds()
    for news in newsList:
        embed['fields'].append({
            "name": news['title'],  # Titolo della notizia
            "value": f"[Leggi di più]({news['link']})",  # Link alla notizia
            "inline": False  # Ogni notizia è su una riga diversa
        })
    payload= {'embeds': [embed]}
    for id, community in activeChannels:
        response= requests.post(f"https://discord.com/api/v9/channels/{id}/messages", headers=HEADERS, json=payload)
        print(response.status_code)  #TODO: Da rimuovere
        if community=='true':
            deleteLastMessage(id)
            createDiscordThread(id, response.json()['id'])
            publishMessage(id, response.json()['id'])


def deleteLastMessage(channel_id):
    response = requests.get(f"https://discord.com/api/v9/channels/{channel_id}/messages", headers=HEADERS)
    r=response.json()
    count=0
    lastMessageId=None
    for message in r:
        lastMessageId=message['id']
        #se è inviato da un bot lo conto
        if message['author'].get('bot',False):
            count+=1
    
    if count>=6:
        requests.delete(f"https://discord.com/api/v9/channels/{channel_id}/messages/{lastMessageId}", headers=HEADERS)


def createDiscordThread(channel_id, message_id):
    payload = {
        'name': f'News {time_italy_now}',
        'auto_archive_duration': 1440, # 24 ore
        'type': 11,
    }
    response= requests.post(f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/threads", headers=HEADERS, json=payload)


def publishMessage(channel_id, message_id):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/crosspost"
    response = requests.post(url, headers=HEADERS)