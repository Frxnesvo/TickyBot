from caricaNewsPipeline import run as caricaNewsPipeline
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  
#Al momento qua non sto gestendo gli errori

def lambda_handler(event, context):
    caricaNewsPipeline()
    