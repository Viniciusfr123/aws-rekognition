import json
import boto3
import base64
from logging import Logger
logger = Logger(name='SaveFaceAuth')

rekognition = boto3.client('rekognition')

COLLECTION_ID = "FaceAuthCollection"

def lambda_handler(event, context):
    try:
        # Verifica se a imagem veio como Base64 ou S3
        if "image_base64" in event:
            image_bytes = base64.b64decode(event["image_base64"])
            image = {'Bytes': image_bytes}
        else:
            return {"statusCode": 400, "body": json.dumps("Erro: Nenhuma imagem fornecida")}

        # Chama a API IndexFaces para adicionar o rosto
        response = rekognition.index_faces(
            CollectionId=COLLECTION_ID,
            Image=image,
            ExternalImageId=event.get("external_id", "unknown"),  # ID opcional para referência
            DetectionAttributes=["DEFAULT"]
        )

        # Pega o FaceId retornado
        if response['FaceRecords']:
            face_id = response['FaceRecords'][0]['Face']['FaceId']
            return {"statusCode": 200, "body": json.dumps({"faceId": face_id})}
        else:
            return {"statusCode": 400, "body": json.dumps("Nenhum rosto detectado.")}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Erro: {str(e)}")}
