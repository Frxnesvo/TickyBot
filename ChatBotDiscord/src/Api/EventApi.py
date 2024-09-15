import boto3
from datetime import datetime , timedelta
from botocore.exceptions import ClientError
import json
from boto3.dynamodb.conditions import Key

class EventApi:
    DATA_FORMAT = "%Y-%m-%d %H:%M"
    STATE_MACHINE_ARN = 'arn:aws:states:eu-central-1:565507045048:stateMachine:MyStateMachine-9p8oim53v'  #TODO: da mettere in variabile d'ambiente
    def __init__(self):
        dynamoDB= boto3.resource('dynamodb')
        self.table= dynamoDB.Table('Calendario')    #TODO: potrei mettere il nome come costante
        self.machine= boto3.client('stepfunctions')

    def addEventToDynamoDB(self, user_id, titolo, data_inizio):
        check= self.__isEventPresent(user_id, titolo)
        if check is None:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error ❌​'
            }
        elif check:
            return {
                'statusCode': 400,
                'body': "L'evento è già presente nel calendario 📅​"
            }
        else:
            data_datetime = datetime.strptime(data_inizio, self.DATA_FORMAT) + timedelta(minutes=1)
            try:
                response = self.table.put_item(
                    Item={
                        'userid': str(user_id),
                        'title': titolo,
                        'datainizio': data_inizio,
                        'timestamp': int(data_datetime.timestamp()) 
                    }
                )
                return {
                    'statusCode': 200,
                    'body': f"Evento '{titolo}' aggiunto con successo in data {data_inizio} 🫡​"
                }
            except ClientError as e:
                return {
                    'statusCode': 500,
                    'body': 'Internal Server Error ❌​'
                }

    def startStateMachine(self, titolo, user_id, event_time):
        input_for_state_machine = json.dumps({
            "event_name": titolo,
            "user_id": user_id,
            "event_time": event_time
        })
        response = self.machine.start_execution(
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
                'body': 'Internal Server Error ❌​'
            }  

    def __isEventPresent(self, user_id, titolo):
        try:
            response = self.table.scan(
                FilterExpression='userid = :userid AND title = :title',
                ExpressionAttributeValues={
                    ':userid': str(user_id),
                    ':title': titolo,
                }
            )
            return 'Items' in response and len(response['Items']) > 0
        except Exception as e:
            return None
        
    def deleteEventFromDynamoDB(self, user_id, titolo):
        check= self.__isEventPresent(user_id,titolo)
        if check is None:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error ❌​'
            }
        elif check:
            try:
                self.table.delete_item(
                    Key={
                        'userid': str(user_id),
                        'title': titolo
                    }
                )
                return {
                    'statusCode': 200,
                    'body': f"Evento '{titolo}' eliminato con successo 🗑️​"
                }
            except ClientError as e:
                return {
                    'statusCode': 500,
                    'body': 'Internal Server Error ❌​'
                }
        else:
            return {
                'statusCode': 400,
                'body': f'Nessun evento {titolo} trovato ❌​'
            }
        
    def stopStateMachine(self, titolo, user_id):
        try:
            response = self.machine.list_executions(
                stateMachineArn=self.STATE_MACHINE_ARN,
                statusFilter='RUNNING'
            )
            for execution in response['executions']:
                execution_arn = execution['executionArn']

                execution_details = self.machine.describe_execution(
                    executionArn=execution_arn
                )
                input = json.loads(execution_details['input'])
                if input.get('event_name') == titolo and input.get('user_id') == user_id:
                    stopResponse = self.machine.stop_execution(
                        executionArn=execution_arn,
                        cause='Evento cancellato'
                    )
                    return {
                        'statusCode': 200,
                        'body': f"State Machine '{self.STATE_MACHINE_ARN}' stopped successfully"
                    }
            return {
                'statusCode': 200,
                'body': f"State Machine '{self.STATE_MACHINE_ARN}' not found"
            }
        except ClientError as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error ❌​'
            }
        
    def getUserEvents(self, user_id):
        response = self.table.query(
            KeyConditionExpression=Key('userid').eq(str(user_id))
        )
        return response['Items']