import logging
import random
import re
import time
from io import BytesIO
from pathlib import Path

from PIL import Image
from bs4 import BeautifulSoup

from solutions.spider import Spider
from solutions.support.driver import *
from solutions.support.model import ONNXModel

logger = logging.getLogger(__name__)


class Scraper(Selenium):
    URL = "https://www.oocl.com/eng/ourservices/eservices/cargotracking/Pages/cargotracking.aspx"

    def initiate_search(self, container_number):
        logger.info(f"Initiating search for container: {container_number}")
        self.get(self.URL)

        timeout = 60
        i = 0
        for i in range(timeout):
            try:
                if self.find_element(By.ID, 'allowAll'):
                    logger.info("Clicking on 'Allow All' button.")
                    self.click_js((By.ID, 'allowAll'))
                logger.info("Selecting cargo type 'Container ID'.")
                Select(self.find_element(By.ID, 'ooclCargoSelector')).select_by_value('cont')
                self.find_element(By.ID, 'SEARCH_NUMBER').send_keys(container_number)
                self.click_js((By.ID, 'container_btn'))
            except Exception as e:
                logger.warning(f"Exception occurred: {e}. Retrying... ({i + 1}/{timeout})")
                time.sleep(1)
            else:
                logger.info("Search initiated successfully.")
                break
        else:
            raise Exception(f"Page failed to load in {timeout} seconds.")

    def detect(self):
        logger.info("Detecting captcha result.")
        screenshot = self.find_element(By.ID, 'imgCanvas').screenshot_as_png
        image = Image.open(BytesIO(screenshot))
        input_data = self.model.preprocess_image(image)
        result = self.model.infer(input_data)
        logger.info(f"Captcha detection result: {result}")
        return result

    def slide(self, x):
        y = random.choice([1, -1]) * random.randint(10, 25)
        logger.debug(f"Sliding captcha slider by (x={x}, y={y}).")
        self.move_human(x=x, y=y)

    def handle_captcha(self):
        logger.info("Handling captcha.")
        slider = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="verify-move-block"]')))
        self.move_human(slider)
        self.actions.click_and_hold(slider).perform()
        self.slide(50)
        for i in range(35):
            self.slide(7)
            if self.detect():
                logger.info("Captcha solved.")
                break
        self.actions.release(slider).perform()

        result_index = self.multiWait([
            (By.XPATH, '//*[text()="Validation failed"]'),
            (By.XPATH, '//*[text()="Cargo Tracking"]')
        ])
        if result_index == 0:
            logger.error("Captcha validation failed.")
        else:
            logger.info("Captcha validation successful.")
        return result_index

    @staticmethod
    def scrape_containers_table(soup):
        logger.info("Scraping containers table.")
        table = soup.find('table', {'id': 'summaryTable'})
        tbody_rows = table.find('tbody').find_all('tr')
        table_data = [re.sub(r'(\n|\t)+', '\\n', element.text.strip()) for element in tbody_rows[2].find_all('td')]
        return {
            'container_number': table_data[0],
            'container_size_type': table_data[1],
            'quantity': table_data[2],
            'gross_weight': table_data[3],
            'verified_gross_mass': table_data[4],
            'latest_event': {
                'event': table_data[5],
                'location': table_data[6],
                'time': table_data[7],
            },
            'final_destination': table_data[8],
        }

    @staticmethod
    def scrape_detention_table(soup):
        logger.info("Scraping detention table.")
        table = soup.find('table', {'id': 'dndTable'})
        tbody_rows = table.find('tbody').find_all('tr')
        table_data = [re.sub(r'(\n|\t)+', '\\n', element.text.strip()) for element in tbody_rows[-1].find_all('td')]
        return {
            'container_number': table_data[0],
            'at_origin': {
                'earliest_empty_pickup_date': table_data[1],
                'detention_last_free_date': table_data[2],
            },
            'at_destination': {
                'combined_dem/det_(2in1)_last_free_date': {
                    'free_time': table_data[3],
                    'last_free_date': table_data[4],
                },
                'inbound_demurrage': {
                    'free_time': table_data[5],
                    'last_free_date': table_data[6],
                },
                'inbound_detention': {
                    'free_time': table_data[7],
                    'last_free_date': table_data[8],
                },
                'quay_rent': {
                    'free_time': table_data[9],
                    'last_free_date': table_data[10],
                }
            }
        }

    @staticmethod
    def scrape_routing_table(soup):
        logger.info("Scraping routing table.")
        table = soup.find('table', {'id': 'eventListTable'})
        tbody_rows = table.find('tbody').find_all('tr')
        table_data = [re.sub(r'(\n|\t)+', '\\n', element.text.strip()) for element in tbody_rows[-1].find_all('td')]
        return {
            "origin": table_data[0],
            "empty_pickup_location": table_data[1],
            "full_return_location": table_data[2],
            "port_of_load": table_data[3],
            "vessel_voyage": table_data[4],
            "port_of_discharge": table_data[5],
            "final_destination_hub": table_data[6],
            "destination": table_data[7],
            "empty_return_location": table_data[8],
            "haulage": table_data[9]
        }

    @staticmethod
    def scrape_equipment_activities_table(soup):
        logger.info("Scraping equipment activities table.")
        data = []
        table = soup.find('div', {'id': 'Tab2'}).find('table', {'id': 'eventListTable'})
        tbody_rows = table.find('tbody').find_all('tr')
        for tr in tbody_rows[1:]:
            table_data = [re.sub(r'(\n|\t)+', '\\n', element.text.strip()) for element in tr.find_all('td')]
            data.append(
                {
                    'event': table_data[0],
                    'facility': table_data[1],
                    'location': table_data[2],
                    'mode': table_data[3],
                    'time': table_data[4],
                    'remarks': table_data[5]
                }
            )
        return data

    def _scrape(self, container_number):
        logger.info(f"Scraping data for container number {container_number}.")
        content = self.driver.page_source
        soup = BeautifulSoup(content, features="html.parser")
        return {
            'containers': self.scrape_containers_table(soup),
            'routing': self.scrape_routing_table(soup),
            'detention_and_demurrage': self.scrape_detention_table(soup),
            'equipment_activities': self.scrape_equipment_activities_table(soup)
        }

    def scrape_container(self, item):
        container_number = item['container_number']
        self.initiate_search(container_number)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        if self.multiWait(
                [
                    {'ec': EC.visibility_of_element_located((By.XPATH, '//*[@class="verify-move-block"]'))},
                    (By.XPATH, '//*[text()="Cargo Tracking"]'),
                ]
        ) == 0:
            if not self.handle_captcha():
                logger.error("Captcha not solved.")
                raise Exception("Captcha not solved.")
        data = self._scrape(container_number)
        self.spider.write_output(data)

    def scrape_containers(self):
        logger.info("Starting to scrape containers.")
        data = self.spider.read_data()
        while data:
            item = data[0]
            self.spider.update_status(0, 'SCRAPING', data)
            try:
                self.scrape_container(item)
            except Exception as e:
                logger.error(f"Exception occurred while scraping container: {e}")
                self.spider.update_status(0, 'INITIAL', data)
                if str(e) == 'Captcha not solved.':
                    raise e
            else:
                self.spider.delete_object(0, data)

    def move_to_lower_right_corner(self):
        """Move to lower right corner to avoid mouse binding with captcha."""
        logger.info("Moving mouse to lower right corner.")
        screen_width, screen_height = self.auto.auto.size()
        self.auto.auto.moveTo(screen_width - 1, screen_height - 1)

    def __call__(self, *args, **kwargs):
        input_filename = Path(args[0]).resolve()
        output_filename = Path(args[1]).resolve()
        output_filename.parent.mkdir(parents=True, exist_ok=True)

        self.spider = Spider(input_filename, output_filename)
        self.auto = Auto()
        self.move_to_lower_right_corner()
        self.model = ONNXModel()
        self.scrape_containers()
