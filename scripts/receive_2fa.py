# -*- coding: utf-8 -*-
# pylint: disable=C0111,C0103,R0205
import pika
import sys
import requests
from keycloak.keycloak_openid import KeycloakOpenID

# def new_access_token():
#     headers = {'Content-Type': 'application/x-www-form-urlencoded'}
#     r = requests.post('http://localhost:8080/realms/test/protocol/openid-connect/token', headers=headers,
#                       data={'client_id': sys.argv[1], 'client_secret': sys.argv[2],
#                             'grant_type': 'client_credentials'})

#     # Check if the request was successful
#     if r.status_code == 200:
#         dictionary = r.json()
#         return dictionary["access_token"]
#     else:
#         # Raise an error if the request was unsuccessful
#         raise Exception(f"Error: The request was unsuccessful with status code {r.status_code}.")

def new_access_token():
    keycloak_openid = KeycloakOpenID(server_url="http://localhost:8080/",
                                     client_id="producer", #sys.argv[1],
                                     realm_name="test",
                                     client_secret_key="kbOFBXI9tANgKUq8vXHLhT6YhbivgXxn")#sys.argv[2])

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

# Get the exchange name and topic or queue name from the user
exchange_name = input("Enter the exchange name: ")
binding_keys = input("Enter the routing/binding key (topic) (e.g., topic.topic2.topic3): ").strip().split(' ')
print(binding_keys)
queue_name = 'nost'

main_channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

# result = main_channel.queue_declare(queue_name, exclusive=True)
# queue_name = result.method.queue
# print(queue_name)

if not binding_keys:
    sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
    sys.exit(1)

for binding_key in binding_keys:
    print(binding_key)
    main_channel.queue_bind(
        exchange=exchange_name, queue=queue_name, routing_key=binding_key)

print(' [*] Waiting for logs. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body.decode('utf-8')}")


main_channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)

main_channel.start_consuming()