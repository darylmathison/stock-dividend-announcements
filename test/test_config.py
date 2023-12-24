import unittest
import os
from stock_news_gathering.config import Config


os.environ["FOR_TEST"] = "whyme"
os.environ["PAPER"] = "FALSE"
os.environ["ME"] = "TRUE"


class TestConfig(unittest.TestCase):
    def test_construct_with_default_file(self):
        c = Config("test/default.json")
        self.assertEqual("42", c.testme)

    def test_with_missing_value(self):
        try:
            c = Config()
            c.testme
            self.fail("Had a value that did not exist")
        except AttributeError as ae:
            pass

    def test_environment_variables_lowercase(self):
        c = Config()
        self.assertEqual(
            "whyme",
            c.for_test,
            "Couldn't find a lowercase existing value in env variables",
        )

    def test_environment_variables_uppercase(self):
        c = Config()
        self.assertEqual("whyme", c.FOR_TEST, "Can't find uppercase env variable")

    def test_environment_variable_mixed_case(self):
        c = Config()
        self.assertEqual("whyme", c.FoR_TesT, "Can't find mixed case env variable")

    def test_as_bool_when_FALSE(self):
        c = Config()
        self.assertFalse(c.as_bool("PAPER"))

    def test_as_bool_when_TRUE(self):
        c = Config()
        self.assertTrue(c.as_bool("ME"))


if __name__ == "__main__":
    unittest.main()
