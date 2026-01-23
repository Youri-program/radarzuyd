import json
import boto3
import hashlib
import hmac
import base64

def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(
        client_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def lambda_handler(event, context):
    client = boto3.client('cognito-idp', region_name='eu-central-1')
    
    client_id = '2c0ccqga4che8rgslck9k51u2m'
    client_secret = '182t91h4084pmfi5dqhi14pfelvfmdquiruapqaujo8i59p7ktlp'
    
    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        elif event.get('body'):
            body = event['body']
        else:
            body = event
        
        username = body.get('username')
        password = body.get('password')
        
        if not username or not password:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Username and password required'})
            }
        
        secret_hash = get_secret_hash(username, client_id, client_secret)
        
        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'access_token': response['AuthenticationResult']['AccessToken'],
                'id_token': response['AuthenticationResult']['IdToken'],
                'expires_in': response['AuthenticationResult']['ExpiresIn']
            })
        }
        
    except client.exceptions.NotAuthorizedException:
        return {
            'statusCode': 401,
            'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid credentials'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e), 'type': str(type(e).__name__)})
        }
