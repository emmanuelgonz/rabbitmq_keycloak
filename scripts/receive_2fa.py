import pika
import sys
import requests
from keycloak.keycloak_openid import KeycloakOpenID
import getpass

# def new_access_token(refresh_token=None):
#     keycloak_openid = KeycloakOpenID(server_url="http://localhost:8080/",
#                                      client_id=client_id,
#                                      realm_name="test",
#                                      client_secret_key=client_secret_key
#                                      )

#     try:
#         if refresh_token:
#             token = keycloak_openid.refresh_token(refresh_token)
#         else:
#             token = keycloak_openid.token(grant_type='password', 
#                                           username=username, 
#                                           password=password, 
#                                           totp=otp, 
#                                           scope='openid rabbitmq.read:*/nost/* rabbitmq.write:*/nost/* rabbitmq.configure:*/nost/*')

#         if 'access_token' in token:
#             print(f"\nAccess token retrieved successfully: {token['access_token']}\n")
#             print(f"Access token scope: {token['scope']}\n")
#             print("rabbitmq.write:<vhost>/<exchange>/<routingkey-topic>\n")
#             return token['access_token'], token['refresh_token']
#         else:
#             raise Exception("Error: The request was unsuccessful.")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         raise

def new_access_token():
    keycloak_openid = KeycloakOpenID(server_url="http://localhost:8080/",
                                     client_id=client_id,
                                     realm_name="test",
                                     client_secret_key=client_secret_key
                                     )

    try:
        token = keycloak_openid.token(grant_type='client_credentials',
                                      scope='openid rabbitmq.read:*/nost/firesat.# rabbitmq.write:*/nost/firesat.# rabbitmq.configure:*/nost/firesat.#')

        if 'access_token' in token:
            print(f"\nAccess token retrieved successfully: {token['access_token']}\n")
            print(f"Access token scope: {token['scope']}\n")
            print("rabbitmq.write:<vhost>/<exchange>/<routingkey-topic>\n")
            return token['access_token'], token['refresh_token']
        else:
            raise Exception("Error: The request was unsuccessful.")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

global client_id, username, password, client_secret_key, otp
client_id = input("Enter client ID: ")
# username = input("Enter your username: ")
# password = getpass.getpass("Enter your password: ")
client_secret_key = input("Enter client secret key: ")
# otp = input("Enter OTP: ")

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

exchange_name = input("Enter the exchange name: ")
binding_key = input("Enter the routing/binding key (topic) (e.g., topic.topic2.topic3): ").strip()#.split(' ')
queue_name = 'nost'

main_channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

# result = main_channel.queue_declare('', durable=True, exclusive=False)
# queue_name = result.method.queue
print(f'Queue: {queue_name}')
print(f'Binding key {binding_key}')
# binding_keys = sys.argv[1:]
# if not binding_keys:
#     sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
#     sys.exit(1)

# for binding_key in binding_keys:
main_channel.queue_bind(
    exchange=exchange_name, queue=queue_name, routing_key=binding_key)

print(' [*] Waiting for logs. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(f" [x] {method.routing_key}:{body.decode('utf-8')}")

main_channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)

main_channel.start_consuming()

# main_channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

# if not binding_keys:
#     sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
#     sys.exit(1)

# for binding_key in binding_keys:
#     print(f"Binding key: {binding_key}")
#     main_channel.queue_bind(
#         exchange=exchange_name, queue=queue_name, routing_key=binding_key)

# print(' [*] Waiting for logs. To exit press CTRL+C')

# def callback(ch, method, properties, body):
#     print(f" [x] {method.routing_key}:{body.decode('utf-8')}")

# main_channel.basic_consume(
#     queue=queue_name, on_message_callback=callback, auto_ack=True)

# main_channel.start_consuming()
