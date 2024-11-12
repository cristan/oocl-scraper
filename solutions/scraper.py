import sys
import time
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
from solutions.support.driver import *
from solutions.support.driver.wind_mouse import wind_mouse
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

    @staticmethod
    def relative_positions(start_pos, points):
        start_pos = np.array(start_pos)
        points = np.array(points)
        relative_points = np.zeros_like(points)
        relative_points[0] = points[0] - start_pos
        for i in range(1, len(points)):
            relative_points[i] = points[i] - points[i - 1]
        return relative_points

    def slide(self, x):
        start_pos = self.auto.auto.position()
        if np.random.choice([True, False]):
            new_pos = start_pos[0] + x, start_pos[1] + np.random.randint(5, 20)
        else:
            new_pos = start_pos[0] + x, start_pos[1] - np.random.randint(5, 20)
        points = wind_mouse(*start_pos, *new_pos)
        points[-1] = [new_pos[0], start_pos[1]]
        rel_points = self.relative_positions(start_pos, points)
        for point in rel_points:
            self.auto.auto.moveRel(*point)

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

    def find_slider_image(self):
        slider_path = str(Path(__file__).resolve().parent / 'images' / 'slider.png')
        try:
            slider_location = self.auto.auto.locateCenterOnScreen(slider_path, confidence=0.7)
        except self.auto.auto.ImageNotFoundException:
            print("Slider image expires. Please capture a new image.")
            input(">>>")
            sys.exit()
        else:
            return slider_location

    def handle_captcha(self):
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="verify-move-block"]')))
        pos = self.find_slider_image()
        self.auto.auto.moveTo(*pos)
        self.auto.auto.mouseDown()
        self.slide(100)
        for i in range(32):
            self.slide(20)
            if self.detect():
                self.auto.auto.mouseUp()
                break
        return self.multiWait(
            [(By.XPATH, "//*")]
        )

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
        self.auto = Auto()
        self.model = ONNXModel()
        self.scrape_container()
