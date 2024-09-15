import boto3
import time
import os
from .AI21TextSplitterDeps import AI21SemanticTextSplitter
from langchain_community.embeddings import BedrockEmbeddings
import duckdb

AI21_API_KEY = os.getenv("AI21_API_KEY")
ROLE_AWS = os.getenv("ROLE_AWS_COMPANY")
EMBEDDINGS_MODEL_ID = "cohere.embed-multilingual-v3"
DB_FILE_NAME = "db.duckdb"
DB_PATH = f"/tmp/{DB_FILE_NAME}"

class UploadDocApi:
    BUCKET_NAME= 'documentsbucketchatbotdiscord'
    PDF_KEY= "document.pdf"
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
        self.textract = boto3.client('textract')
        self.splitter= AI21SemanticTextSplitter(api_key= AI21_API_KEY)
        self.embedder = BedrockEmbeddings(client=self.bedrock,model_id=EMBEDDINGS_MODEL_ID)

    def isFolderPresent(self, folder_name):
        if not folder_name.endswith('/'):
            folder_name += '/'
        response = self.s3.list_objects_v2(Bucket=self.BUCKET_NAME, Prefix=folder_name)
        return 'Contents' in response and len(response['Contents']) > 0
    
    def createFolder(self, folder_name):
        try:
            self.s3.put_object(Bucket=self.BUCKET_NAME, Key=(folder_name+'/'))
            return {
                'statusCode': 200,
                'body': 'Folder created successfully'
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }
        
    def resetFolder(self, folder_name):
        try:
            response = self.s3.list_objects_v2(Bucket=self.BUCKET_NAME, Prefix=folder_name)
            if 'Contents' in response:
                for item in response['Contents']:
                    self.s3.delete_object(Bucket=self.BUCKET_NAME, Key=item['Key'])
            return {
                'statusCode': 200,
                'body': 'Folder reset successfully'
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }
        
    def uploadDocToFolder(self, folder_name, file_content):
        key=f"{folder_name}/{self.PDF_KEY}"
        try:
            self.s3.put_object(Bucket=self.BUCKET_NAME, Key=key, Body=file_content)
            return {
                'statusCode': 200,
                'body': 'File uploaded successfully'
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }
        
    def extractText(self, folder_name):
        s3FilePath=f"{folder_name}/{self.PDF_KEY}"
        try:
            response = self.textract.start_document_text_detection(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': self.BUCKET_NAME,
                        'Name': s3FilePath
                    }
                }
            )
            jobId = response['JobId']
            while not self.__isJobComplete(jobId)   :#FIXME: possibile loop infinito se non metto un timeout
                time.sleep(3)                #FIXME: riguardare il tempo di attesa per il completamento del job
            result=self.textract.get_document_text_detection(JobId=jobId)
            if result['JobStatus'] == 'FAILED':
                return {
                    'statusCode': 500,
                    'body': 'Internal Server Error'
                }
            nextToken=result.get('NextToken', None)
            results=[result['Blocks']]
            while nextToken:
                result=self.textract.get_document_text_detection(JobId=jobId, NextToken=nextToken)
                results.append(result['Blocks'])
                nextToken=result.get('NextToken', None)
            documentText=""
            for block in results:
                for item in block:
                    if item['BlockType'] == 'LINE':
                        documentText+=item['Text']+ '\n'
            return {
                'statusCode': 200,
                'body': documentText
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }
        
    def splitText(self, text):
        return self.splitter.split_text(text)

    def getEmbeddings(self, chunks):
        return self.embedder.embed_documents(chunks)
    
    def createAndUploadDuckDbFile(self, chunks, embeddings, folder_name):
        conn= self.__createTable()
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings),start=1):
            conn.execute('INSERT INTO documents (id, text, embedding) VALUES (?,?,?)', (i, chunk, embedding))
        conn.close()
        try:
            with open(DB_PATH, 'rb') as file:
                filePath=f"{folder_name}/{DB_FILE_NAME}"
                self.s3.upload_fileobj(file, self.BUCKET_NAME, filePath)
        except Exception as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }
        try:
            os.remove(DB_PATH)
        except Exception as e:
            return {
                'statusCode': 500,
                'body': 'Internal Server Error'
            }
        return {
            'statusCode': 200,
            'body': 'DuckDB file uploaded successfully'
        }


    def __isJobComplete(self, jobId):
        response = self.textract.get_document_text_detection(JobId=jobId)
        status = response['JobStatus']
        print(f"Job status: {status}") #FIXME: rimuovere
        if status == 'FAILED':
            print(f"Job failed: {response['StatusMessage']}")
            return True
        return status=='SUCCEEDED'
    
    def __createTable(self):
        conn = duckdb.connect(database=DB_PATH, read_only=False)
        conn.execute('CREATE TABLE documents (id INTEGER, text VARCHAR, embedding FLOAT4[1024])')
        return conn
    