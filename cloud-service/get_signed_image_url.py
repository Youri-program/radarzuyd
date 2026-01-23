import json
import boto3

s3 = boto3.client("s3")
BUCKET = "edge-images-zuyd"

def lambda_handler(event, context):

    # Read params from API Gateway
    params = event.get("queryStringParameters") or {}
    key = params.get("key")

    if not key:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing key"})
        }

    try:
        # Generate signed URL valid for 1 hour
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BUCKET, "Key": key},
            ExpiresIn=3600
        )

        return {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"url": url})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

