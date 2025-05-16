import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SpotifyConnectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Deployed app base URL
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

    def login_as_test2(self):
        # Log into the app as test2@example.com
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

    def test_spotify_connect_button_redirect(self):
        try:
            self.login_as_test2()

            # Step 1: Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'h1'))
            )

            # Step 2: Find the "Connect Spotify" button
            connect_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, 'Connect Spotify'))
            )

            # Step 3: Click the button
            connect_button.click()

            # Step 4: Wait for redirection to Spotify
            WebDriverWait(self.driver, 10).until(
                lambda driver: "accounts.spotify.com" in driver.current_url
            )

            # Step 5: Assert URL is a Spotify login/authorization page
            self.assertIn("accounts.spotify.com", self.driver.current_url)

        except Exception as e:
            with open("spotify_connect_debug.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise e
