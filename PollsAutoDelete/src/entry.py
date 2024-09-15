from Pipelines.DiscordPipelines.pollsDeletePipeline import run as pollsDeletePipeline

def lambda_handler(event, context):  #cambiare il nome nel file template.yaml
    pollsDeletePipeline(event)