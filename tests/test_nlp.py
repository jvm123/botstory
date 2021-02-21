import sys
import os
import unittest
import string
from botstory.nlp import nlp_analyze

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestNLP(unittest.TestCase):
    def test_entity_identification(self):
        word_classes = {
                'icecreamflavours': ['vanilla', 'chocolate' ],
                'vehicles': ['car', 'motorcycle' ]}

        # Identify nouns in sentences
        #      nlp = nlp_analyze("I would like to book a single room on Jan 1,
        #            2021 for 2 nights on the name Michael Jackson")
        #      print(nlp)

        nlp = nlp_analyze("My name is Michael Jackson")
        self.assertEqual(string.capwords(nlp["lastnoun"]), "Michael Jackson")

        nlp = nlp_analyze("I am Michael Jackson")
        self.assertEqual(string.capwords(nlp["lastnoun"]), "Michael Jackson")

        nlp = nlp_analyze("Michael Jackson")
        self.assertEqual(string.capwords(nlp["lastnoun"]), "Michael Jackson")

        #      nlp = nlp_analyze("Define car") # tagging doesn't work
        #      self.assertEqual(str(nlp["lastnoun"]), "car")

        nlp = nlp_analyze("Define car", [], 1) # skip first word
        self.assertEqual(str(nlp["lastnoun"]), "car")

        nlp = nlp_analyze("What does 'car' mean?", word_classes)
        self.assertEqual(str(nlp["lastnoun"]), "car")

        # Match word classes to sentence
        self.assertTrue("vehicles" in nlp["word_classes"])

        # Identify numbers in a sentence
        nlp = nlp_analyze("I have 256, 2 and three apples.")
        self.assertEqual(nlp["numbers"][0], 256)
        self.assertEqual(nlp["numbers"][1], 2)
        self.assertEqual(nlp["numbers"][2], 3)

        # Find multiple nouns and multiple numbers in a sentence
        nlp = nlp_analyze("Two chocolate and 1 vanilla are my favorite", word_classes)
        self.assertEqual(nlp["numbers"][0], 2)
        self.assertEqual(nlp["numbers"][1], 1)
        self.assertEqual(nlp["nouns"][0], "chocolate")
        self.assertEqual(nlp["nouns"][1], "vanilla")
        self.assertTrue("icecreamflavours" in nlp["word_classes"])

        # Identify dates in sentences
        nlp = nlp_analyze("Today is January 1, 2047")
        self.assertEqual(str(nlp["date"]), "2047-01-01 00:00:00")

        nlp = nlp_analyze("Let's meet on Nov 12 2021.")
        self.assertEqual(str(nlp["date"]), "2021-11-12 00:00:00")

        #nlp = nlp_analyze("Let's meet on Nov 12, 2021 for 2 days.") # fails
        #self.assertEqual(str(nlp["date"]), "2021-11-12 00:00:00")

        nlp = nlp_analyze("Let's meet on Nov 12, 2021 for two days.")
        self.assertEqual(str(nlp["date"]), "2021-11-12 00:00:00")

        nlp = nlp_analyze("Let's meet on 12.11.2021.")
        self.assertEqual(str(nlp["date"]), "2021-12-11 00:00:00")

        nlp = nlp_analyze("Let's meet on December 3rd 2020.")
        self.assertEqual(str(nlp["date"]), "2020-12-03 00:00:00")
