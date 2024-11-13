from solutions import Scraper
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logfile = f"logs/oocl_scraping_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.log"
os.makedirs(os.path.dirname(logfile), exist_ok=True)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_format)

file_handler = logging.FileHandler(logfile, mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter('[%(asctime)s] %(levelname)s:%(name)s:%(funcName)s:%(lineno)d %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_format)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

logging.getLogger('uc').setLevel(logging.WARNING)
logging.getLogger('undetected_chromedriver').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('solutions.support.driver.driver').setLevel(logging.WARNING)

MAXIMUM_RETRIES = 3
INPUT_FILENAME = "./ToScrape/oocl.json"
OUTPUT_FILENAME = "./Outputs/oocl.json"


def main():
    attempt = 0
    while attempt < MAXIMUM_RETRIES:
        try:
            logger.info("Starting attempt %d", attempt + 1)
            scraper = Scraper("uc", start=True)
            try:
                scraper(INPUT_FILENAME, OUTPUT_FILENAME)
            except Exception as e:
                logger.error("Error occurred during scraper execution on attempt %d: %s", attempt + 1, e)
            else:
                logger.info("Scraper ran successfully on attempt %d", attempt + 1)
                break
            finally:
                scraper.quit()
        except Exception as e:
            logger.error("Error occurred during scraper initialization on attempt %d: %s", attempt + 1, e)

        attempt += 1
        if attempt == MAXIMUM_RETRIES:
            logger.error("Maximum attempts reached. Exiting.")


if __name__ == '__main__':
    main()
