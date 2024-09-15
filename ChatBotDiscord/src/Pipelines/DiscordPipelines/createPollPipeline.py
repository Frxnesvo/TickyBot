from DiscordManager import DiscordManager
from Api.PollApi import PollApi
from datetime import datetime, timedelta, timezone
import pytz

def run(client: DiscordManager): 
    body=client.body
    if 'guild_id' not in body:
        client.invia_follow_up(body['token'], "Non puoi eseguire questo comando nella chat privata ❌")
        return
    data=client.data
    api=PollApi() 
    question = next(item for item in data['options'] if item['name'] == 'domanda')['value']
    answers = next(item for item in data['options'] if item['name'] == 'risposte')['value'].split(',')
    #togli gli spazi bianchi
    answers = [answer.strip() for answer in answers]
    duration = next((item['value'] for item in data['options'] if item['name'] == 'durata'), 5)


    if len(answers) < 2:
        client.invia_follow_up(body['token'], "Sono necessarie almeno due opzioni per creare un sondaggio")
    if len(set(answers)) < len(answers):
        client.invia_follow_up(body['token'], "Non puoi inserire opzioni duplicate")

    end_time = datetime.now(timezone.utc) + timedelta(minutes=duration)
    end_time_italy= end_time.astimezone(pytz.timezone('Europe/Rome'))
    formatted_end_time = end_time_italy.strftime('%Y-%m-%d %H:%M')
   
    embed = {
        "title": f"Sondaggio: {question}",
        "description": f"Scadenza: {formatted_end_time}",
        "color": 3447003,  # Colore dell'embed, esempio in HEX: 0x3498db
        "fields": [{"name": answer, "value": "Voti: 0"} for answer in answers]  # Inizializza i voti a 0
    }
    
    # Prepara i bottoni per le opzioni di risposta
    buttons = [{
        "type": 2,  # Tipo per i bottoni
        "label": answer,
        "style": 1,  # Stile Blu
        "custom_id": f"buttonpoll:{answer}"  # custom_id univoco per l'opzione
    } for answer in answers]

    # Prepara il componente del messaggio con i bottoni
    components = [{
        "type": 1,  # Il tipo 1 indica che il componente è un'azione
        "components": buttons
    }]
    payload = {'embeds': [embed], 'components': components}
    status_code, response_json= client.invia_follow_up(body['token'], payload)
    if status_code == 200:
        machine_response= api.startStepMachine(end_time.strftime('%Y-%m-%dT%H:%M:%S+00:00'), body['channel_id'], response_json['id'])
