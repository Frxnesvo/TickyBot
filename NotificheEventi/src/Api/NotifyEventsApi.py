import boto3

class NotifyEventsApi:
    def __init__(self):
        dynamo= boto3.resource('dynamodb')
        self.table= dynamo.Table('Calendario')

    def deleteEvent(self, user_id, event_name):
        try:
            self.table.delete_item(
                Key={
                    'userid': user_id,
                    'title': event_name
                }
            )
        except Exception as e:
            print(f"Errore nella cancellazione dell'evento: {e}")  #TODO: da loggare