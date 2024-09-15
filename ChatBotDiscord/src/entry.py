from DiscordManager import DiscordManager

def lambda_handler(event, context):  
    client = DiscordManager(event)
    return client.redirectRequest()
    