#!/usr/bin/env python
import pika
import sys
from keycloak.keycloak_openid import KeycloakOpenID

def new_access_token():
    keycloak_openid = KeycloakOpenID(server_url="http://localhost:8080/",
                                     client_id=sys.argv[1],
                                     realm_name="test",
                                     client_secret_key=sys.argv[2])

    # Get token
    token = keycloak_openid.token(grant_type='client_credentials')

    # Check if the request was successful
    if 'access_token' in token:
        return token['access_token']
    else:
        # Raise an error if the request was unsuccessful
        raise Exception("Error: The request was unsuccessful.")
    
access_token = new_access_token()
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

main_channel.exchange_declare(exchange='topic_logs', exchange_type='topic')

result = main_channel.queue_declare('', exclusive=True)
queue_name = result.method.queue

if not binding_keys:
    sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
    sys.exit(1)

for binding_key in binding_keys:
    main_channel.queue_bind(
        exchange='topic_logs', queue=queue_name, routing_key=binding_key)

print(' [*] Waiting for logs. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body}")


main_channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)

main_channel.start_consuming()