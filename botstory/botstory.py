"""
(C) 2021 Julian von Mendel <prog@derjulian.net>

Branch and storyline entity management and NLP for accumulating entities from
user responses.
"""

import datetime
from botstory.nlp import nlp_prefilter, nlp_analyze

class BotStory():
    """
    Branch and storyline entity management and NLP.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # State variables used in further class logic
        self.branches = [ ]
        self.current_branch = None # Current storyline branch
        self.open_question = False # Currently in focus entity
        self.training_data = [] # Chatterbot training data
        self.branch_buttons = [] # Buttons for initial branch choice
        self.nlp = None # Last NLP result

        # Branch / entity definition
        self.word_classes = {
            'yes': [ "yes", "ok", "correct", "good" ],
            'no': [ "no", "nope", "incorrect", "wrong", "not", "bad" ],
        }
        self.entities = {}
        self.entity_values = {}

        # Language database
        self.lang = {
            "confirm": "Is this correct?",
            "confirm_wrong": "Sorry, I do not understand. Yes or no?",
            "no_confirm": "Sorry I could not help you. Let's start over.",
        }

    def add_branch(self, branch_name, trigger_words = None, entities = None, \
                   button = None):
        """
        Define a new storyline branch.
        :param str branch_name: Branch name
        :param list trigger_words: List of strings that should be considered
                trigger words for the branch
        :param entities: Dictionary with entity names as key and
                { 'type': '<type>', 'question': 'Question text',
                'buttons': [ 'a', 'b' ] } as value,
                where <type> can be int:<min>:<max>, int_or_str, bool,
                bool_confirm, date or str; The question text can contain
                "{entity_name}" variables. Also, for type 'bool' additional
                settings 'str_true' and 'str_false' can be given to define
                formatting
        :param button: String with a button name to link to the branch, or None
                to not add show button
        """

        self.branches.append(branch_name)

        if isinstance(trigger_words, list):
            self.word_classes['trigger_{}'.format(branch_name)] = trigger_words

        if isinstance(entities, dict):
            self.entities[branch_name] = entities
            self.entity_values[branch_name] = dict.fromkeys(entities, None)

        if self.current_branch is None:
            self.current_branch = branch_name

        if button is not None:
            self.branch_buttons.append(button)

    def add_blind_branches(self, prompts, add_buttons = True):
        """
        Define a new storyline branch.
        :param list prompts: User prompt and bot reponses, in alternately
        :param bool add_buttons: Add buttons for these branches?
        """

        self.training_data.extend(prompts)

        if add_buttons:
            self.branch_buttons.extend(prompts[::2]) # Add every user prompt as button

    def add_blind_branch(self, prompt, reply, add_buttons = True):
        """
        Define a new storyline branch.
        :param str prompt: User prompt to react to
        :param str reply: Bot response to train
        :param bool add_buttons: Add buttons for these branches?
        """

        self.training_data.append(prompt)
        self.training_data.append(reply)

        if add_buttons:
            self.branch_buttons.append(prompt)

        # # Training with variations of the user prompt seems to be overkill
        ###
        # punctuation = list('.,;:?!')
        #
        # # If prompt includes punctuation as final character, remove it
        # if prompt[-1] in punctuation:
        #     prompt = prompt[:-1]
        #
        # # Train prompt in a couple variations
        # punctuation.append('')
        # prompt_variations = [ prompt, prompt.lower(), prompt.upper() ]
        # all_prompts = list(prompt_variations)
        #
        # for prompt_iter in prompt_variations:
        #     for counter in range(0, len(punctuation)):
        #         self.training_data.append(prompt_iter + punctuation[counter])
        #         self.training_data.append(reply)

    def get_training_data(self):
        """
        Retrieve list with conversation flows that the ChatterBot knowledge
        graph can be trained with.
        """

        return self.training_data

    def get_branch_buttons(self):
        """
        Retrieve list of initial branch prompts, that can be displayed as
        buttons to the user.

        :return: List of button names (str)
        :rtype: list
        """

        return self.branch_buttons

    def get_branch_name(self):
        """
        Return current storyline branch
        """
        return self.current_branch

    def enter_branch(self, new_branch_name = "init"):
        """
        Change branch in the storyline and reset entity values

        :return: True if branch exists
        :rtype: bool
        """

        if new_branch_name not in self.branches:
            return False

        self.current_branch = new_branch_name

        # Reset collected entities in target branch
        self.entity_values[new_branch_name] = dict.fromkeys(
                self.entity_values[new_branch_name].keys(), None)
        #print(self.entity_values)

        # Get ready for first entity response
        entities = list(self.entities[new_branch_name].keys())
        if len(entities) == 0:
            self.open_question = None
        else:
            self.open_question = entities[0]

        return True

    def get_entity_values(self):
        """
        Return current storyline branch
        """

        return self.entity_values

    def get_entity_values_formatted(self):
        """
        Retrieve formatted entities for current branch

        :return: User feedback or None if processing completed and no response
            is required
        :rtype: str
        """

        entities_formatted = {}

        # Format available entities, traverse through all that are available
        for key in self.entity_values[self.current_branch]:
            val = self.entity_values[self.current_branch][key]
            entity_type = self.entities[self.current_branch][key]['type'].split(':')

            if entity_type[0] == 'bool' and isinstance(val, bool):
                # The entity definition can include a string to use for True or
                # False when inserting the value into a user prompt
                if 'str_true' in self.entities[self.current_branch][key] and \
                        'str_false' in self.entities[self.current_branch][key]:
                    if val:
                        val = self.entities[self.current_branch][key]['str_true']
                    else:
                        val = self.entities[self.current_branch][key]['str_false']

            if entity_type[0] == 'date' and isinstance(val, datetime.date):
                # Format dates
                val = val.strftime('%d/%m/%Y')

            entities_formatted[key] = val

        return entities_formatted

    def entity_store_append(self, values):
        """
        Load additional values into the currently active storyline branch
        entity value store.

        :param dict values: key<->val dict of entity values
        """

        self.entity_values[self.current_branch] = {
            **self.entity_values[self.current_branch], **values }

    def entity_store_copy(self, source_branch):
        """
        Copy additional values into the currently active storyline branch
        entity value store from another branch as source.

        :param str source_branch: source branch name
        :return: Returns True if source branch was found.
        :rtype: bool
        """

        if source_branch in self.entity_values:
            self.entity_values[self.current_branch] = {
                **self.entity_values[self.current_branch],
                **self.entity_values[source_branch] }
            self.entities[self.current_branch] = {
                **self.entities[self.current_branch],
                **self.entities[source_branch] }
            return True

        return False

    def process_query(self, text, add_word_classes = None):
        """
        Run NLP on a new user message and store it for further processing

        :param str text: User message
        :param dict add_word_classes: Additional word classes to consider
        :return: NLP dict from botstory.nlp.nlp_analyze is returned
        :rtype: dict
        """

        if add_word_classes is None:
            add_word_classes = {}

        query = nlp_prefilter(text)
        self.nlp = nlp_analyze(query,
                {**self.word_classes, **add_word_classes}) # merge dicts)
        return self.nlp

    def identify_intent(self):
        """
        Try to identify the intent in a user prompt.

        :return: The branch name is returned if one can be associated, otherwise
            None
        :rtype: str
        """

        for word_class in self.word_classes:
            if word_class[0:8] == "trigger_" and \
                    word_class in self.nlp['word_classes']:
                branch = word_class[8:]
                return branch

        return None

    def process_entity_in_user_response(self, entity = None):
        """
        Process entities in the user response.

        :param str entity: Entity to identify or None to auto select the most recent
        :return: User feedback or None if processing completed and no response
            is required
        :rtype: str
        """

        nlp = self.nlp
        if entity is None:
            entity = self.open_question
        #print(nlp)
        #print(self.open_question)
        #print(self.current_branch)

        # Assemble entities from user responses

        if entity not in self.entities[self.current_branch] or \
                'type' not in self.entities[self.current_branch][entity]:
            return None

        entity_type = self.entities[self.current_branch][entity]['type'].split(':')

        if entity == self.open_question:
            # Parallel takeup feature: Two entities can be configured to be allowed
            # within one sentence together. Find those entities to consider:
            for key in self.entities[self.current_branch]:
                val = self.entities[self.current_branch][key]
                if 'parallel_takeup' in val and val['parallel_takeup'] == entity:
                    self.process_entity_in_user_response(key)

        # Process type formats:
        # int:<min>:<max>, int_or_str, bool, bool_confirm, date or str
        option = None

        if entity_type[0] == "int" and len(nlp['numbers']) > 0:
            num_min = -9999
            num_max = 9999
            if len(entity_type) > 1:
                num_min = int(entity_type[1])
            if len(entity_type) > 2:
                num_max = int(entity_type[2])

            if nlp['numbers'][-1] >= num_min and nlp['numbers'][-1] <= num_max:
                option = nlp['numbers'][-1]
        elif entity_type[0] == "bool":
            if 'yes' in nlp['word_classes'] and not 'no' in nlp['word_classes']:
                option = True
            elif 'no' in nlp['word_classes'] and not 'yes' in nlp['word_classes']:
                option = False
        elif entity_type[0] == "bool_confirm":
            if 'yes' in nlp['word_classes'] and not 'no' in nlp['word_classes']:
                option = True # Confirmed
            elif 'no' in nlp['word_classes'] and not 'yes' in nlp['word_classes']:
                self.enter_branch('init')
                return self.lang["no_confirm"] # Current branch cancelled
            else:
                return self.lang["confirm_wrong"] # Invalid answer
        elif entity_type[0] == "str":
            if len(nlp['tokens']) <= 3: # If it's very short the user probably typed in just the answer string
                option = nlp['query']
            else: # Extract noun from a full sentence
                option = nlp['lastnoun']
        elif entity_type[0] == "int_or_str":
            if len(nlp['tokens']) <= 3: # If it's very short the user probably typed in just the answer string
                if len(nlp['numbers']) > 0:
                    option = str(nlp['numbers'][0])
                else:
                    option = str(nlp['query'])
            else: # extract noun from a full sentence
                option = str(nlp['lastnoun'])
        elif entity_type[0] == "date" and nlp['date'] is not None:
            option = nlp['date']

        if option is not None:
            self.entity_values[self.current_branch][entity] = option
            self.open_question = None

        #print(self.entity_values[self.current_branch])
        return None # no user prompt results directly from the entity search

    def prompt_for_open_entities(self):
        """
        If there are entities that are still missing, prompt the user for them.

        :return: User prompt
        :rtype: str
        """

        # Prompt user for open entities
        if self.current_branch in self.entities.keys():
            # We are currently in a state in the logic flow, where we are assembling data
            for key in self.entities[self.current_branch]:
                if self.entity_values[self.current_branch][key] is None:
                    self.open_question = key

                    # Format the text question with variables that may be inserted
                    return self.entities[self.current_branch][key]['question']. \
                            format(**self.get_entity_values_formatted())

        return None # we have assembled all entities

    def set_requested_entity(self, entity):
        """
        If the user was prompted for an entity through a prompt somehow decided
        outside of this class logic, but the response shall be processed in this
        class, the prompted entity name can be selected via this function.
        """

        if not isinstance(entity, str):
            return None

        self.open_question = entity
        return True

    def get_last_requested_entity(self):
        """
        Return info on the entity we last asked for in a user prompt

        :return: Entity info of the format provided to add_branch() or None
            if last prompt contained no entity question
        :rtype: dict
        """

        if not isinstance(self.current_branch, str) or \
                not isinstance(self.open_question, str):
            return None

        info = dict(self.entities[self.current_branch][self.open_question])
        info['entity'] = self.open_question
        return info


    def get_last_requested_entity_buttons(self):
        """
        Return buttons for quick response selection to entity questions.

        :return: List of button names (str) if appropriate for the message
        :rtype: list
        """

        open_entity = self.get_last_requested_entity()
        if open_entity is None:
            return None

        if 'buttons' in open_entity:
            return open_entity['buttons']

        entity_type = open_entity['type'].split(':')

        if entity_type[0] == 'bool' or entity_type[0] == 'bool_confirm':
            buttons = [ 'Yes', 'No' ]
        elif entity_type[0] == 'date':
            buttons = [ 'Today', 'Tomorrow' ]
        elif entity_type[0] == 'int':
            if len(entity_type) != 3:
                buttons = []
            else:
                if (int(entity_type[1]) + 6) < int(entity_type[2]):
                    entity_type[2] = int(entity_type[1]) + 6
                buttons = list(range(int(entity_type[1]), int(entity_type[2]) + 1))
        else:
            buttons = []

        return buttons
