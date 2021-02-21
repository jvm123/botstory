import sys
import os
import unittest
from botstory.botclass import BotClass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestChatbot(unittest.TestCase):
    def test_chatbot(self):
        chatbot = BotClass()
        # Check whether the bot is able to respond to a simple phrase from conversations.json
        self.assertEqual(chatbot.process_query("Thank you."), "You're welcome.")
        self.assertEqual(chatbot.process_query("thank you"), "You're welcome.")
