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
            token = keycloak_openid.refresh_token(refresh_token)
        else:
            token = keycloak_openid.token(grant_type='password', 
                                          username=username, 
                                          password=password, 
                                          totp=otp, 
                                          scope='openid rabbitmq.read:*/* rabbitmq.write:*/* rabbitmq.configure:*/*')

        if 'access_token' in token:
            print(f"\nAccess token retrieved successfully: {token['access_token']}\n")
            print(f"Access token scope: {token['scope']}\n")
            return token['access_token'], token['refresh_token']
        else:
            raise Exception("Error: The request was unsuccessful.")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

global client_id, username, password, client_secret_key, otp
client_id = input("Enter client ID: ")
username = input("Enter your username: ")
password = getpass.getpass("Enter your password: ")
client_secret_key = input("Enter client secret key: ")
otp = input("Enter OTP: ")

access_token, refresh_token = new_access_token()

credentials = pika.PlainCredentials('', access_token)
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost',
        virtual_host="/",
        port=5672,
        credentials=credentials))
    print("Connection established successfully.")
except pika.exceptions.ProbableAccessDeniedError as e:
    print(f"Access denied: {e}")
    sys.exit(1)

main_channel = connection.channel()

# Get the exchange name and topic or queue name from the user
exchange_name = input("Enter the exchange name: ")
topic_or_queue = input("Enter the routing key (topic/queue) (e.g., topic.topic2.topic3): ")

# Declare the topic exchange
main_channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

_COUNT_ = 100

tnow = datetime.datetime.now()
last_update = datetime.datetime.now()

for i in range(0, _COUNT_):

    message = f'Message #{i}'
    print(f'[x] Sent: {message}')

    if (datetime.datetime.now() - last_update).total_seconds() > 55:
        last_update = datetime.datetime.now()
        print('Refreshing token.')
        access_token, refresh_token = new_access_token(refresh_token)
        connection.update_secret(access_token, 'secret')

    main_channel.basic_publish(
        exchange=exchange_name,
        routing_key=topic_or_queue,
        body=message,
        properties=pika.BasicProperties(content_type='application/json'))

    time.sleep(5)

connection.close()
