from zoneinfo import ZoneInfo
from DiscordManager import DiscordManager
from Api.EventApi import EventApi

formato_data = "%Y-%m-%d %H:%M"
cet=ZoneInfo('Europe/Berlin')

def run(client: DiscordManager):   #TODO: per essere perfetto dovrei farlo transazionale
    body=client.body
    data=client.data
    api=EventApi()
    titolo = next(item for item in data['options'] if item['name'] == 'titolo')['value']

    user_id = body['member']['user']['id']
    response=api.deleteEventFromDynamoDB(user_id, titolo)
    if response['statusCode'] == 200:
        print("STO PER FARE LA STOP STATE MACHINE")
        machine_response= api.stopStateMachine(titolo,user_id)
        print("HO FATTO LA STOP STATE MACHINE CON RISPOSTA:", machine_response['statusCode'])
        if machine_response['statusCode'] == 200:
            client.invia_follow_up(body['token'], response['body'])
        else:
            client.invia_follow_up(body['token'], machine_response['body'])
    else:
        client.invia_follow_up(body['token'], response['body'])
