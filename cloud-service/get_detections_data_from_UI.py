import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("radar-logs")

# Helper to convert Decimal to int/float for JSON
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,OPTIONS"
    }

    params = event.get("queryStringParameters") or {}

    jetson_id = params.get("jetson_id")
    if not jetson_id:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "jetson_id is required"})
        }

    object_name = params.get("object_name")
    from_time = params.get("from")
    to_time = params.get("to")
    limit = int(params.get("limit", 50))

    key_exp = Key("jetson_id").eq(jetson_id)

    if from_time and to_time:
        key_exp = key_exp & Key("timestamp").between(from_time, to_time)

    response = table.query(
        KeyConditionExpression=key_exp,
        Limit=limit,
        ScanIndexForward=False
    )

    items = response.get("Items", [])

    if object_name:
        items = [i for i in items if i.get("object_name") == object_name]

    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps(items, default=decimal_default)
    }
