from Api.UploadDocApi import UploadDocApi
from DiscordManager import DiscordManager
import requests

api=UploadDocApi()
def run(client: DiscordManager):
    body = client.body
    data = client.data
    if 'guild_id' not in body:
        client.invia_follow_up(body['token'], "Non puoi eseguire questo comando nella chat privata ❌")
        return
    server_id = body['guild_id']
    pdf_url = next(item for item in data['options'] if item['name'] == 'url')['value']
    folder_name = f"DiscordServer_{server_id}"
    if not api.isFolderPresent(folder_name):
        create_folder_response = api.createFolder(folder_name)
        if create_folder_response['statusCode'] != 200:
            client.invia_follow_up(body['token'], "Errore nella creazione della cartella ❌")
            return
    else:
        reset_folder_response=api.resetFolder(folder_name)
        if reset_folder_response['statusCode'] != 200:
            client.invia_follow_up(body['token'], "Errore nel reset della cartella ❌")
            return
    try:
        pdf= requests.get(pdf_url)   #Scarico il pdf
        pdf.raise_for_status()
    except requests.exceptions.RequestException as e:
        client.invia_follow_up(body['token'], "Errore nel download del file ❌")
        return
    pdfContent = pdf.content
    upload_response = api.uploadDocToFolder(folder_name, pdfContent)  # Salva il PDF nel bucket S3
    if upload_response['statusCode'] != 200:
        client.invia_follow_up(body['token'], "Errore nell'upload del file ❌")
        return
    extract_response = api.extractText(folder_name)  #estrazione del testo dal documento
    if extract_response['statusCode'] != 200:
        client.invia_follow_up(body['token'], "Errore nell'estrazione del testo ❌")
        return
    documentText = extract_response['body']
    chunks = api.splitText(documentText)  #divisione del testo in chunks semantici
    embeddings = api.getEmbeddings(chunks)  #ottenimento degli embeddings
    db_response = api.createAndUploadDuckDbFile(chunks, embeddings, folder_name)  #creazione e upload del file db
    if db_response['statusCode'] != 200:
        client.invia_follow_up(body['token'], "Errore nella creazione del file db ❌")
        return
    client.invia_follow_up(body['token'], "Il documento è stato caricato con successo! ✅")

