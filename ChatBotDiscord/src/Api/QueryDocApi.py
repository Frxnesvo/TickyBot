import boto3
import os
from langchain_community.embeddings import BedrockEmbeddings
import duckdb
import json

ROLE_AWS = os.getenv("ROLE_AWS_COMPANY")
DB_FILE_NAME = "db.duckdb"
DB_PATH = f"/tmp/{DB_FILE_NAME}"
BUCKET_NAME = 'documentsbucketchatbotdiscord'
EMBEDDINGS_MODEL_ID = "cohere.embed-multilingual-v3"
AI_COMPLETION_MODEL_ID = "anthropic.claude-instant-v1"

class QueryDocApi:
    def __init__(self):
        sts_client = boto3.client('sts')
        assumed_role = sts_client.assume_role(
            RoleArn=ROLE_AWS,
            RoleSessionName="session_name"
        )
        credentials = assumed_role['Credentials']
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name='us-east-1',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
        )
        self.s3 = boto3.client('s3')
        self.embedder = BedrockEmbeddings(client=self.bedrock, model_id=EMBEDDINGS_MODEL_ID)

    def downloadDbFile(self, serverId):
        s3Path = f"DiscordServer_{serverId}/{DB_FILE_NAME}"
        try:
            self.s3.download_file(BUCKET_NAME, s3Path, DB_PATH)
            return {
                'statusCode': 200,
                'body': 'File downloaded successfully'
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }
        
    def getQueryEmbeddings(self, query):
        return self.embedder.embed_query(query)
    
    def queryDb(self, queryEmbeddings):
        conn = duckdb.connect(database=DB_PATH, read_only=True)
        query = f"SELECT text FROM documents ORDER BY array_cosine_similarity(embedding, ?::FLOAT4[1024]) DESC LIMIT 3"
        result = conn.execute(query, [queryEmbeddings]).fetchdf()
        print(result.to_string()) #TODO: da rimuovere
        return ' '.join(result['text'].tolist())

    def generateCompletionMessage(self, query, results):
        prompt=f'''Questa è la query: {query} 
               Questi sono i dati dove devi cercare: {results}
               Se pensi che ci sia qualcosa di pertinente in uno di questi dati, fornisci una riposta, per pertintente non significa che tutti i dati devono matchare, ma anche solo una parte. Se invece pensi che nessun match sia presente in nessuno di questi dati, fornisci una risposta dove dici che non hai trovato nulla nel documento del server discord.
               La tua risposta sarà postata direttamente in un server discord quindi cerca di non far capire che io ti ho fornito dati, ma rispondi come se ti avessero posto una domanda a cui tu sai la risposta.'''
        try:
            body = {
                "prompt": "Human: " + prompt + "\nAssistant:",
                "max_tokens_to_sample": 500,
                "temperature": 0.6,
                "top_p": 0.9,
            }

            response = self.bedrock.invoke_model(
                modelId=AI_COMPLETION_MODEL_ID, body=json.dumps(body)
            )
            response_body = json.loads(response["body"].read())
            completion = response_body["completion"]
            return {
                'statusCode': 200,
                'body': completion
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }