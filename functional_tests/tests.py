from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time


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
        self.assertIn("Fund Entry Form", form_header, "\nFund form not found")

    def test_can_input_and_save_fund(self):
        # Need to add a new fund, visit the fund form page
        self.browser.get(f"{self.live_server_url}/fund/add/")

        # input the fund information
        fundbox = self.browser.find_element(By.ID, "fund_fund")
        fundbox.send_keys("C113")
        fundbox.send_keys(Keys.TAB)
        fundbox = self.browser.find_element(By.ID, "fund_name")
        fundbox.send_keys("National Procurement")
        fundbox.send_keys(Keys.TAB)
        fundbox = self.browser.find_element(By.ID, "fund_vote")
        fundbox.send_keys("1")
        fundbox.send_keys(Keys.TAB)
        fundbox.send_keys(Keys.ENTER)

    def test_fund_path_default_to_fund_page(self):
        self.browser.get(f"{self.live_server_url}/fund/")

        # Mario notices the page title and header mention Funds list
        self.assertIn("Fund List", self.browser.title)
        table_id = self.browser.find_element(By.ID, "fund-table").text
        self.assertIn("Funds", table_id)


class CostElementFundTableTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = WebDriver()

    def tearDown(self):
        self.browser.quit()

    def test_can_retreive_fund_list(self):
        # Mario needs to create a new fund.  Let's visite the home page
        self.browser.get(f"{self.live_server_url}/fund/table/")

        # Mario notices the page title and header mention Funds list
        self.assertIn("Fund List", self.browser.title)
        table_id = self.browser.find_element(By.ID, "fund-table").text
        self.assertIn("Funds", table_id)
        time.sleep(10)
        # self.fail("Finish the test!")
