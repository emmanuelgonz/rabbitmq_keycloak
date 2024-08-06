# Setting up RabbitMQ on Local Host with Keycloak as OAuth 2.0 server

## Background

Originally, NOS-T was designed to utilize the Solace PubSub+ Standard Edition event broker with the Message Queuing Telemetry Transport (MQTT) protocol. However, it has now transitioned to using RabbitMQ with the Advanced Message Queuing Protocol (AMQP) protocol.

This page shows how to configure a new standalone RabbitMQ broker on a local host such as a personal machine or a secure local network. The tutorial mostly mirrors the rabbitmq [rabbitmq-oauth2-tutorial guide](https://github.com/rabbitmq/rabbitmq-oauth2-tutorial/tree/main) which provides instructions and tools to get a RabbitMQ message broker Docker container up-and-running on a desktop using Docker Compose, a tool for defining and running multi-container Docker applications. While the capabilities of a locally hosted broker are more limited, it is useful for becoming familiar with the RabbitMQ interface and experimenting with publisher/subscriber behaviors.

## Motivation

The transition from Solace PubSub+ Standard Edition to RabbitMQ was primarily driven by RabbitMQ's advanced queueing capabilities and its open-source nature. Furthermore, updates to NASA's Science Managed Cloud Environment (SMCE) requirements now include two-factor authentication (2FA). Keycloak, an Identity and Access Management (IAM) software, was chosen as the OAuth 2.0 provider due to its open-source nature and robust 2FA capabilities.

## Instructions

Below are instructions for configuring and deploying Keycloak and RabbitMQ.

### Prerequisites

This guide requires the following software to be installed and operational:

- [Docker](https://www.docker.com/get-started/)
- [make](https://www.geeksforgeeks.org/how-to-install-make-on-ubuntu/)

> **Note:**
> Click on the software name for more directions on their installation.

### Clone GitHub Repository

To begin setting up a RabbitMQ broker, clone the [rabbitmq-oauth2-tutorial](https://github.com/rabbitmq/rabbitmq-oauth2-tutorial/tree/main) GitHub repository:

```bash
git clone git@github.com:rabbitmq/rabbitmq-oauth2-tutorial.git
```

### Deploy Keycloak

To deploy a Keycloak broker, run:

```bash
make start-keycloak
```

> **Note:**
> The above command will launch Keycloak with all the required scopes, users and clients preconfigured. Keycloak comes configured with its own signing key, and the [rabbitmq.conf](https://github.com/rabbitmq/rabbitmq-oauth2-tutorial/blob/main/conf/keycloak/rabbitmq.conf) used by ```make start-keycloak``` is also configured with the same signing key.


To access the Keycloak Administration Console, a management interface, navigate to http://localhost:8080.
<!-- ![](/images/AdobeStock_144374589.jpeg) -->

<p align="center"><img src="images/administration_console.png" width="700"></p>
<p align="center"><i>The Keycloak Administration Console enables administrators to manage scopes, users and clients.</i></p>

Click on "Administration Console," which will prompt a login screen. Enter the following credentials:

- Username: admin
- Password: admin

<p align="center"><img src="images/keycloak_login.png" width="700"></p>
<p align="center"><i>The Keycloak Administration Console login screen.</i></p>

There is a dedicated Keycloak realm called ```test``` that is configured with the following three clients:

- ```rabbitmq-client-code``` for the rabbitmq managament ui
- ```mgt_api_client``` to access via the management api
- ```producer``` to access via AMQP protocol.

### Deploy RabbitMQ

To start RabbitMQ run the following two commands:

```bash
export MODE=keycloak
make start-rabbitmq
```

The first commands directs RabbitMQ to be configured using the [rabbitmq.conf](https://github.com/rabbitmq/rabbitmq-oauth2-tutorial/blob/main/conf/keycloak/rabbitmq.conf) file. Below is an example of the contents of this file:

#### RabbitMQ Configuration

```
auth_backends.1 = rabbit_auth_backend_oauth2

log.default.level = debug

management.oauth_enabled = true
management.oauth_client_id = rabbitmq-client-code
management.oauth_scopes = openid profile rabbitmq.tag:administrator
management.oauth_provider_url = http://localhost:8080/realms/test

auth_oauth2.resource_server_id = rabbitmq
auth_oauth2.preferred_username_claims.1 = user_name
auth_oauth2.additional_scopes_key = extra_scope
auth_oauth2.issuer = https://keycloak:8443/realms/test
auth_oauth2.https.peer_verification = verify_none
```

- Authentication Backend:
    - auth_backends.1 = rabbit_auth_backend_oauth2: This line sets RabbitMQ to use OAuth2 as the authentication backend. This is essential for integrating RabbitMQ with OAuth2 providers like Keycloak.

- Logging:
    - log.default.level = debug: This sets the logging level to debug, which is useful for troubleshooting and ensuring that the OAuth2 integration is working correctly.

- Management Plugin Configuration:
    - management.oauth_enabled = true: Enables OAuth2 authentication for the RabbitMQ management plugin.
    - management.oauth_client_id = rabbitmq-client-code: Specifies the OAuth2 client ID used by RabbitMQ to authenticate with the OAuth2 provider.
    - management.oauth_scopes = openid profile rabbitmq.tag:administrator: Defines the scopes required for OAuth2 authentication. These scopes determine the level of access granted to the authenticated user.
    - management.oauth_provider_url = http://localhost:8080/realms/test: Specifies the URL of the OAuth2 provider (in this case, Keycloak).

- OAuth2 Resource Server Configuration:
    - auth_oauth2.resource_server_id = rabbitmq: Sets the resource server ID for RabbitMQ.
    - auth_oauth2.preferred_username_claims.1 = user_name: Defines the claim used to extract the preferred username from the OAuth2 token.
    - auth_oauth2.additional_scopes_key = extra_scope: Specifies additional scopes that might be required.
    - auth_oauth2.issuer = https://keycloak:8443/realms/test: Sets the issuer URL for the OAuth2 tokens, ensuring they are validated correctly.
    - auth_oauth2.https.peer_verification = verify_none: Disables peer verification for HTTPS, which can be useful in development environments but should be used with caution in production.

#### RabbitMQ Management User Interface

To access the RabbitMq management user interface, navigate to http://localhost:15672/#/.

<p align="center"><img src="images/rabbitmq_home.png" width="700"></p>
<p align="center"><i>The RabbitMQ management user interface.</i></p>

Click on "Click here to log in" button, which will prompt a login screen. Enter the following credentials:
- Username: rabbit_admin
- Password: rabbit_admin

<p align="center"><img src="images/rabbitmq_login.png" width="700"></p>
<p align="center"><i>The RabbitMQ management user interface login screen.</i></p>

> **Note:**
> The ```rabbit_admin``` is the single user created in Keycloak with the appropriate scopes to access the management user interface.

#### Access AMQP protocol with Pika

The AMQP protocol can be accessed using the Pika Python library. A Python sample application that receives a token, uses the token to authenticate and publish AMQP messages, and refreshes the token on a live AMQP connection is provided [here](https://github.com/rabbitmq/rabbitmq-oauth2-tutorial/blob/main/pika-client/producer.py).

To run the Python sample application, run:

```bash
pip install pika requests
```

After installing the dependencies, you will need to obtain the client secret key. Ensure you are in the ```test``` realm. Navigate to "Clients" > "Credentials". In the "Client secret" section, you will find the client secret key.

<p align="center"><img src="images/keycloak_secret_key.png" width="700"></p>
<p align="center"><i>Retrieving the client secret key for a specific client in Keycloak.</i></p>

Finally, run the Python sample application using the client ID and client secret key you retrieved above:

```bash
python3 pika-client/producer.py <client ID> <client secret key>
```

<!-- ```bash
python3 pika-client/producer.py producer kbOFBXI9tANgKUq8vXHLhT6YhbivgXxn
``` -->

## OAuth 2.0 Authentication Workflow

When an end user first accesses the management user interface and clicks the "Click here to login" button, they are redirected to the OAuth 2.0 provider for authentication. After successfully authenticating, the user is redirected back to RabbitMQ with a valid JWT token. RabbitMQ then validates the token, identifies the user, and extracts their permissions from the JWT token.

> **Note:**
> The token is passed as a parameter to RabbitMQ commands. However, the connection cannot be used beyond the token’s lifespan, so token refresh is necessary for long-lived connections.


<p align="center"><img src="images/rabbitmq-keycloak.png" width="700"></p>
<p align="center"><i>OAuth 2.0 workflow integrating RabbitMQ as the event broker and Keycloak as the IAM and OAuth 2.0 provider.</i></p>