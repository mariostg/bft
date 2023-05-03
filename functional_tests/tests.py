from selenium import webdriver
import unittest


class NewVisitorTest(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_start_a_fund_list_and_retreive_it_later(self):
        # Mario needs to create a new fund.  Let's visite the home page
        self.browser.get("http://localhost:8000")

        # Mario notices the page title and header mention Funds list
        self.assertIn("Funds list", self.browser.title)
        self.fail("Finish the test!")


if __name__ == "__main__":
    unittest.main()
