import boto3

class NewsApi:
    def __init__(self):
        dynamoDB= boto3.resource('dynamodb')
        self.table= dynamoDB.Table('News')
        
    def getServerStatusInDB(self, server_id):
        response = self.table.get_item(
            Key={
                'serverid': server_id
            }
        )
        return response
    
    def updateDB(self, channel_id, server_id, operation):
        response = self.table.update_item(
            Key={
                'serverid': server_id
            },
            UpdateExpression="set stato = :s, channelid = :c",
            ExpressionAttributeValues={
                ':s': operation,
                ':c': channel_id
            }
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {
                'statusCode': 200,
                'body': 'DB updated successfully'
            }
        
    def addToDB(self, responseCreateChannel, server_id, community, client):
        channel_id = responseCreateChannel.json()['id']
        response = self.table.put_item(
            Item={
                'serverid': server_id,
                'stato': 'attiva',
                'channelid': channel_id,
                'community': community
            }
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {
                'statusCode': 200,
                'body': 'DB updated successfully'
            }