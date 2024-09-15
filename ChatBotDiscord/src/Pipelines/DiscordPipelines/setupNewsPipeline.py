from DiscordManager import DiscordManager
from Api.NewsApi import NewsApi
import requests
import json

textChannelPayload = {"name": "BOT NEWS", "type": 0, "topic": "Notizie dal mondo per rimanere sempre aggiornati!"}
announcementChannelPayload = {"name": "BOT NEWS", "type": 5, "topic": "Notizie dal mondo per rimanere sempre aggiornati!"}

api=NewsApi()

def run(client:DiscordManager):
    body=client.body
    if 'guild_id' not in body:
        client.invia_follow_up(body['token'], "Non puoi eseguire questo comando nella chat privata ❌")
        return
    server_id = body['guild_id']
    azione = next((option['value'] for option in body['data']['options'] if option['name'] == 'azione'), None)
    
    response= api.getServerStatusInDB(server_id)
    print(f"RESPONSE STATUS: {response}") #debug
    if 'Item' in response:
        if azione == 'attiva':
            if response['Item']['stato'] == 'attiva':
                client.invia_follow_up(body['token'], "La funzione News è già attiva su questo server")
                return
            __activateChannel(server_id, 'riattiva', client)  
            
        elif response['Item']['stato'] == 'disattiva':
            client.invia_follow_up(body['token'], "La funzione News è già disattiva su questo server")
            return
        else:
            __deactivateChannel(response, server_id, client)  
    else:
        if azione == 'attiva':
            __activateChannel(server_id, 'attiva', client)  #fare anche il follow up
        else:
            client.invia_follow_up(body['token'], "La funzione News è già disattiva su questo server")
            

                

    
def __activateChannel(server_id, operation, client:DiscordManager):
    creationChannelUrl = f"https://discord.com/api/v8/guilds/{server_id}/channels"
    community='false'
    info_server = requests.get(f"https://discord.com/api/v8/guilds/{server_id}", headers=client.HEADERS)
    if info_server.status_code == 200 and info_server.json().get('features',[]).count('COMMUNITY') > 0:
        responseCreationChannel= requests.post(creationChannelUrl, headers=client.HEADERS, data=json.dumps(announcementChannelPayload))
        community='true'
    else:
        responseCreationChannel= requests.post(creationChannelUrl, headers=client.HEADERS, data=json.dumps(textChannelPayload))
    if responseCreationChannel.status_code == 201:
        channel_id = responseCreationChannel.json()['id']
        if operation == 'riattiva':
            update_response=api.updateDB(channel_id, server_id, 'attiva')
            if update_response['statusCode'] == 200:
                client.invia_follow_up(client.body['token'], f"Canale BOTNEWS creato e funzione News attivata! ✅")
                return
        elif operation == 'attiva':
            add_response=api.addToDB(responseCreationChannel, server_id, community, client)
            if add_response['statusCode'] == 200:
                client.invia_follow_up(client.body['token'], f"Canale BOTNEWS creato e funzione News attivata! ✅")
                return
    client.invia_follow_up(client.body['token'], "Errore nella creazione del canale ❌")
    
    

def __deactivateChannel(itemDB, server_id, client: DiscordManager):
    print("SONO NELLA DEACTIVATE") #debug
    channel_id = itemDB['Item']['channelid']
    removeChannelUrl = f"https://discord.com/api/v8/channels/{channel_id}"
    responseRemoveChannel= requests.delete(removeChannelUrl, headers=client.HEADERS)
    if responseRemoveChannel.status_code == 200:
        print("HO RIMOSSO IL CANALE")
        update_response=api.updateDB('null', server_id, 'disattiva')
        if update_response['statusCode'] == 200:
            client.invia_follow_up(client.body['token'], f"Canale BOTNEWS rimosso e funzione News disattivata! ✅")
            return
    print("ERRORE NELLA RIMOZIONE DEL CANALE", responseRemoveChannel.status_code) #debug
    client.invia_follow_up(client.body['token'], "Errore nella rimozione del canale ❌")

