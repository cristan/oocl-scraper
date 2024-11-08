import time
from io import BytesIO

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

    def handle_captcha(self):
        slider = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="verify-move-block"]')))
        self.actions.click_and_hold(slider).perform()
        for i in range(120):
            self.actions.move_by_offset(5, 0).perform()
            if self.detect():
                self.actions.release(slider).perform()
                break
            time.sleep(0.1)
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
