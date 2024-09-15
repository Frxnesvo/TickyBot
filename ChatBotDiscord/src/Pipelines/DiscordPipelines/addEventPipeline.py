from DiscordManager import DiscordManager
from Api.EventApi import EventApi
from datetime import datetime
from zoneinfo import ZoneInfo

formato_data = "%Y-%m-%d %H:%M"
cet=ZoneInfo('Europe/Berlin')

def run(client: DiscordManager):          #TODO: per essere perfetto dovrei farlo transazionale
    body=client.body
    data=client.data
    api=EventApi()
    now_cet = datetime.now(cet)
    titolo = next(item for item in data['options'] if item['name'] == 'titolo')['value']
    hour = next(item for item in data['options'] if item['name'] == 'hour')['value']
    minute = next((item for item in data['options'] if item['name'] == 'minute'), {'value': 0})['value']
    day = next((item for item in data['options'] if item['name'] == 'day'), {'value': now_cet.day})['value']
    month = next((item for item in data['options'] if item['name'] == 'month'), {'value': now_cet.month})['value']
    year = next((item for item in data['options'] if item['name'] == 'year'), {'value': now_cet.year})['value']
    
    user_id = body['member']['user']['id']
    
    # Converti i parametri in un oggetto datetime
    try:
        data_inizio = datetime(year, month, day, hour, minute).strftime(formato_data)
    except ValueError as e:
        client.invia_follow_up(body['token'], f"Errore nella creazione della data dell'evento: {str(e)} ❌​")
        return
    now = now_cet.strftime(formato_data)
    if data_inizio < now:
        client.invia_follow_up(body['token'], "Non puoi aggiungere un evento nel passato ❌​")
        return
    data_cet= datetime(year, month, day, hour, minute, tzinfo=cet)
    response=api.addEventToDynamoDB(user_id, titolo, data_cet.strftime(formato_data))
    if response['statusCode'] == 200:
        machine_response= api.startStateMachine(titolo,user_id, data_cet.isoformat())
        print(machine_response)
        if machine_response['statusCode'] == 200:
            client.invia_follow_up(body['token'], response['body'])
        else:
            client.invia_follow_up(body['token'], machine_response['body'])
    else:
        client.invia_follow_up(body['token'], response['body'])