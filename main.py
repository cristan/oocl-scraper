from solutions import Scraper
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", "w", "utf-8")
    ]
)

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
