"""
(C) 2021 Julian von Mendel <prog@derjulian.net>

definitionslogicadapter.py
====================================
Chatterbot logic adapter to pull definitions from NLTK wordnet for user prompts
such as "What is a car?" or "Explain what a hotel is." or "Define reservation."
"""

from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement
from nltk.corpus import wordnet as wn
from botstory.nlp import nlp_analyze

class DefinitionsLogicAdapter(LogicAdapter):
    """
    Chatterbot logic adapter to pull definitions from NLTK wordnet for user prompts
    """

    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)

        output_text = kwargs.get('output_text')
        self.response_statement = Statement(output_text)

        # Trigger words
        self.word_classes = {
            'triggerAny': ['what', 'define', 'explain' ] }

    def can_process(self, statement):
        """
        Chatterbot interface to check whether a statement can be processed by
        this logic adapter.
        """
        # Verify that the user prompt matches our word triggers
        query = nlp_analyze(statement.text, self.word_classes)

        if 'triggerAny' in query['word_classes']:
            return True

        return False

    def process(self, statement, additional_response_selection_parameters = None):
        """
        Chatterbot interface for processing of statements: Identify word a
        user wishes to defined and respond with the definition from WordNet if
        one can be found.
        """

        query = nlp_analyze(statement.text, self.word_classes, 1) # skip first word

        # noun = nlp['tokens'][-1] # preliminary solution to avoid proper word tagging
        noun = query['lastnoun']
        #print(noun)

        # Let NLTK wordnet identify common synonyms
        if noun is None:
            synsets = []
        else:
            synsets = wn.synsets(noun)

        if len(synsets) == 0:
            # No definition found; return no result with low confidence
            self.response_statement.confidence = 0.1
            self.response_statement.text = "Sorry, I don't understand."
        else:
            # Retrieve word definitions from NLTK wordnet
            definitions = list()
            for i in synsets:
                definitions.append(wn.synset(i.name()).definition().capitalize())

            self.response_statement.confidence = 0.9
            self.response_statement.text = ". ".join(definitions) + "."

        return self.response_statement
