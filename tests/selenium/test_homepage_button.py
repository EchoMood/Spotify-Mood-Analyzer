import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class HomePageButtonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use your deployed site URL
        cls.base_url = 'https://spotify-mood-analyzer-production.up.railway.app'

        # Set up headless browser
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        cls.driver = webdriver.Chrome(options=options)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_get_started_button_clickable(self):
        # Step 1: Open homepage
        self.driver.get(f'{self.base_url}/')

        # Step 2: Wait for Get Started button to appear and click it
        button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'get-started-btn'))
        )
        button.click()

        # Step 3: Confirm we navigated to login page (email input should exist)
        email_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'email'))
        )
        self.assertTrue(email_input.is_displayed())
