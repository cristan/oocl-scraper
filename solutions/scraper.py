import csv
import random
import time
from io import BytesIO
from pathlib import Path

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
        y = random.choice([1, -1]) * random.randint(10, 25)
        self.move_human(x=x, y=y)

    def handle_captcha(self):
        slider = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="verify-move-block"]')))
        self.move_human(slider)
        self.actions.click_and_hold(slider).perform()
        self.slide(100)
        for i in range(32):
            self.slide(10)
            if self.detect():
                self.actions.release(slider).perform()
                break
        return self.multiWait([
            (By.XPATH, '//*[text()="Validation failed"]'),
            (By.XPATH, '//*[text()="Cargo Tracking"]')
        ])

    def _scrape(self):
        self

    def scrape_container(self):
        self.initiate_search()
        self.driver.switch_to.window(self.driver.window_handles[-1])

        if self.multiWait(
                [
                    (By.ID, 'imgCanvas'),
                    (By.XPATH, '//*[text()="Cargo Tracking"]'),
                ]
        ) == 0:
            if not self.handle_captcha():
                raise Exception("Captcha not solved.")
        self._scrape()
        return True

    def move_to_lower_right_corner(self):
        """Move to lower right corner to avoid mouse binding with captcha."""
        screen_width, screen_height = self.auto.auto.size()
        self.auto.auto.moveTo(screen_width - 1, screen_height - 1)

    @staticmethod
    def read_csv(filename):
        with open(filename, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            return [row[0] for row in reader if row]

    def write_csv(self, data):
        with open(self.OUTPUT_CSV_FILENAME, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=list(data.keys())) # noqa
            writer.writeheader() if self.OUTPUT_CSV_FILENAME.stat().st_size == 0 else None
            writer.writerow(data)

    def get_new(self):
        if self.OUTPUT_CSV_FILENAME.exists():
            output_csv = self.read_csv(self.OUTPUT_CSV_FILENAME)
        input_csv = self.read_csv(self.INPUT_CSV_FILENAME)


    def __call__(self, *args, **kwargs):
        self.INPUT_CSV_FILENAME = Path(args[0]).resolve()
        self.OUTPUT_CSV_FILENAME = Path(args[1]).resolve()

        self.auto = Auto()
        self.move_to_lower_right_corner()
        self.model = ONNXModel()
        self.scrape_container()
