import time

from solutions.support.driver import *


class DataCollector(Selenium):
    URL = "https://www.oocl.com/eng/ourservices/eservices/cargotracking/Pages/cargotracking.aspx"
    CONTAINER_NUMBER = "TXGU8170341"

    def initiate_search(self):
        self.get(self.URL)

        for _ in range(15):
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

    def save_image(self, i):
        screenshot = self.find_element(By.ID, 'imgCanvas').screenshot_as_png
        with open(f'dataset/{self.i}/{i + 1}.png', 'wb') as file:
            file.write(screenshot)

    def handle_captcha(self):
        slider = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="verify-move-block"]')))
        self.actions.click_and_hold(slider).perform()
        for i in range(60):
            self.actions.move_by_offset(5, 0).perform()
            self.save_image(i)
            time.sleep(0.2)
        return True
        # self.actions.release(slider).perform()

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
        self.i = args[0]
        self.scrape_container()
        return True


if __name__ == '__main__':
    import os

    from nordvpn_connect import initialize_vpn, rotate_VPN

    num_puzzles = 40


    def main():
        for i in range(10, num_puzzles + 1):
            settings = initialize_vpn('US')
            rotate_VPN(settings)

            os.makedirs(f"dataset/{i}", exist_ok=True)
            print(i)
            collector = DataCollector("uc", start=True)
            collector(i)
            collector.quit()


    main()
