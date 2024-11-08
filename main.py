from solutions.scraper import Scraper


def main():
    scraper = Scraper("uc", start=True)
    scraper()
    scraper.quit()


if __name__ == '__main__':
    main()
