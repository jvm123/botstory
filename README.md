# BotStory

## Intro

Small talk capable chatbot based on Chatterbot to facilitate information requests and action triggers. An abstract interface to specify storyline branching and entity type schemas is provided by the BotStory class. A web interface with buttons for storyline dependent default selections is provided.

## Using Docker

You can build a Docker image and run the application from there:
```
make docker # Build image
make run-docker # Run command line mode
make run-docker-flask # Run web UI
```

During the build of the docker image, necessary requirements are installed, the ChatterBot knowledge graph is trained and the unit tests are executed.

After initiating the Flask app, you should be able to access the web UI at http://localhost:8080/

## Manual setup

### Requirements

Prepare necessary requirements with
```
apt update
apt install python3 python3-pip
make install
'''

### Running

Run command line interface with
'''
make run
'''

Run the web UI with
'''
make flask
'''
The web application runs on part 8080 by default.

Display other available commands by using
'''
make help
'''

