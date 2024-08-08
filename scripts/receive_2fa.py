# -*- coding: utf-8 -*-
# pylint: disable=C0111,C0103,R0205
import pika
import sys
import requests

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
    virtual_host="/",
    credentials=credentials))

main_channel = connection.channel()

# Callback function to handle received messages
def callback(ch, method, properties, body):
    message = body.decode('utf-8')
    print(f"[x] Received: {message}")
    # Acknowledge the message after processing
    ch.basic_ack(delivery_tag=method.delivery_tag)

main_channel.basic_qos(prefetch_count=10)  # Increase prefetch count for better handling
main_channel.basic_consume(queue='nost', on_message_callback=callback, auto_ack=False)  # Turn off auto acknowledgments

print('Waiting for messages. To exit press CTRL+C')
main_channel.start_consuming()
