import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SendFriendRequestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = 'https://spotify-mood-analyzer-production.up.railway.app'

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        cls.driver = webdriver.Chrome(options=options)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def login_as_test(self):
        self.driver.get(f'{self.base_url}/')
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'get-started-btn'))
        ).click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'email'))
        )
        self.driver.find_element(By.NAME, 'email').send_keys('test@example.com')
        self.driver.find_element(By.NAME, 'password').send_keys('test123')
        self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()

    def test_send_friend_request(self):
        try:
            self.login_as_test()

            # Step 1: Go to "Find Friends"
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.tab[data-tab="search-friends"]'))
            ).click()

            # Step 2: Enter "test2" and submit search
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'search-input'))
            )
            search_input.clear()
            search_input.send_keys("test2")
            self.driver.find_element(By.CSS_SELECTOR, '#search-form button').click()

            # Step 3: Wait for result and click "Send Friend Request"
            result_card = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'result-card'))
            )
            send_button = result_card.find_element(By.CSS_SELECTOR, 'form[action="/friends/add"] button')
            send_button.click()

            # Step 4: Wait for redirection to /friends
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("/friends")
            )

            # Step 5: Optional: check if flash message or friend list updated
            self.assertIn("Friend", self.driver.page_source)  # weak check

        except Exception as e:
            with open("send_request_debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise e
