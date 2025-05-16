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

    def test_send_friend_request_to_test2(self):
        try:
            self.login_as_test()

            # Step 1: Go to "Find Friends" tab
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.tab[data-tab="search-friends"]'))
            ).click()

            # Step 2: Search for "test2"
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'search-input'))
            )
            search_input.clear()
            search_input.send_keys("test2")
            self.driver.find_element(By.CSS_SELECTOR, '#search-form button').click()

            # Step 3: Wait for result card to load
            result_card = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'result-card'))
            )

            result_text = result_card.text.lower()

            # Step 4: Check if request already sent or already friends
            if "already friends" in result_text:
                print("Already friends. No action needed.")
                return
            if "friend request pending" in result_text:
                print("Friend request already sent.")
                return

            # Step 5: Send the request
            send_button = result_card.find_element(By.CSS_SELECTOR, 'form[action="/friends/add"] button')
            send_button.click()

            # Step 6: Wait for redirect or confirmation
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("/friends")
            )

        except Exception as e:
            with open("send_request_debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise e
