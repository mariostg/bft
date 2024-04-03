import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webdriver import WebDriver


class CostElementFundFormTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = WebDriver()

    def tearDown(self):
        self.browser.quit()

    def test_can_retreive_fund_form(self):
        # Need to add a new fund, visit the fund form page
        self.browser.get(f"{self.live_server_url}/fund/fund-add/")

        # Mario notices the page title and Form mention Create Fund
        self.assertIn("Fund Form", self.browser.title)
        form_header = self.browser.find_element(By.CLASS_NAME, "form__header").text
        self.assertIn("Fund Entry Form", form_header, "\nFund form not found")

    def test_can_input_and_save_fund(self):
        # Need to add a new fund, visit the fund form page
        self.browser.get(f"{self.live_server_url}/fund/fund-add/")

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
        self.browser.get(f"{self.live_server_url}/fund/fund-table/")

        # Mario notices the page title and header mention Funds list
        self.assertIn("Fund List", self.browser.title)
        table_id = self.browser.find_element(By.ID, "fund-table").text
        self.assertIn("Funds", table_id)
        time.sleep(1)
        # self.fail("Finish the test!")


class CostElementSourceFormTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = WebDriver()

    def tearDown(self):
        self.browser.quit()

    def test_can_retreive_source_form(self):
        # Need to add a new fund, visit the fund form page
        self.browser.get(f"{self.live_server_url}/source/source-add/")

        # Mario notices the page title and Form mention Create Fund
        self.assertIn("Source Form", self.browser.title)
        form_header = self.browser.find_element(By.CLASS_NAME, "form__header").text
        self.assertIn("Source Entry Form", form_header, "\nSource form not found")

    def test_can_input_and_save_source(self):
        # Need to add a new fund, visit the fund form page
        self.browser.get(f"{self.live_server_url}/source/source-add/")

        # input the fund information
        fundbox = self.browser.find_element(By.ID, "id_source")
        fundbox.send_keys("Basement")
        fundbox.send_keys(Keys.TAB)
        fundbox.send_keys(Keys.ENTER)

    def test_source_path_default_to_source_page(self):
        self.browser.get(f"{self.live_server_url}/source/source-table/")

        # Mario notices the page title and header mention Funds list
        self.assertIn("Source Table", self.browser.title)
        table_id = self.browser.find_element(By.ID, "source-table").text
        self.assertIn("Sources", table_id)


class CostElementSourceTableTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = WebDriver()

    def tearDown(self):
        self.browser.quit()

    def test_can_retreive_source_list(self):
        # Mario needs to create a new source.  Let's visite the home page
        self.browser.get(f"{self.live_server_url}/source/source-table/")

        # Mario notices the page title and header mention Sources list
        self.assertIn("Source Table", self.browser.title)
        table_id = self.browser.find_element(By.ID, "source-table").text
        self.assertIn("Sources", table_id)
        time.sleep(5)
        # self.fail("Finish the test!")


class CostElementFundCenterTableTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = WebDriver()

    def tearDown(self):
        self.browser.quit()

    def test_can_retreive_fund_center_list(self):
        # Mario needs to create a new fund.  Let's visite the home page
        self.browser.get(f"{self.live_server_url}/fundcenter/fundcenter-table/")

        # Mario notices the page title and header mention Funds list
        self.assertIn("Fund Center Table", self.browser.title)
        table_id = self.browser.find_element(By.ID, "fundcenter-table").text
        self.assertIn("Fund Centers", table_id)
        time.sleep(1)
        # self.fail("Finish the test!")


class CostElementFundCenterFormTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = WebDriver()

    def tearDown(self):
        self.browser.quit()

    def test_can_retreive_fund_center_form(self):
        # Need to add a new fund, visit the fund form page
        self.browser.get(f"{self.live_server_url}/fundcenter/fundcenter-add/")

        # Mario notices the page title and Form mention Create Fund
        self.assertIn("Fund Center Form", self.browser.title)
        form_header = self.browser.find_element(By.CLASS_NAME, "form__header").text
        self.assertIn("Fund Center Entry Form", form_header, "\nFund Center form not found")

    def test_can_input_and_save_fund(self):
        # Need to add a new fund, visit the fund form page
        self.browser.get(f"{self.live_server_url}/fundcenter/fundcenter-add/")

        # input the fund information
        fundbox = self.browser.find_element(By.ID, "id_fundcenter")
        fundbox.send_keys("Basement")
        fundbox.send_keys(Keys.TAB)
        fundbox = self.browser.find_element(By.ID, "id_shortname")
        fundbox.send_keys("Basement")
        fundbox.send_keys(Keys.TAB)
        fundbox.send_keys(Keys.ENTER)

    def test_fund_center_path_default_to_fund_center_page(self):
        self.browser.get(f"{self.live_server_url}/fundcenter/fundcenter-table")

        # Mario notices the page title and header mention Funds list
        self.assertIn("Fund Center Table", self.browser.title)
        table_id = self.browser.find_element(By.ID, "fundcenter-table").text
        self.assertIn("Fund Centers", table_id)
