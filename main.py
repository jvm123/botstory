"""
(C) 2021 Julian von Mendel <prog@derjulian.net>

main.py
====================================
This is the main program for the command line chatbot interface
"""

import sys
import logging

from example.demochatbot import DemoChatBot

TEST_CONVERSATIONS_FILE = 'tests/conversations.txt'
logging.basicConfig(level=logging.CRITICAL)
#logging.basicConfig(level=logging.INFO)

def main_cli():
    """
    Show interactive command line chatbot
    """

    # Set up chatbot class and show welcome messages if available
    chatbot = DemoChatBot()
    for msg in chatbot.get_chatlog():
        print(msg)
    print()

    while True:
        try:
            # Prompt for user message
            query = input("> ")

            # Print response
            response = chatbot.process_query(query)
            print(response)
            print()

            # Quit program if user seems to intend to quit
            if query.lower() == "bye" or query == "exit" or query == "quit":
                break

        # Press ctrl-c or ctrl-d on the keyboard to exit
        except (KeyboardInterrupt, EOFError, SystemExit):
            break

def main_sim():
    """
    Load prompts from txt file and print bot responses
    """

    current_chatbot = DemoChatBot(tmp_erp = True)

    with open(TEST_CONVERSATIONS_FILE, "r") as conversation_input:
        for line in conversation_input:
            if line.strip() == "":
                # New conversation, reset data
                current_chatbot = DemoChatBot(tmp_erp = True)
                print("\n--- new conversation ---\n")
                continue

            # Process user prompt and print response
            print("> {}".format(line.strip()))
            response = current_chatbot.process_query(line)
            print(response)

        conversation_input.close()

# Command line interface
if __name__ == "__main__":
    if len(sys.argv) == 1: # No parameter: start up the chatbot
        main_cli()
    elif sys.argv[1] == "--train": # Train the knowledge graph of the chatbot
        print("Training...")
        chatbot_to_train = DemoChatBot()
        chatbot_to_train.train()
        print("Done")
    elif sys.argv[1] == "--sim": # Load stored up user prompts and print bot answers
        main_sim()
    else:
        print("usage: {} [--train|--sim]".format(sys.argv[0]))
