import os
import requests

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
HEADERS = {
        'Authorization': f'Bot {DISCORD_BOT_TOKEN}',
        'Content-Type': 'application/json',
    }

def run(event):
    channel_id = event['channel_id']
    message_id = event['message_id']
    message_url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}"

    response = requests.get(message_url, headers=HEADERS)
    if response.status_code != 200:
        return
    
    message_data = response.json()
    embed = message_data['embeds'][0]

    # Modifica l'embed per segnalare che il sondaggio è scaduto
    embed['color'] = 0xFF0000  # Colore Rosso
    embed['description'] = "SONDAGGIO SCADUTO"

    # Prepara il payload per aggiornare il messaggio
    payload = {
        "embeds": [embed],
        "components": []  # Rimuovi tutti i componenti interattivi, come bottoni
    }
    # Aggiorna il messaggio su Discord
    update_response = requests.patch(message_url, headers=HEADERS, json=payload)