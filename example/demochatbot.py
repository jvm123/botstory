"""
(C) 2021 Julian von Mendel <prog@derjulian.net>

demochatbot.py
====================================
Chatbot demo
"""

import tempfile
import botstory.botclass

# Base class for the specific chatbot
class DemoChatBot(botstory.botclass.BotClass):
    """
    Main class for chatbot
    """

    def __init__(self, tmp_erp = False):
        # Chatbot
        super().__init__(welcome_msg = 'Hi. How may I help you?',
                logic_adapters = [
                   'example.demologicadapter.DemoLogicAdapter',
                   'botstory.definitionslogicadapter.DefinitionsLogicAdapter'
                ], chatbot_vars = { })

