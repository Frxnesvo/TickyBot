from DiscordManager import DiscordManager
from Api.QueryDocApi import QueryDocApi

api=QueryDocApi()
def run(client:DiscordManager):
    body = client.body
    if 'guild_id' not in body:
        client.invia_follow_up(body['token'], "Non puoi eseguire questo comando nella chat privata ❌")
        return
    serverId = body['guild_id']
    query = next((option['value'] for option in body['data']['options'] if option['name'] == 'query'), None)
    download_response=api.downloadDbFile(serverId)
    if download_response['statusCode'] != 200:
        client.invia_follow_up(body['token'], "Errore nel download del file ❌​")
        return
    queryEmbeddings = api.getQueryEmbeddings(query)
    queryResults = api.queryDb(queryEmbeddings)
    completion_response=api.generateCompletionMessage(query, queryResults)
    if completion_response['statusCode'] != 200:
        client.invia_follow_up(body['token'], "Errore nella generazione del completamento ❌​")
        return
    client.invia_follow_up(body['token'], completion_response['body'])
    