"""
(C) 2021 Julian von Mendel <prog@derjulian.net>

demologicadapter.py
====================================
Chatterbot logic adapter to collect information and run action triggers.
"""

import re
from nltk.metrics.distance import jaro_similarity
from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement

JARO_SIMILARITY_LIMIT = 0.6

class DemoLogicAdapter(LogicAdapter):
    """
    Chatterbot logic adapter
    """

    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)

        output_text = kwargs.get('output_text')
        self.response_statement = Statement(output_text)

        self.reservations_db = kwargs.get('reservations_db')
        self.botclass = kwargs.get('botclass')
        self.botstory = self.botclass.botstory

        self.botstory.add_branch("init",
                [ 'quit', 'exit', 'help', 'bye', 'reconsidered', 'cu' ],
                { })
        self.botstory.add_branch('search',
                [ 'search', 'offer', 'price', 'products', 'offer' ],
                {
                    'date': { 'type': 'date', 'question': "What date are you interested in?" },
                    'quantity': { 'type': 'int:1:20', 'parallel_takeup': 'date', 'question': 'Ok, the date is {date}. What quantity are you interested in?' },
                    'size': { 'type': 'str', 'question': 'What size do you prefer? We offer small, mid and large.', 'buttons': [ 'small', 'mid', 'large' ] },
                })
        self.botstory.add_branch('search_confirm',
                 [ ], # Can't be user triggered, it's programmatically initiated after search
                 {
                     # date and nights we overtake from the previous search branch
                     'action_now': { 'type': 'bool_confirm', 'question': 'Would you like to order now?' },
                 },
                 button = 'Trigger search')
        self.botstory.add_branch('action',
                 [ 'action', 'trigger' ],
                 {
                     # date, quantity and size we overtake from the previous search branch
                     'queryname': { 'type': 'int_or_str', 'question': 'Which option do you prefer?' },
                     'name': { 'type': 'str', 'question': 'What is your name?' },
                     'catering': { 'type': 'bool', \
                                   'question': 'Can we offer you catering?', \
                                   'str_true': '', 'str_false': 'no ' },
                     'confirm_action': { 'type': 'bool_confirm', 'question': 'Let me summarize: You would like to order {quantity} items of {queryname} for {date} with {catering}catering. Your name is {name}. Is this correct?' }
                 })

        # "Blind" branches with no further logic
        self.botstory.add_blind_branches([
            "Can you tell me your contact information?",
            "Sure. Our address is ...",
            "What are your opening times?",
            "Our opening times are ..."
             ])

        # A couple of lang snippets used in the hotel logic
        self.lang = {
            "dontunderstand": "Sorry, I don't understand.",
            "search_results": "On {date} for quantity {quantity} and size {size} I can offer you these options:\n{search_results}\nWould you like to order now?",
            "done": "Thank you! Can I help you with anything else?" }

        self.search_results = None # Used in further class logic

    def can_process(self, statement):
        """
        Chatterbot interface to check whether a statement can be processed by
        this logic adapter.
        """

        # Verify that the user prompt matches our word triggers
        if self.botstory.get_branch_name() != "init":
            # A story branch is already active
            return True

        nlp = self.botstory.process_query(statement.text,
                { 'trigger_any': [ 'search', 'price', 'offer', 'action', 'product', 'products' ] })

        if 'trigger_any' in nlp['word_classes']:
            return True

        return False

    def switch_branch(self):
        """
        Try to identify the intent in a user prompt and switch branch if
        adequate.

        NPLEntityAccumulation does the main job, but business logic related
        processing needs to take place here.

        :return: User feedback or None if processing completed and no response
            is required
        :rtype: str
        """

        branch = self.botstory.get_branch_name()
        suggested_branch = self.botstory.identify_intent()
#print("current branch: {}".format(branch))
#print("suggested branch: {}".format(suggested_branch))

        if branch != "init" and suggested_branch == 'init':
            self.botstory.enter_branch('init')
            return self.lang['done']

        if branch == "init" and suggested_branch == 'search':
            self.botstory.enter_branch(suggested_branch)
            return self.botstory.prompt_for_open_entities()

            # Use a more colorful free-style opening
            #self.botstory.set_requested_entity('date')
            #return self.lang["start_search"]

        return None

    def process_entity_in_user_response(self):
        """
        Process entities in the user response.

        NPLEntityAccumulation does the main job, but business logic related
        processing needs to take place here.

        :return: User feedback or None if processing completed and no response
            is required
        :rtype: str
        """

        text = self.botstory.process_entity_in_user_response()
        branch = self.botstory.get_branch_name()
        entity_values = self.botstory.get_entity_values()

        if branch != 'action' or branch not in entity_values or \
                'queryname' not in entity_values[branch]:
            return text

        # Match user choice with actual search results
        queryname = entity_values[branch]['queryname']
        if queryname is None:
            return text

        if queryname.isnumeric():
            i = int(queryname) - 1
        elif queryname != "":
            # Note: Jaro similarity is more suitable than Levenshtein distance here
            best_match = -1
            best_match_score = 0
            for i, room in enumerate(self.search_results):
                score = jaro_similarity(room['name'], queryname)
                if score > best_match_score:
                    best_match_score = score
                    best_match = i

            if best_match_score > JARO_SIMILARITY_LIMIT: # Don't match things that don't match
                i = best_match

        # Save updated entities back
        if 0 <= i < len(self.search_results):
            entity_values[branch]['queryname'] = self.search_results[i]["name"]
            self.botstory.entity_store_append(entity_values[branch])

        return text

    def trigger_branch_action(self):
        """
        If all entities have been assembled, process the actual user intent
        and interface it to the ERP.

        :return: User feedback or None if processing completed and no response
            is required
        :rtype: str
        """

        branch = self.botstory.get_branch_name()
        entity_values = self.botstory.get_entity_values()

        # We have all data and the confirmation! Trigger actions.
        #print(entity_values)

        # if branch == "cancel":
        #     roomid = self.search_results[0]["room"]
        #     self.reservations_db.cancel(room, entity_values['date'], entity_values['name'])
        #     self.reset_entity_values() # start anew if another conversation follows
        #     return self.question["done"]

        if branch == "search":
            # Search parameters are assembled, perform search
            #self.search_results = search( \
            #        entity_values['search']['quantity'], \
            #        None, entity_values['search']['size'], \
            #        entity_values['search']['date'])
            self.search_results = [ { "id": 1, "name": "Rooftop bar", "price": 246 },
                                    { "id": 2, "name": "Beach bar", "price": 369 },
                                     { "id": 3, "name": "Food truck", "price": 123 } ]

            if len(self.search_results) == 0:
                # No rooms with given parameters are available
                self.botstory.enter_branch('init')
                return self.lang["no_search_results"]

            # Print search results
            search_results = []
            self.botclass.button_overwrite['queryname'] = []
            i = 1
            for item in self.search_results:
                name_safe = "".join([c for c in item['name'].lower() if re.match(r'\w', c)]) # alphanumeric_
                vals_formatted = {'i': i, 'name': item['name'],
                                  'shortname': name_safe, 'price': item['price']}
                search_results.append("\t{i}) {name} for {price} EUR\n".format(**vals_formatted))
                self.botclass.button_overwrite['queryname'].append(
                    '<b>{name}</b><!--<img src="/static/img/{shortname}.jpg" />-->'.format(**vals_formatted))
                i += 1

            entities_formatted = self.botstory.get_entity_values_formatted()
            entities_formatted['search_results'] = "".join(search_results)

            # Have the user confirm whether she wants to book
            self.botstory.enter_branch('search_confirm')

            return self.lang["search_results"].format(**entities_formatted)

        if branch == "search_confirm":
            # User would like to move on with booking
            self.botstory.enter_branch('action')

            # Copy over entities that were accumulated in search branch
            self.botstory.entity_store_copy('search')

            # Prompt for missing entities
            prompt = self.botstory.prompt_for_open_entities()
            return prompt

        if branch == "action":
            # Parameters are assembled, identify the item to trigger
            #self.search_results = search( \
            #    entity_values['book']['quantity'], entity_values['book']['queryname'], \
            #    entity_values['book']['size'], entity_values['book']['date'])
            #if len(self.search_results) == 0: # Item vanished since search results were shown?!
            #    self.botstory.enter_branch('init')
            #    return self.question["item_vanished"]

            # Book the item for the given date
            #id = self.search_results[0]["id"]
            #self.reservations_db.book(id, entity_values['book']['date'], \
            #    entity_values['book']['quantity'], entity_values['book']['name'], \
            #    entity_values['book']['catering'])
            self.botstory.enter_branch('init')
            return self.lang["done"]

        return None

    def process(self, statement, additional_response_selection_parameters = None):
        """
        Chatterbot interface for processing of statements:
        If adequate, perform any of the following:
        a) Switch storyline  branch
        b) Assemble entities
        c) Prompt user to provide additional entities
        d) Trigger actions when all entities are available
        """

        # Perform NLP
        self.botstory.process_query(statement.text)
        #nlp = self.botstory.process_query(statement.text)
        #print(nlp)
        #print(self.botstory.get_last_requested_entity())

        self.response_statement.confidence = 1

        self.response_statement.text = self.switch_branch()
        if self.response_statement.text is not None:
            return self.response_statement

        self.response_statement.text = self.process_entity_in_user_response()
        if self.response_statement.text is not None:
            return self.response_statement

        self.response_statement.text = self.botstory.prompt_for_open_entities()
        if self.response_statement.text is not None:
            return self.response_statement

        self.response_statement.text = self.trigger_branch_action()
        if self.response_statement.text is not None:
            return self.response_statement

        self.response_statement.text = self.lang['dontunderstand']
        self.response_statement.confidence = 0.1
        return self.response_statement

