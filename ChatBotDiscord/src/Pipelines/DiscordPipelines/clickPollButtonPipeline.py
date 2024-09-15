from DiscordManager import DiscordManager
from Api.PollApi import PollApi
from datetime import datetime
import requests
import json

api=PollApi()
def run(client: DiscordManager):  #TODO: per essere perfetto dovrei farlo transazionale e controllare per ogni richiesta api se è andata a buon fine
    body = client.body
    data = client.data
    message= body['message']
    description = message['embeds'][0]['description']
    end_time_str = description.split("Scadenza: ")[1].split(" UTC")[0]
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
    channel_id = message['channel_id']
    message_id = message['id']
    vote = data['custom_id'].replace('poll_vote:', '')
    user_id = body['member']['user']['id']
    old_vote = api.AlreadyVoted(user_id, message_id)
    if old_vote is not None:
        if old_vote != vote:
            api.changeVote(user_id, message_id, vote)
    else:
        api.insertVote(user_id, message_id, vote, end_time)
    __updatePollVotes(message_id, channel_id, client)
    return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'type': 6})}




def __updatePollVotes(message_id, channel_id,client: DiscordManager):
    votes_count = api.getVotesCount(message_id)
    if votes_count is None:
        return
    message_url = f"{client.BASE_DISCORD_API_URL}/channels/{channel_id}/messages/{message_id}"
    response = requests.get(message_url, headers=client.HEADERS)
    embed = response.json()['embeds'][0]
    for field in embed ['fields']:
        vote_key = f"buttonpoll:{field['name']}"
        vote_count = votes_count.get(vote_key, 0)
        field['value'] = f"Voti: {vote_count}"
    payload = { "embeds": [embed] }
    requests.patch(message_url, headers=client.HEADERS, json=payload)