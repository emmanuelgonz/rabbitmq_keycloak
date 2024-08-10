import pika
import sys
from keycloak.keycloak_openid import KeycloakOpenID

def new_access_token():
    keycloak_openid = KeycloakOpenID(server_url="http://localhost:8080/",
                                     client_id=client_id,
                                     realm_name="test",
                                     client_secret_key=client_secret_key
                                     )

    try:
        token = keycloak_openid.token(grant_type='client_credentials', 
                                      scope='openid rabbitmq.read:*/nost/* rabbitmq.write:*/nost/* rabbitmq.configure:*/nost/*')

        if 'access_token' in token:
            print(f"\nAccess token retrieved successfully: {token['access_token']}\n")
            print(f"Access token scope: {token['scope']}\n")
            return token['access_token'], token['refresh_token']
        else:
            raise Exception("Error: The request was unsuccessful.")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

global client_id, client_secret_key
client_id = input("Enter client ID: ")
client_secret_key = input("Enter client secret key: ")

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

channel = connection.channel()

# Get the exchange name and topic or queue name from the user
exchange_name = input("Enter the exchange name: ")
binding_keys = input("Enter the routing/binding key (topic) (e.g., topic.topic2.topic3): ")
queue_name = 'nost'

# Declare the topic exchange
channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

# Declare a queue and bind it to the exchange with the routing key
channel.queue_declare(queue=queue_name, durable=True)
channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=binding_keys)

def callback(ch, method, properties, body):
    print(f" [x] Received {body}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
