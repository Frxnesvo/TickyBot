import boto3
import json
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

class PollApi:

    def __init__(self):
        self.client = boto3.client('stepfunctions')
        self.STATE_MACHINE_ARN = 'arn:aws:states:eu-central-1:565507045048:stateMachine:MyStateMachine-nveyhoj4z'  #TODO: spostare in variabili d'ambiente
        dynamoDB = boto3.resource('dynamodb')
        self.table = dynamoDB.Table('VotiSondaggi')  #TODO: potrei mettere il nome come costante

    def startStepMachine(self,event_time, channel_id, message_id):
        input_for_state_machine = json.dumps({
            "event_time": event_time,  # Assicurati che sia in formato ISO 8601
            "channel_id": channel_id,
            "message_id": message_id
        })

        # Avvia l'esecuzione della State Machine
        response = self.client.start_execution(
            stateMachineArn=self.STATE_MACHINE_ARN,
            input=input_for_state_machine
        )
        if 'executionArn' in response:
            return {
                'statusCode': 200,
                'body': "State Machine started successfully"
            }
        else:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }
        
    def AlreadyVoted(self, user_id, message_id):
        response = self.table.get_item(
            Key={
                'messageid': message_id,
                'userid': user_id
            }
        )
        if 'Item' in response:
            return response['Item']['vote']
        else:
            return None
    
    def changeVote(self, user_id, message_id, new_vote):
        try:
            self.table.update_item(
                Key={
                    'messageid': message_id,
                    'userid': user_id
                },
                UpdateExpression="set vote = :v",
                ExpressionAttributeValues={
                    ':v': new_vote
                }
            )
            return { 
                'statusCode': 200, 
                'body': 'Voto cambiato con successo' 
            }
        except ClientError as e:
            return { 
                'statusCode': 500, 
                'body': 'Internal Server Error' 
            }
        
    
    def insertVote(self, user_id, message_id, vote, end_time):
        try:
            response = self.table.put_item(
                Item={
                    'messageid': message_id,
                    'userid': user_id,
                    'vote': vote,
                    'timestamp': int(end_time.timestamp())
                }
            )
            return {
                'statusCode': 200,
                'body': 'Voto inserito con successo'
            }
        except ClientError as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }

    
    def getVotesCount(self, message_id):
        try:
            response = self.table.scan(
                FilterExpression=Attr('messageid').eq(message_id)
            )
            votes_count = {}
            for item in response['Items']:
                vote = item['vote']
                votes_count[vote] = votes_count.get(vote, 0) + 1
            return votes_count
        except ClientError as e:
            #TODO: gestire l'errore
            return None



