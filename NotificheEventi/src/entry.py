from Pipelines.DiscordPipelines.notificaEventiPipeline import run as notificaEventiPipeline

def lambda_handler(event, context): 
    notificaEventiPipeline(event)