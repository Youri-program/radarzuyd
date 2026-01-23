import json
import boto3
import base64
from datetime import datetime

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("radar-logs")

BUCKET = "edge-images-zuyd"

def lambda_handler(event, context):

    try:
        body = json.loads(event["body"])
    except:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON"})
        }

    jetson_id = body.get("jetson_id")
    object_name = body.get("object_name", "unknown")
    image_base64 = body.get("image_base64")

    # SAFE TIMESTAMP (no +, no :, no spaces)
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")

    image_key = f"{jetson_id}/{timestamp}_{object_name}.jpeg"

    if image_base64:
        image_data = base64.b64decode(image_base64)
        s3.put_object(
            Bucket=BUCKET,
            Key=image_key,
            Body=image_data,
            ContentType="image/jpeg"
        )

    table.put_item(Item={
        "jetson_id": jetson_id,
        "timestamp": timestamp,
        "object_name": object_name,
        "image_url": image_key
    })

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Upload OK", "image_url": image_key})
    }

