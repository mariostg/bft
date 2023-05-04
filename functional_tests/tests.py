from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class CostElementFundVisitorTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = WebDriver()

    def tearDown(self):
        self.browser.quit()

    def test_can_retreive_fund_form(self):
        # Need to add a new fund, visit the fund form page
        self.browser.get(f"{self.live_server_url}/fund/add/")

        # Mario notices the page title and Form mention Create Fund
        self.assertIn("Fund Form", self.browser.title)
        form_header = self.browser.find_element(By.CLASS_NAME, "form__header").text
        self.assertIn("Fund Form", form_header, "\nFund form not found")

    def test_can_retreive_fund_list(self):
        # Mario needs to create a new fund.  Let's visite the home page
        self.browser.get(f"{self.live_server_url}/fund_page/")

        # Mario notices the page title and header mention Funds list
        self.assertIn("Fund List", self.browser.title)
        table_id = self.browser.find_element(By.ID, "fund-table").text
        self.assertIn("Funds", table_id)
        # self.fail("Finish the test!")
