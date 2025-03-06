import json
import boto3
import base64
from logging import Logger
logger = Logger(name='SearchFaceByImage')

rek_client = boto3.client('rekognition')

def lambda_handler(event, context):
    try:
        # Extrai os parâmetros da requisição
        collection_id = event['collection_id']
        
        # Verifica se a imagem foi enviada corretamente
        if "image_base64" not in event:
            return {"statusCode": 400, "body": json.dumps("Erro: Nenhuma imagem Base64 fornecida.")}

        # Decodifica a imagem Base64 para bytes
        image_bytes = base64.b64decode(event["image_base64"])

        # Faz a busca pela face na coleção
        response = rek_client.search_faces_by_image(
            CollectionId=collection_id,
            Image={'Bytes': image_bytes},
            MaxFaces=1,
            FaceMatchThreshold=90
        )

        return {
            "statusCode": 200,
            "body": json.dumps(response)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

