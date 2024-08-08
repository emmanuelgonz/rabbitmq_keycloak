# -*- coding: utf-8 -*-
# pylint: disable=C0111,C0103,R0205
import datetime
import time
import pika
import requests
import sys

print('pika version: %s' % pika.__version__)

# You need Pika 1.3
# Get the access token
def new_access_token():
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post('http://localhost:8080/realms/test/protocol/openid-connect/token', headers=headers,
                      data={'client_id': sys.argv[1], 'client_secret': sys.argv[2],
                            'grant_type': 'client_credentials'})

    # Check if the request was successful
    if r.status_code == 200:
        dictionary = r.json()
        return dictionary["access_token"] 
    else: 
        # Raise an error if the request was unsuccessful
        raise Exception(f"Error: The request was unsuccessful with status code {r.status_code}.")

credentials = pika.PlainCredentials('', new_access_token())
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='localhost',
    virtual_host="/",
    port=5672,
    credentials=credentials))

main_channel = connection.channel()
main_channel.queue_declare(queue="keycloak", auto_delete=False, durable=True,
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
        print('Access token refreshed.')
        connection.update_secret(new_access_token(), 'secret')

    main_channel.basic_publish(
        exchange='',
        routing_key='keycloak',
        body=message,
        properties=pika.BasicProperties(content_type='application/json'))

    time.sleep(5)

connection.close()
