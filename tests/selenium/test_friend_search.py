import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FriendSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use deployed app URL
        cls.base_url = 'https://spotify-mood-analyzer-production.up.railway.app'

        # Set up headless Chrome browser
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        cls.driver = webdriver.Chrome(options=options)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def login_as_test2(self):
        self.driver.get(f'{self.base_url}/')

        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'get-started-btn'))
        ).click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'email'))
        )
        self.driver.find_element(By.NAME, 'email').send_keys('test2@example.com')
        self.driver.find_element(By.NAME, 'password').send_keys('test1234')
        self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()

    def test_search_for_test_user(self):
        try:
            self.login_as_test2()

            # Step 1: Go to "Find Friends" tab
            find_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.tab[data-tab="search-friends"]'))
            )
            find_tab.click()

            # Step 2: Enter "test" and submit search
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'search-input'))
            )
            search_input.clear()
            search_input.send_keys('test')

            self.driver.find_element(By.CSS_SELECTOR, '#search-form button').click()

            # Step 3: Wait for search results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'result-card'))
            )

            # Step 4: Check if 'test@example.com' is in results
            self.assertIn("test@example.com", self.driver.page_source)

        except Exception as e:
            with open("friend_search_debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise e
