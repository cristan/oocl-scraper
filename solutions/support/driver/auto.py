import logging
import os.path
import random
import time
from pathlib import Path

import pyautogui

from .delays import Delay

logger = logging.getLogger(__name__)


class Auto:
    IMAGE_DIR = str(Path(__file__).resolve().parent.parent / "images")

    def __init__(self):
        self.auto = pyautogui
        self.delay = Delay()

    def write(self, content):
        for c in content:
            self.auto.write(c)
            time.sleep(random.uniform(0.01, 0.1))

    def click_image(self, image_name, timeout=30, confidence=0.8, region=None, random_delay=True):
        pos = self.wait_until_image_found(image_name, timeout, confidence, region)
        if pos is None:
            raise TimeoutError(f"Image not found on screen in {timeout} seconds!")

        self.auto.click(*pos)
        if random_delay:
            self.delay.one10_one()

    def wait_until_image_found(self, image_name, timeout=30, confidence=0.8, region=None):
        """ Wait unless image found, return None or position """
        image_path = os.path.join(self.IMAGE_DIR, image_name)

        for i in range(timeout):
            position = self.auto.locateCenterOnScreen(image_path, confidence=confidence, region=region)
            if position is not None:
                logger.info(f"Found {image_name}")
                return position
            logger.debug(f"{image_name} not found  | Polls: {i}")
            time.sleep(1)
        return None

    def wait_until_image_hide(self, image_name, timeout=30, confidence=0.8, region=None):
        image_path = os.path.join(self.IMAGE_DIR, image_name)

        for i in range(timeout):
            position = self.auto.locateCenterOnScreen(image_path, confidence=confidence, region=region)
            if position is None:
                logger.info(f"Hide {image_name}")
                return position
            logger.debug(f"{image_name} still visible  | Polls: {i}")
            time.sleep(1)
        return None

    def scroll_to_image(self, img_name, scroll_st=50):
        persistence = 0
        for i in range(10):
            if self.wait_until_image_found(image_name=img_name, timeout=1) is None:
                self.auto.vscroll(-scroll_st)
                logger.info("Scrolling downward")
                persistence = 0
                self.auto.click(10, 500)
            else:
                persistence += 1
                if persistence == 2:
                    logger.info("Scrolled to interested image")
                    return True
            time.sleep(1)

        raise Exception("Cannot scroll to image!")

    def multiWait(self, images, confidence=0.8, region=None, timeout=30):
        """
        Wait until any image found on screen
        :param images: list of images paths
        :param confidence: percentage of image to match, default 0.8
        :param region: region where image might located, default None means anywhere
        :param timeout: maximum no of time allowed, default 30
        :raise: TimeoutError
        :return: i, position of image at center
        """
        polls = int(timeout / len(images))
        for _ in range(polls + 1):
            for i, img in enumerate(images):
                pos = self.wait_until_image_found(image_name=img, confidence=confidence, region=region, timeout=1)
                if pos is not None:
                    return i, pos

        raise TimeoutError("No image found on given region")

    def click_any(self, images, confidence=0.8, region=None, timeout=30, random_delay=True):
        pos = self.multiWait(images, confidence, region, timeout)
        self.auto.click(*pos)

        if random_delay:
            self.delay.one10_one()
