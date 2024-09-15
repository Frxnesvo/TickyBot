from DiscordManager import DiscordManager
from Api.EventApi import EventApi

def run(client: DiscordManager):   
    body=client.body
    api=EventApi()
    user_id = body['member']['user']['id']
    events=api.getUserEvents(user_id)
    if not events:
        client.invia_follow_up(body['token'], "Non hai eventi in programma")
        return
    embed = {
            "title": "I tuoi eventi",
            "description": "💻Ecco una lista dei tuoi eventi imminenti:",
            "color": 0x00ff00,
            "fields": [{"name": event['title'], "value": f"Data: {event['datainizio']}", "inline": False} for event in events]
    }
    message_payload = {
        "embeds": [embed],
        "flags": 1 << 6
    }
    client.invia_follow_up(body['token'], message_payload)