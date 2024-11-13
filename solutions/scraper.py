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


class Scraper(Selenium):
    URL = "https://www.oocl.com/eng/ourservices/eservices/cargotracking/Pages/cargotracking.aspx"

    def initiate_search(self, container_number):
        self.get(self.URL)

        timeout = 60
        i = 0
        for i in range(timeout):
            try:
                if self.find_element(By.ID, 'allowAll'):
                    self.click_js((By.ID, 'allowAll'))

                Select(self.find_element(By.ID, 'ooclCargoSelector')).select_by_value('cont')
                self.find_element(By.ID, 'SEARCH_NUMBER').send_keys(container_number)
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
        self.slide(50)
        for i in range(24):
            self.slide(10)
            if self.detect():
                break
        self.actions.release(slider).perform()
        return self.multiWait([
            (By.XPATH, '//*[text()="Validation failed"]'),
            (By.XPATH, '//*[text()="Cargo Tracking"]')
        ])

    @staticmethod
    def scrape_containers_table(soup):
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
                    (By.ID, 'imgCanvas'),
                    (By.XPATH, '//*[text()="Cargo Tracking"]'),
                ]
        ) == 0:
            if not self.handle_captcha():
                raise Exception("Captcha not solved.")

        data = self._scrape(container_number)
        self.spider.write_output(data)

    def scrape_containers(self):
        data = self.spider.read_data()
        for i, item in enumerate(data):
            self.spider.update_status(i, 'SCRAPING', data)
            try:
                self.scrape_container(item)
            except (Exception,) as e:
                self.spider.update_status(i, 'INITIAL', data)
                if e.msg == 'Captcha not solved.':
                    raise e
            else:
                self.spider.delete_object(i, data)

    def move_to_lower_right_corner(self):
        """Move to lower right corner to avoid mouse binding with captcha."""
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
