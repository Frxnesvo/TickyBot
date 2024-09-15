from ClientManager import ClientManager
import json
import os
import requests
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from HandlerManager import HandlerManager


class DiscordManager(ClientManager):
    APPLICATION_ID = os.getenv("APPLICATION_ID")
    BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    HEADERS = {'Authorization': f'Bot {BOT_TOKEN}', 'Content-Type': 'application/json'}
    BASE_DISCORD_API_URL = "https://discord.com/api/v8"
    PUBLIC_KEY = os.getenv('APPLICATION_PUBLIC_KEY')

    def __init__(self, event):
        super().__init__(event)

    def _deserializeEvent(self, event):
        self.body = json.loads(event['body'])
        self.data = self.body['data']


    def inviaAck(self, silent=False):
        token = self.body['token']
        interaction_id = self.body['id']
        url = f"{self.BASE_DISCORD_API_URL}/interactions/{interaction_id}/{token}/callback"
        
        ack_payload = {
            "type": 6 if silent else 5       # 5: ACK con source message, 6: ACK senza source message
        }
        requests.post(url, headers=self.HEADERS, json=ack_payload)

    def invia_follow_up(self,token, message):
        url = f"{self.BASE_DISCORD_API_URL}/webhooks/{self.APPLICATION_ID}/{token}"  #TODO: potrei evitare di passare il token come parametro e fare direttamente body['token'] 
        message_payload = message
        if isinstance(message, str):
            message_payload = {
                "content": message,
                "flags": 1 << 6
            }
        #se è un dizionario lo invio direttamente
        response= requests.post(url, headers=self.HEADERS, json=message_payload)
        return response.status_code, response.json()

    def _auth(self):
        signature= self.event['headers']['x-signature-ed25519']
        timestamp = self.event['headers'].get('x-signature-timestamp')
        try:
            verify_key= VerifyKey(bytes.fromhex(self.PUBLIC_KEY))
            verify_key.verify(f"{timestamp}{self.body}".encode(), bytes.fromhex(signature))
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'type': 1})  # Risposta necessaria per la verifica PING da Discord
            }
        except BadSignatureError:
            return {
                'statusCode': 401,
                'body': 'Not Authorized'
            }
        
    def getHandlersMap(self):
        return{
            "addevent": "Pipelines.DiscordPipelines.addEventPipeline.run",
            "deleteevent": "Pipelines.DiscordPipelines.deleteEventPipeline.run",
            "showevents": "Pipelines.DiscordPipelines.showEventsPipeline.run",
            "createpoll": "Pipelines.DiscordPipelines.createPollPipeline.run",
            "buttonpoll": "Pipelines.DiscordPipelines.clickPollButtonPipeline.run",
            "setupnews": "Pipelines.DiscordPipelines.setupNewsPipeline.run",
            "serversentiment": "Pipelines.DiscordPipelines.serverSentimentPipeline.run",
            "uploaddocument": "Pipelines.DiscordPipelines.uploadDocPipeline.run",
            "querydocument": "Pipelines.DiscordPipelines.queryDocPipeline.run",
        }
    
    #TODO: piu che handlers qua parliamo di pipelines (da cambiare alla fine)
    def redirectRequest(self):
        interaction_type = self.body.get('type')
        if interaction_type == 1:
            return self._auth()
        elif interaction_type == 2 or interaction_type == 3: # 2: ComandoSlash, 3: Bottone
            print("SONO NEL REDIRECT REQUEST CON INTERACTION TYPE 2 o 3")
            h_Manager =  HandlerManager(self)
            if interaction_type == 2:
                command_name = self.data['name']
            else:
                command_name = self.data['custom_id'].split(':')[0]
            if command_name in self.getHandlersMap() and interaction_type == 2: 
                self.inviaAck()
            handler= h_Manager.getHandler(command_name)
            if handler:
                return handler(self)
            else:
                return self.__webhook_response("Comando non riconosciuto")
        else:
            return self.__webhook_response("Tipo di interazione non supportato")

    
    def __webhook_response(self, message):
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'type': 4,  # CHANNEL_MESSAGE_WITH_SOURCE
                'data': {
                    'content': f"{message}",
                    'flags': 1 << 6,  # Opzionale: Imposta il flag EPHEMERAL se desiderato
                }
            })
        }
        