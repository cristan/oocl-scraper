# OOCL Scraper

OOCL Scraper is a tool designed to scrape container data from the OOCL website. The input to the scraper is a container ID, which
is specified in the `./ToScrape/oocl.json` file. The outputs of the scraper are saved in `./Outputs/oocl.json`.

## Installation

First, ensure you have Python 3.9.7 installed. Then, install the necessary packages listed in `requirements.txt` using the
following command:

```sh
pip install -r requirements.txt
```

## Input and Output

- **Input**: The input to the scraper is provided in the `./ToScrape/oocl.json` file. This file contains the container IDs to be
  scraped.
- **Output**: The output of the scraper is saved in the `./Outputs/oocl.json` file.

## Logs

Logs are saved to `logs/oocl_scraper_<datetime>.log` files, where `<datetime>` is the timestamp of the scraper's run.

## Captcha Solving

The scraper utilizes a deep learning solution to handle captchas gracefully. Two deep learning models are used:

1. **Mouse Movement Model**: Mimics human mouse movements to achieve a better score.
2. **Captcha Prediction Model**: Predicts the captcha image.
   In addition to these models, image processing techniques are applied to further enhance the confidence in captcha predictions.

## Running the Scraper

To run the scraper, simply execute the `main.py` file:

```sh
python main.py
```