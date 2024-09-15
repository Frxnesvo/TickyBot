from DiscordManager import DiscordManager
from Api.SentimentApi import SentimentApi
import datetime
import pytz
import requests
api=SentimentApi()

time_pattern='%Y-%m-%d %H:%M:%S'

def run(client:DiscordManager):
    body = client.body
    if 'guild_id' not in body:
        client.invia_follow_up(body['token'], "Non puoi eseguire questo comando nella chat privata ❌")
        return
    server_id = body['guild_id']
    durata = next((option['value'] for option in body['data']['options'] if option['name'] == 'durata'), None)
    exist, time= api.getServerStatus(server_id)
    if exist:
        endTime = datetime.datetime.strptime(time, time_pattern)
        endTime= pytz.timezone("Europe/Rome").localize(endTime) #aggiunge il fuso orario
        now = datetime.datetime.now(pytz.timezone("Europe/Rome"))
        if now < endTime:
            client.invia_follow_up(body['token'], "Il server è già stato analizzato in passato. Per rianalizzarlo attendere la data di fine analisi 🕟")
            return
    older_than_date = datetime.datetime.now(pytz.timezone("Europe/Rome")).replace(tzinfo=None) - datetime.timedelta(days=int(durata))
    messages= fetchMessages(server_id, older_than_date, client)
    if not messages:
        client.invia_follow_up(body['token'], "Non ci sono messaggi da analizzare")
        return
    chunks= api.divideMessagesInChunks(messages)
    sentiment, scores= api.analyzeServerSentiment(chunks)
    strScores=', '.join([f"{val:.2f}" for key, val in scores.items()])
    print(f"Sentiment prevalente: {sentiment} e punteggi medi: {scores}")  #FIXME: da loggare
    response= api.generateCompletionMessage(sentiment, strScores)
    if response['statusCode'] == 200:
        add_response= api.addCalculationToDynamoDB(server_id, durata)
        if add_response['statusCode'] == 200:
            client.invia_follow_up(body['token'], response['body'])
            return
    client.invia_follow_up(body['token'], "Errore durante l'analisi del server ❌")


def fetchMessages(server_id, older_than_date,client:DiscordManager):
    '''
    Recupera tutti i messaggi inviati in un server Discord fino a una certa data.
    Ritorna una lista di stringhe contenente i messaggi.
    '''
    
    channel_ids = get_text_channel_ids(server_id,client.HEADERS)
    
    all_messages = []
    
    for channel_id in channel_ids:
        last_message_id = None
        while True:
            params = {
                "limit": 100
            }
            if last_message_id:
                params["before"] = last_message_id
                
            response = requests.get(f"https://discord.com/api/v9/channels/{channel_id}/messages", headers=client.HEADERS, params=params)
            messages = response.json()
            
            if not messages:
                break
                
            for message in messages:
                message_time = datetime.datetime.strptime(message['timestamp'], '%Y-%m-%dT%H:%M:%S.%f%z')
                message_time = message_time.astimezone(pytz.timezone("Europe/Rome")).replace(tzinfo=None)  # Converte il timestamp in ora italiana
                if message['author'].get('bot', False) or len(message['content'])<=0: # Ignora i messaggi dei bot e i messaggi di chi entra nel server (non contengono testo)
                    continue
                if message_time < older_than_date:
                    break
                all_messages.append(message['content'])
                
            last_message_id = messages[-1]['id']
    
    return all_messages

def get_text_channel_ids(server_id, headers):
    '''
    Recupera gli ID dei canali di testo di un server Discord.
    Ritorna una lista di stringhe contenente gli ID.
    '''

    url = f"https://discord.com/api/v9/guilds/{server_id}/channels"
    
    response = requests.get(url, headers=headers)
    channels = response.json()
    
    text_channel_ids = [channel['id'] for channel in channels if channel['type'] == 0]  # 0 è il tipo per i canali di testo
    return text_channel_ids