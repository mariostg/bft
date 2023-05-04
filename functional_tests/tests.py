from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import unittest


class NewVisitorTest(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_retreive_fund_form(self):
        # Need to add a new fund, visit the fund form page
        self.browser.get("http://localhost:8000/fund/add")

        # Mario notices the page title and Form mention Create Fund
        self.assertIn("Fund Form", self.browser.title)
        form_header = self.browser.find_element(By.CLASS_NAME, "form__header").text
        self.assertIn("Fund Form", form_header, "Fund form not found")

    def test_can_retreive_fund_list(self):
        # Mario needs to create a new fund.  Let's visite the home page
        self.browser.get("http://localhost:8000/fund/fund_page")

        # Mario notices the page title and header mention Funds list
        self.assertIn("Fund List", self.browser.title)
        table_id = self.browser.find_element(By.ID, "fund-table").text
        self.assertIn("Funds", table_id)
        # self.fail("Finish the test!")


if __name__ == "__main__":
    unittest.main()
