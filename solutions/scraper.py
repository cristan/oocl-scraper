import time
from io import BytesIO

import numpy as np
from PIL import Image

from solutions.support.driver import *
from solutions.support.model import ONNXModel


class Scraper(Selenium):
    URL = "https://www.oocl.com/eng/ourservices/eservices/cargotracking/Pages/cargotracking.aspx"
    CONTAINER_NUMBER = "TXGU8170341"

    def initiate_search(self):
        self.get(self.URL)

        timeout = 60
        i = 0
        for i in range(timeout):
            try:
                if self.find_element(By.ID, 'allowAll'):
                    self.click_js((By.ID, 'allowAll'))

                Select(self.find_element(By.ID, 'ooclCargoSelector')).select_by_value('cont')
                self.find_element(By.ID, 'SEARCH_NUMBER').send_keys(self.CONTAINER_NUMBER)
                self.click_js((By.ID, 'container_btn'))
            except (Exception,):
                time.sleep(1)
            else:
                break
        if i == timeout - 1:
            raise Exception(f"Page failed to load in {i + 1} seconds.")

    def detect(self):
        screenshot = self.find_element(By.ID, 'imgCanvas').screenshot_as_png
        image = Image.open(BytesIO(screenshot))
        input_data = self.model.preprocess_image(image)
        return self.model.infer(input_data)

    def slide(self, x):
        offset = 1 if x >= 0 else -1
        for i in range(abs(x)):
            self.actions.move_by_offset(offset, 0).perform()

    @staticmethod
    def generate_balanced_sequence(size=10, min_value=1, max_value=300, net_result=40):
        numbers = []
        cumulative_sum = 0

        for _ in range(size - 1):
            number = np.random.randint(min_value, max_value + 1)
            if cumulative_sum + number > max_value:
                number = -np.random.randint(min_value, min(cumulative_sum, max_value) + 1)
            cumulative_sum += number
            cumulative_sum = np.clip(cumulative_sum, min_value, max_value)
            numbers.append(number)
        last_number = net_result - cumulative_sum
        last_number = np.clip(last_number, -max_value, max_value)
        numbers.append(last_number)
        return numbers

    def play_with_slider(self):
        numbers = self.generate_balanced_sequence(size=np.random.randint(4, 7))
        print(numbers)
        for d in numbers:
            self.slide(d)

    def handle_captcha(self):
        slider = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="verify-move-block"]')))
        self.actions.click_and_hold(slider).perform()
        self.slide(40)
        for i in range(120):
            self.slide(8)
            if self.detect():
                self.actions.release(slider).perform()
                break
        input(">>>")
        return True

    def scrape_container(self):
        self.initiate_search()
        self.driver.switch_to.window(self.driver.window_handles[-1])

        if self.multiWait(
                [
                    (By.ID, 'imgCanvas'),

                ]
        ) == 0:
            self.handle_captcha()
        return True

    def __call__(self, *args, **kwargs):
        self.model = ONNXModel()
        self.scrape_container()
