"""
(C) 2021 Julian von Mendel <prog@derjulian.net>

botstory.py
====================================
Main class for a chatbot that covers ChatterBot init,
retrieving chatterbot responses and training the ChatterBot knowledge graph.
"""

from chatterbot import ChatBot
import chatterbot.filters
from chatterbot.trainers import ListTrainer
#from chatterbot.trainers import UbuntuCorpusTrainer
from chatterbot.trainers import ChatterBotCorpusTrainer

from botstory.botstory import BotStory

BOT_NAME='Ron' # Bot name passed on in ChatterBot Statement objects

class BotClass:
    """
    Main class for chatbot

    :param ChatterBot chatbot: ChatterBot class, or None if a new one should be
            created
    :param str welcome_msg: Welcome message to print
    :param list logicadapters: Additional logic adapters to configure
            ChatterBot with
    :param dict chatbot_vars: Dict with additional data to provide to logic adapters
    """

    def __init__(self, chatbot = None, welcome_msg = "Hi.", \
                 logic_adapters = None, chatbot_vars = None, \
                 database_uri = 'db/database.sqlite3'):
        # Story dialog management
        self.botstory = BotStory()
        self._build_default_story()
        self.button_overwrite = {} # UI buttons provided by business logic

        # Chat log
        self.chatlog = [ ]
        self.welcome_msg = welcome_msg
        if isinstance(self.welcome_msg, str):
            self.chatlog_append(self.welcome_msg, bot_user=True)

        # Chatterbot init
        if logic_adapters is None:
            logic_adapters = []

        logic_adapters.extend([
            {
                'import_path': 'chatterbot.logic.BestMatch',
                'default_response': 'I am sorry, but I do not understand.',
                'threshold': 0.90
            },
            #         'chatterbot.logic.MathematicalEvaluation',
            #         'chatterbot.logic.TimeLogicAdapter'
        ])

        if chatbot_vars is None:
            chatbot_vars = {}

        if chatbot is not None:
            self.chatbot = chatbot
        else:
            self.chatbot = ChatBot(BOT_NAME,
                read_only=True,
                logic_adapters=logic_adapters,
                filters=[chatterbot.filters.get_recent_repeated_responses],
                input_adapter="chatterbot.input.VariableInputTypeAdapter",
                output_adapter="chatterbot.output.OutputAdapter",
                storage_adapter='chatterbot.storage.SQLStorageAdapter',
                database_uri='sqlite:///{}'.format(database_uri),
                botclass=self,
                **chatbot_vars)

    def _build_default_story(self):
        """
        Set up a few default conversation lines
        """

        self.botstory.add_blind_branches([
                "Start over",
                "Okay. Let's start over.",
                "New session",
                "Okay. Let's start over.",
                "Quit",
                "Okay. Let's start over.",
                "quit",
                "Okay. Let's start over."
            ], add_buttons = False)
        self.botstory.add_blind_branches([
                "Hi",
                "Hello there!",
                "Hey friend.",
                "Hey.",
                "Hello",
                "Hi there!",
                "Are you my friend?",
                "Sure!",
                "ok",
                "Ok.",
                "Can you help me?",
                "What would you like to talk about?",
                "Thanks.",
                "You're welcome.",
                "Thanks you.",
                "You're welcome.",
                "Thanks you very much.",
                "You're welcome.",
                "Thank you.",
                "You're welcome.",
                "See you.",
                "Bye. It was a pleasure serving you!",
                "Have a nice day.",
                "Bye. It was a pleasure serving you!",
                "Bye.",
                "Bye. It was a pleasure serving you!"
            ], add_buttons = False)

    def process_query(self, query):
        """
        Process a user prompt and return the chatbot response

        :param str query: Input text
        :return: Chatbot response
        :rtype: str
        """

        self.chatlog_append(query)

        response = str(self.chatbot.get_response(query))
        self.chatlog_append(response, bot_user = True)

        return response

    def get_chatlog(self):
        """
        Retrieve chat log

        :return: List of all past user prompts and bot replies
        :rtype: list
        """

        return self.chatlog

    def chatlog_append(self, msg, bot_user = False):
        """
        Internal helper function to store user prompts or bot replies in chat log
        """

        if bot_user:
            msg = '*{}*'.format(msg)
        self.chatlog.append(msg)

    def train(self):
        """
        Training of the chatterbot knowledge graph

        :return: True if training has been completed fully, False otherwise
        :rtype: bool
        """
        # Careful, UbuntuCorpus takes over 10GB of memory
        #   trainer = UbuntuCorpusTrainer(chatbot)
        #   trainer.train()

        self.chatbot.storage.drop()

        # Train with random conversations from English language corpus
        trainer = ChatterBotCorpusTrainer(self.chatbot)
        trainer.train("chatterbot.corpus.english")

        # Train with storyline data from BotStory
        trainer = ListTrainer(self.chatbot)
        trainer.train(self.botstory.get_training_data())

        return True

        # Train with conversations from json file
        #with open(CONVERSATIONS_DATA, "rb") as f:
        #    conversation = json.load(f)
        #    print(conversation)
        #    trainer.train(conversation)
        #    return True

        #return False

    def get_template_data(self):
        """
        Provide data for UI templates
        """

        return { 'welcome': self.welcome_msg,
                'home_buttons': self.botstory.get_branch_buttons() }

    def get_buttons_for_last_response(self):
        """
        Return buttons for quick response selection to entity questions.

        :return: List of button names (str) if appropriate for the message
        :rtype: list
        """

        info = self.botstory.get_last_requested_entity()
        if not isinstance(info, dict) or 'entity' not in info:
            # Nothing is currently going on in the story
            return []
        entity = info['entity']

        if entity in self.button_overwrite and \
                isinstance(self.button_overwrite[entity], list):
            # This is a way for business logic modules to provide their own
            # set of button selections
            buttons = list(self.button_overwrite[entity])
            del self.button_overwrite[entity]
            return buttons

        buttons = self.botstory.get_last_requested_entity_buttons()
        return buttons
