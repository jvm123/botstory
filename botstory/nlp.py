"""
(C) 2021 Julian von Mendel <prog@derjulian.net>

nlp.py
====================================
NLP functions
"""

import re
import string
import datetime
import nltk
import dateutil.parser
from nltk.corpus import stopwords
from nltk import word_tokenize

def cleaned_episode(raw_text, custom_stop_words = False):
    """
    Tokenize a string
    Adapted from Alex Mitrani at https://gist.githubusercontent.com/amitrani6/24116fbb08d315799492cdac36de833e/raw/f686cec899c941a45449c316328aee6e4999b40d/NLTK_script_cleaning_function.py

    :param str raw_string: Input text
    :param bool custom_stop_words: Additional stop words to use or None to turn
        off English stop words
    :return: A list of tokens
    :rtype: list
    """

    # Add only English language stopwords and punctuation list together
    stop_words_list = list(string.punctuation)
    if custom_stop_words is not None:
        stop_words_list += stopwords.words('english')

    # If a list of additional custom stopwords are passed add them to the default
    # NLTK stopwords and punctuation list
    if custom_stop_words:
        stop_words_list += custom_stop_words

    # Removes all punctuation
    for char in string.punctuation:
        raw_text = raw_text.replace(char, "")

    # Removes all text between and including brackets and parenthesis with RegEx
    raw_text_no_stage_notes = re.sub("[\(\[].*?[\)\]]", "", raw_text)

    # Remove all text with colons (:), i.e. character line indications
    raw_text_no_stage_notes_or_names = raw_text_no_stage_notes.split(" ")

    for i in raw_text_no_stage_notes_or_names:
        if i.endswith(':') or i == '' or i == ' ':
            raw_text_no_stage_notes_or_names.remove(i)

    # Rejoin all of the text as one string for tokenization
    raw_text_rejoined = " ".join(raw_text_no_stage_notes_or_names)

    # Tokenize the raw text
    token_list = word_tokenize(raw_text_rejoined)

    # Remove stop words and punctuation
    cleaned_and_tokenized_list = [w for w in token_list if w not in stop_words_list]

    return cleaned_and_tokenized_list

def nlp_prefilter(query):
    """
    Prefilter user query

    :param str query: User text
    :return: Improved query for further processing
    :rtype: str
    """

    query_lower = query.lower()

    # TODO: support in sentence replacements and more cases
    if query_lower == "today":
        return datetime.datetime.today().strftime("%m/%d/%Y")

    if query_lower == "tomorrow":
        return (datetime.datetime.today() + datetime.timedelta(days = 1)).strftime("%m/%d/%Y")

    return query

def find_numbers(tokens):
    """
    Find numbers and numeric words in token list

    :param list tokens: List of tokens
    :return: (tokens, numbers)
    :rtype: tuple
    """

    num_words = ["zero","one","two","three","four","five","six","seven",
        "eight","nine","ten","eleven","twelve","thirteen","fourteen",
        "fifteen","sixteen","seventeen","eighteen","nineteen","twenty"]
    numbers = list()
    # TODO: be smart and only consider numbers that are NOT part of a date
    # Problem: The date parser likes to mark numeric values that are NO
    #    dates as dates

    for i, token in enumerate(tokens): #enmerate(tokens_without_date):
        # Replace numeric words in sentence with the actual numeric value
        if token.lower() in num_words:
            number = num_words.index(token.lower())
            tokens[i] = str(number)

    for token in tokens: #tokens_without_date:
        if token.isnumeric():
            numbers.append(int(token))

    return tokens, numbers

def find_nouns(tagged_words, skip_words_in_nlp = 0):
    """
    Compile a list of nouns in tagged word list

    Note: treebankTagger works better than standard nltk.pos_words(). Tags can
    be compiled with
        treebank_tagger = nltk.data.load(
            'taggers/maxent_treebank_pos_tagger/english.pickle')
        tagged_words = treebank_tagger.tag(tokens)

    :param list tagged_words: Tagged word list from an NLTK tagger
    :param int skip_words_in_nlp: During noun search, if the initial word(s) of
        a sentence should not be considered, pass a value > 0. For example
        in a sentence "define word" where "define" is an expected trigger
        word, skipping it will avoid having it misclassified in the noun
        list.
    :return: List of nouns
    :rtype: list
    """

    nouns = list()
    current = False

    for word, pos in tagged_words[skip_words_in_nlp:]:
        if pos[0:2] != 'NN' and current:
            nouns.append(current)
            current = False

        if pos[0:2] != 'NN':
            continue

        if not current:
            current = word
        else:
            # If multiple NN* tags follow, combine the word back into a single noun
            current += " " + word

    if current:
        nouns.append(current)

    return nouns

def identify_word_classes(tokens, word_classes):
    """
    Match word classes to the token list

    :param list tokens: List of tokens
    :param dict word_classes: Dictionary of word lists to find and tag with the
        respective dictionary key
    :return: Matched word classes
    :rtype: list
    """

    if word_classes is None:
        word_classes = []

    classes = set()
    for key in word_classes:
        for token in tokens:
            if token.lower() in word_classes[key]:
                classes.add(key)
    return classes

def nlp_analyze(query, word_classes = None, skip_words_in_nlp = 0):
    """
    Run a number of NLP tasks on a given sentence

    :param str query: Input text
    :param dict word_classes: Dictionary of word lists to find and tag with the
        respective dictionary key
    :param int skip_words_in_nlp: Parameter for find_nouns()
    :return: Dict of format { 'query': cleaned_query, 'tokens': tokens,
        'tags': tagged_words,
        'word_classes': classes, 'numbers': numbers, 'date': date,
        'nouns': nouns, 'lastnoun': lastnoun }
    :rtype: dict
    """

    # Tokenize
    tokens = cleaned_episode(query, None)
    #      tokens = nltk.word_tokenize(query)
    #      print(tokens)

    # Find date in sentence
    date = None
    tokens_without_date = tokens

    try:
        # TODO: improve this bad if clause and the entire date identification part
        # Problem: It often misclassifies numbers as dates, e.g. "2 nights"
        #   is interpreted as date.
        if len(tokens) > 1 or (len(tokens) == 1 and not query.isnumeric()):
            date, tokens_without_date = dateutil.parser.parse(query,
                                                    fuzzy_with_tokens=True)
    except:
        pass

    # Find numbers
    tokens, numbers = find_numbers(tokens)

    # Rebuild string
    cleaned_query = " ".join(tokens)

    # Tag words (treebankTagger works better than standard nltk.pos_words()
    #    function)
    treebank_tagger = nltk.data.load(
        'taggers/maxent_treebank_pos_tagger/english.pickle')
    tagged_words = treebank_tagger.tag(tokens)

    # Compile the final sequence of untagged or tagged as noun words
    #    (uninterrupted)
    nouns = find_nouns(tagged_words, skip_words_in_nlp)

    if len(nouns) == 0:
        lastnoun = None
    else:
        lastnoun = nouns[-1]

    # Identify matching word classes
    classes = identify_word_classes(tokens, word_classes)

    # Return all our preliminary data
    return { 'query': cleaned_query, 'tokens': tokens, 'tags': tagged_words,
        'word_classes': classes, 'numbers': numbers, 'date': date,
        'nouns': nouns, 'lastnoun': lastnoun }
