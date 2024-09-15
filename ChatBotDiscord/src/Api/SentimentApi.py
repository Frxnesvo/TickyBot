import boto3
import json 
import datetime
import pytz

class SentimentApi:
    TIME_PATTERN='%Y-%m-%d %H:%M:%S'
    DEFAULT_MAX_CHUNK_SIZE = 5000
    ROLE_ARN="arn:aws:iam::684359859465:role/FrancescoGallo"  #TODO: da mettere in variabile d'ambiente
    def __init__(self):
        dynamodb = boto3.resource('dynamodb')
        self.table = dynamodb.Table('Sentiment') #TODO: potrei mettere il nome come costante
        self.comprehend = boto3.client('comprehend')
        


    def getServerStatus(self, server_id):
        response = self.table.get_item(
            Key={
                'serverid': server_id
            }
        )
        if 'Item' in response:
            return True, response['Item']['time']
        return False, None
        
    def divideMessagesInChunks(self, messages, max_chunk_size=DEFAULT_MAX_CHUNK_SIZE):
        '''
        Divide i messaggi in blocchi di dimensione massima max_size (in bytes).
        Ritorna una lista di tuple in cui il primo elemento è il blocco di messaggi concatenati e il secondo elemento è la dimensione del blocco.
        '''
        blocks = []
        current_block = []
        current_size = 0
        
        for msg in messages:
            msg_size = len(msg.encode('utf-8'))  # Calcola la dimensione del messaggio in bytes
            if current_size + msg_size > max_chunk_size:
                blocks.append((". ".join(current_block), current_size))   # Aggiungi il blocco corrente alla lista in una tupla con la dimensione
                current_block = [msg]
                current_size = msg_size
            else:
                current_block.append(msg)
                current_size += msg_size

        # Aggiungi l'ultimo blocco se non è vuoto
        if current_block:
            blocks.append((". ".join(current_block), current_size))

        return blocks
    
    def analyzeServerSentiment(self, chunks, max_chunk_size=DEFAULT_MAX_CHUNK_SIZE):
        '''
        Dato un insieme di blocchi di messaggi e le relative dimensioni, calcola il sentiment ponderato di tutti i messaggi.
        Ritorna una tupla contenente il sentiment prevalente e i punteggi medi di sentiment.
        '''

        sumWeights = 0
        scores = {"Positive": [], "Negative": [], "Neutral": [], "Mixed": []}

        for chunk, size in chunks:
            sentiment, score = self.__calculate_sentiment(chunk)   #FIXME: non uso il valore di ritorno sentiment, vedere se toglierlo proprio o meno
            sumWeights += size
            for key in scores.keys():
                scores[key].append(score[key]*size)


        # Calcola la media dei punteggi di sentiment
        average_scores = {key: sum(val) / sumWeights for key, val in scores.items()}
        mode_sentiment = max(average_scores, key=average_scores.get)

        return mode_sentiment, average_scores
    


    def generateCompletionMessage(self,sentiment, scores):
        prompt=f'''Il sentiment del mio server discord è {sentiment}. Queste a seguire sono le percentuali di sentiment positive, negative, neutral e misto: 
            {scores}. Che consigli mi daresti per migliorare il mio server? Rispondi mostrando e spiegando i dati e poi dando qualche consiglio
            variegato . La tua risposta sarà postata direttamente in un server discord quindi cerca di non far capire che io ti ho fornito dati, ma rispondi 
            come se ti avessero chiesto di fare a te un'analisi del sentiment del server.'''
        try:
            body = {
                "prompt": "Human: " + prompt + "\nAssistant:",      #TODO: questi settings potrei metterli in una classe a parte
                "max_tokens_to_sample": 500,
                "temperature": 0.8,
                "top_p": 0.9,
            }
            sts_client = boto3.client('sts')
            assumed_role = sts_client.assume_role(
                RoleArn=self.ROLE_ARN,
                RoleSessionName="session_name"
            )
            
            credentials = assumed_role['Credentials']
            bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name='us-east-1',
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
            )

            response = bedrock_client.invoke_model(
                modelId="anthropic.claude-instant-v1", body=json.dumps(body)
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
        
    def addCalculationToDynamoDB(self,server_id, durata):
        time_ita = datetime.datetime.now(pytz.timezone("Europe/Rome")) + datetime.timedelta(days=int(durata))
        timestamp = time_ita.timestamp()
        time_ita = time_ita.strftime(self.TIME_PATTERN)
        try:
            self.table.put_item(
                Item={
                    'serverid': server_id,
                    'time': time_ita,
                    'timestamp': int(timestamp)
                }
            )
            return {
                'statusCode': 200,
                'body': 'Calculation added successfully'
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }

    
    def __calculate_sentiment(self, message):
        response = self.comprehend.detect_sentiment(
            Text=message,
            LanguageCode='it'
        )
        return response['Sentiment'], response['SentimentScore']
    
