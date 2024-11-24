# Lync Chat Server
A simple chat app with direct messaging functionality where a user can start 
a chat with another user and share text messages within the chat. This 
application exposes HTTP API endpoints as well as WebSocket endpoints for
real-time communication between server and client.


## Setup
The Lync Chat app is comprised of two separate backend and frontend components.
The codebase for the backend application is maintained in this repo while the 
frontend application is maintained [here][1].

[1]: <https://github.com/justinharry4/lync-chat-client>

The steps to set up the server application in a development environment are listed
below:

1. Clone the repository
    ```
    git clone http://github.com/justinharry4/lync-chat-server.git
    ```

    ```
    cd lync-chat-server
    ```

2. Install pipenv for virtual environment and dependency management
    ```
    pip install pipenv
    ```

3. Create virtual environment and install project dependencies
   (Python version 3.10 or higher is recommended)
    ```
    pipenv install
    ```

4. Activate virtual environment
    ```
    pipenv shell
    ```

5. Run database migrations
    ```
    python manage.py migrate
    ```

6. Populate database with dummy user data
    ```
    python manage.py createchatcontext
    ```

7. Start the server application
    ```
    python manage.py runserver
    ```

## Usage
After the server is set up and running locally, the user-facing component of the
Lync Chat app, the client, must then be set up and run locally. The client 
application (Chat UI) can then be accessed via a web browser. Setup instructions
for the client app can be found in the [chat client repo][2].

[2]: <https://github.com/justinharry4/lync-chat-client?#setup>


## Features
- Private chats between two users (Direct messaging)
- Text messaging

There is currently no support for file sharing and group chats involving multiple 
users. While a base framework on which these features may be built exists, no
concrete implementation has been adopted as of now.


## Application Design
The lync chat server Django project is comprised of three Django apps: `chat`,
`dispatcher` and `core`.

The `chat` app defines the entities involved in the chat system and exposes HTTP
API endpoints which provide client access to chat resources.

The `dispatcher` app is a reusable app based on Django Channels. It provides a 
structured framework that allows for the definition of WebSocket event handlers 
using a custom user-defined system of status codes.

The `core` app encapsulates real-time message processing logic within the chat 
system and exposes a WebSocket endpoint for two-way communication between the 
server and a client.


## Note
The chat server application in this repository is **not production ready**. It
was built primarily to learn and practice API design and development concepts
with Django.

That being said, any contributions to the project are welcome!