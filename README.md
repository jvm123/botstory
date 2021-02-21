# BotStory

## Intro

This repository contains the BotStory class, an abstract interface to specify storyline branching and entity type schemas for the simple design of natural language chatbot conversation flows. It is based on [ChatterBot](https://github.com/gunthercox/ChatterBot) and [NLTK](https://www.nltk.org).

A demo chatbot is provided in the example folder.
A command line and a [Flask](https://flask.palletsprojects.com/en/1.1.x/) based web interface is also provided. The web interface displays storyline dependent default selections.

![Web interface screenshot](flask_screenshot.png)

## Example conversation

Here's an example for a natural language conversation. While the conversation offers limited sense, the storyline flow is easily adapted for individual use cases.
```
> Are you sentient?
Sort of.
> Tell me a joke.
Did you hear the one about the mountain goats in the andes? It was "ba a a a a a d".
> What is a car?
A motor vehicle with four wheels; usually propelled by an internal combustion engine. A wheeled vehicle adapted to the rails of railroad. The compartment that is suspended from an airship and that carries personnel and the cargo and the power plant. Where passengers ride up and down. A conveyance for passengers or freight on a cable railway.

--- new conversation ---

> I would like to order one of your products please.
What date are you interested in?
> The date is 2020-12-01.
Ok, the date is 01/12/2020. What quantity are you interested in?
> 1 item please.
What size do you prefer? We offer small, mid and large.
> any
On 01/12/2020 for quantity 1 and size any I can offer you these options:
	1) Rooftop bar for 246 EUR
	2) Beach bar for 369 EUR
	3) Food truck for 123 EUR

Would you like to order now?
> Yes
Which option do you prefer?
> I would prefer the beach bar.
What is your name?
> My name is Peter Frank.
Can we offer you catering?
> No catering.
Let me summarize: You would like to order 1 items of Beach bar for 01/12/2020 with no catering. Your name is Peter Frank. Is this correct?
> Yes, that's correct.
Thank you! Can I help you with anything else?
> Bye.
Bye. It was a pleasure serving you!
```

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
```

### Running

Run command line interface with
```
make run
```

Run the web UI with
```
make flask
```
The web application runs on part 8080 by default.

Display other available commands by using
```
make help
```

