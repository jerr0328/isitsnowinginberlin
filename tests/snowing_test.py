import unittest

# import os
# import flask
# from isitsnowinginberlin import isitsnowinginberlin


class SnowingTests(unittest.TestCase):
    def test_truthiness(self):
        five = 5
        self.assertEqual(five, 5)


if __name__ == "__main__":
    unittest.main()
