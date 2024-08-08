import datetime
import time
import pika
import requests
import sys
from keycloak.keycloak_openid import KeycloakOpenID
import getpass
def new_access_token(refresh_token=None):
    keycloak_openid = KeycloakOpenID(server_url="http://localhost:8080/",
                                     client_id=client_id,
                                     realm_name="test",
                                     client_secret_key=client_secret_key
                                     )
    try:
        if refresh_token:
            # Use the refresh token to get a new access token
            token = keycloak_openid.refresh_token(refresh_token)
        else:
            # Get initial token with required scopes
            token = keycloak_openid.token(grant_type='password', 
                                          username=username, 
                                          password=password, 
                                          totp=otp, 
                                          scope='openid rabbitmq.read:*/nost/* rabbitmq.write:*/nost/* rabbitmq.configure:*/nost/*')

        # Check if the request was successful
        if 'access_token' in token:
            print(f"Access token retrieved successfully: {token['access_token']}")
            print(f"\nAccess token retrieved successfully: {token['access_token']}\n")
            print(f"Access token scope: {token['scope']}\n")
            return token['access_token'], token['refresh_token']
        else:
            # Raise an error if the request was unsuccessful
            raise Exception("Error: The request was unsuccessful.")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
# Define credentials
global client_id, username, password, client_secret_key, otp
client_id = input("Enter client ID: ")
username = input("Enter your username: ")
password = getpass.getpass("Enter your password: ")
client_secret_key = input("Enter client secret key: ")
otp = input("Enter OTP: ")
# Retrieve the access token and refresh token
access_token, refresh_token = new_access_token()
# Use the access token as the password for RabbitMQ
credentials = pika.PlainCredentials('', access_token)  # Use the correct username
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost',
        virtual_host="/",  # URL-encoded virtual host
        port=5672,
        credentials=credentials))
    print("Connection established successfully.")
except pika.exceptions.ProbableAccessDeniedError as e:
    print(f"Access denied: {e}")
    sys.exit(1)
main_channel = connection.channel()
main_channel.queue_declare(queue="nost", auto_delete=False, durable=True,
                           arguments={"x-queue-type": "quorum"})
_COUNT_ = 100
tnow = datetime.datetime.now()
last_update = datetime.datetime.now()
for i in range(0, _COUNT_):
    message = f'Message #{i}'
    print(f'[x] Sent: {message}')
    # Update the secret each minute. Supposed that Access Token Lifespan is 1 minute.
    if (datetime.datetime.now() - last_update).total_seconds() > 55:
        last_update = datetime.datetime.now()
        # print('updating secret {}'.format((datetime.datetime.now() - tnow).total_seconds() / 60))
        print('Refreshing token.')
        access_token, refresh_token = new_access_token(refresh_token)
        connection.update_secret(access_token, 'secret')
    main_channel.basic_publish(
        exchange='nost',
        routing_key='nost',
        body=message,
        properties=pika.BasicProperties(content_type='application/json'))
    time.sleep(5)
connection.close()