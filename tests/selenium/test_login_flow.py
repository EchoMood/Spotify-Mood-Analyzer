import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LoginFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set your deployed app base URL
        cls.base_url = 'https://spotify-mood-analyzer-production.up.railway.app'

        # Set up headless Chrome browser
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        cls.driver = webdriver.Chrome(options=options)

    @classmethod
    def tearDownClass(cls):
        # Close the browser after test
        cls.driver.quit()

    def test_login_with_valid_credentials(self):
        try:
            # Step 1: Open homepage
            self.driver.get(f'{self.base_url}/')

            # Step 2: Click the "Get Started" button
            start_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'get-started-btn'))
            )
            start_button.click()

            # Step 3: Wait for login form and fill credentials
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'email'))
            )
            self.driver.find_element(By.NAME, 'email').send_keys('test@example.com')
            self.driver.find_element(By.NAME, 'password').send_keys('test123')
            self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()

            # Step 4: Wait for dashboard to appear
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'h1'))
            )
            self.assertIn("Dashboard", self.driver.page_source)

        except Exception as e:
            with open("login_debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise e
