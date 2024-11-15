import logging
import random
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Union, Callable, Tuple, Dict, Optional, Any

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    ElementNotInteractableException,
    ElementNotVisibleException,
    ElementNotSelectableException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    NoSuchElementException,
    NoSuchAttributeException,
    JavascriptException,
    InvalidArgumentException,
    InvalidSelectorException,
    InvalidSessionIdException,
    NoSuchCookieException,
    NoSuchWindowException,
    NoSuchFrameException,
    NoAlertPresentException,
    UnexpectedAlertPresentException,
    MoveTargetOutOfBoundsException,
    WebDriverException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

try:
    from .proxy import Proxy
except ImportError:
    pass

logging.getLogger('selenium').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

__all__ = ["ActionChains", "By", "Options", "EC", "WebDriverWait", "webdriver", "Selenium", "multiWait", "Select",
           "length_of_window_handles_become", "length_of_window_handles_less_than",
           "length_of_window_handles_greater_than", "multiWaitNsec", "Keys", "TableScraper",
           # **Exceptions**
           "ElementNotInteractableException", "TimeoutException",
           "ElementNotVisibleException", "ElementNotSelectableException",
           "ElementClickInterceptedException", "StaleElementReferenceException", "NoSuchElementException",
           "NoSuchAttributeException", "JavascriptException", "InvalidArgumentException", "InvalidSelectorException",
           "InvalidSessionIdException", "NoSuchCookieException", "NoSuchWindowException", "NoSuchFrameException",
           "NoAlertPresentException", "UnexpectedAlertPresentException", "MoveTargetOutOfBoundsException",
           "WebDriverException"
           # **Exceptions**
           ]


class Selenium:
    """ Master class for all selenium work """

    common_exceptions = (
        TimeoutException,
        ElementNotInteractableException,
        ElementNotVisibleException,
        ElementNotSelectableException,
        ElementClickInterceptedException,
        StaleElementReferenceException,
        NoSuchElementException,
        NoSuchAttributeException,
        JavascriptException,
        InvalidArgumentException,
        InvalidSelectorException,
        InvalidSessionIdException,
        NoSuchCookieException,
        NoSuchWindowException,
        NoSuchFrameException,
        NoAlertPresentException,
        UnexpectedAlertPresentException,
        MoveTargetOutOfBoundsException,
        WebDriverException
    )
    current_position = (0, 0)

    def __init__(
            self,
            webdriver_name: str = "chrome",
            user_data_dir: Union[str, Path] = None,
            incognito: bool = False,
            proxy=None,
            headless: bool = False,
            headless2: bool = False,
            remove_images: bool = False,
            load_full: bool = False,
            timeout: int = 30,
            zoom: Union[float, int] = None,
            args: Tuple[str] = (),
            extensions: List[str] or Tuple[str] = (),
            options: Optional[Any] = None,
            user_agent: str = None,
            start: bool = False,
    ):
        """
        Initialising selenium wrapper
        :param webdriver_name: The webdriver to use for the class. Default is "chrome" (chrome|uc|seleniumbase)
        :param user_data_dir: The path to the user data directory. Default is None
        :param incognito: A boolean indicating whether to start the browser in incognito mode. Default is False
        :param proxy: Proxy object
        :param headless: A boolean indicating whether to run the browser in headless mode. Default is False (Old method)
        :param headless2: A boolean indicating whether to run the browser in headless mode. Default is False
        :param load_full: A boolean indicating whether to load the full page or just the visible content. Default is False
        :param timeout: An integer representing the timeout for the browser in seconds. Default is 30
        :param zoom: A float or integer representing the zoom level for the browser. Default is None
        :param args: A tuple of strings representing command line arguments to pass to the browser
        :param extensions: A tuple of strings representing the path to the browser extensions to be loaded
        :param options: An instance of a class that contains additional options for the browser. Default is None
        :param start: A boolean indicating whether to start the browser immediately after initialization. Default is False
        """
        self._webdriver = webdriver_name
        self._user_agent = user_agent
        self._headless = headless
        self._headless2 = headless2
        self._incognito = incognito
        self._user_data_dir = user_data_dir
        self._load_full = load_full
        self._remove_images = remove_images
        self._extensions = extensions
        self._args = args
        self._zoom = zoom
        self._proxy = proxy
        self._current_dir = Path(__file__).resolve().parent
        self._driver_executable_dir = self._current_dir / '.wdm'
        self._driver_name = 'chromedriver.exe' if sys.platform == 'win32' else 'chromedriver'
        self._driver_executable_path = self._driver_executable_dir / self._driver_name
        self._driver_dist_path = self._driver_executable_dir / 'dist-info.txt'
        self._options = self._init_options() if options is None else options

        self.driver: webdriver.Chrome = None  # noqa
        self.actions: ActionChains = None  # noqa
        self.wait: WebDriverWait = None  # noqa
        self.timeout = timeout

        self.start() if start else None
        self._load_wind_mouse()

    def _load_wind_mouse(self):
        wind_mouse_path = self._current_dir / 'wind_mouse.py'
        if wind_mouse_path.exists():
            from .wind_mouse import wind_mouse
            self.wind_mouse = wind_mouse

    def _install_chromedriver(self):
        from webdriver_manager.chrome import ChromeDriverManager

        self._driver_executable_dir.mkdir(parents=True, exist_ok=True)
        wdm_driver_path = Path(ChromeDriverManager().install()).resolve().parent / self._driver_name
        shutil.copy2(wdm_driver_path, self._driver_executable_path)
        with open(self._driver_dist_path, 'w') as f:
            f.write(datetime.now().strftime('%y/%m/%d'))

    def _install_webdriver(self):
        if not self._driver_executable_path.exists():
            logger.info("Driver not found. Downloading a new one ...")
            self._install_chromedriver()
            logger.info("Chromedriver downloaded.")
        else:
            with open(self._driver_dist_path, 'r') as f:
                date = datetime.strptime(f.read(), '%y/%m/%d')
            if datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7) > date:
                logger.info("Webdriver is older than 7 days.\nUpdating ...")
                try:
                    shutil.rmtree(self._driver_executable_dir)
                except (OSError, PermissionError):
                    logger.error("Failed to delete webdriver directory. Terminating ...")
                    sys.exit(1)

                self._install_chromedriver()

    def _init_options(self):
        """ Initialize Options class using given params """
        logger.debug("Compiling options ...")
        options = Options()
        options.add_argument(self._proxy.chrome_proxy) if self._proxy else None
        options.add_argument(f"--user-agent={self._user_agent}") if self._user_agent else None
        options.add_argument("--headless=new") if self._headless2 else None
        options.add_argument("--blink-settings=imagesEnabled=false") if self._remove_images else None
        options.add_argument("--headless") if self._headless and not self._headless2 else None
        options.add_argument(f"--user-data-dir={self._user_data_dir}") if self._user_data_dir else None
        options.add_argument("--incognito") if self._incognito else ''
        options.add_argument(f"--force-device-scale-factor={self._zoom} --high-dpi-support={self._zoom}") \
            if self._zoom is not None else ''
        [options.add_argument(arg) for arg in self._args]
        [options.add_extension(ext) for ext in self._extensions]
        options.page_load_strategy = "none" if not self._load_full else 'normal'

        # Chrome specific options
        if self._webdriver == 'chrome':
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         'Chrome/68.0.3440.84 Safari/537.36'
            options.add_argument("--hide-scrollbars")
            options.add_argument(f"user-agent={user_agent}") if self._headless or self._headless2 else None
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-notifications")
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-application-cache')
            options.add_argument('--disable-gpu')
            options.add_argument("--start-maximized")
            options.add_argument("--disable-dev-shm-usage")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_experimental_option("prefs", {"profile.default_content_setting_values.popups": 1, })
        return options

    def start(self):
        """ Start webdriver (uc, webdriver, seleniumBase) """
        logger.debug(f"Starting webdriver {self._webdriver}")
        if self._webdriver.lower() == "chrome":
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service

            self._install_webdriver()
            self.driver = webdriver.Chrome(service=Service(str(self._driver_executable_path)), options=self._options)
            self.driver.execute_script("navigator.webdriver = false;")
        elif self._webdriver == "uc":
            import undetected_chromedriver as uc

            self._install_webdriver()
            self.driver = uc.Chrome(use_subprocess=True, options=self._options,
                                    driver_executable_path=str(self._driver_executable_path))
            self.driver.maximize_window()
        elif self._webdriver.lower() == 'seleniumbase':
            from seleniumbase import Driver  # noqa
            self.driver = Driver(headless2=self._headless2, headless=self._headless, uc=True,
                                 user_data_dir=self._user_data_dir,
                                 page_load_strategy=self._options.page_load_strategy
                                 )
            self.driver.maximize_window()
        else:
            raise NotImplementedError(f"{self._webdriver} is not implemented yet!")

        self.wait = WebDriverWait(self.driver, self.timeout)
        self.actions = ActionChains(self.driver, duration=0)
        logger.debug(f"Webdriver \"{self._webdriver}\" is ready to use!")

    def execute_js_element_inside_iframe(self, by, value, script):
        """
        Gets the element inside the first iframe with the given locator, including nested iframes.
        Sample Usage: By.ID, submit, arguments[0].click()
        Note: script must start with arguments[0] and then as needed.
        """
        element = self.find_element(by, value)
        if element is not None:
            return self.driver.execute_script(script, element)

        frames = self.driver.find_elements(By.XPATH, '//iframe')
        logger.debug(f"Frames found: {frames}")

        for frame in frames:
            try:
                self.driver.switch_to.frame(frame)
            except (Exception,):
                logger.debug("Fake frame.")
            else:
                element = self.find_element(by, value)
                if element is not None:
                    return self.driver.execute_script(script, element)

                # Recursive call to handle nested iframes
                result = self.execute_js_element_inside_iframe(by, value, script)
                if result:
                    return result
            finally:
                self.driver.switch_to.parent_frame()

        # If no element is found in any iframe, return None
        return None

    def clear_cache(self):
        self.driver.get('chrome://settings/clearBrowserData')
        script = """
        document.querySelector("body > settings-ui").shadowRoot.querySelector("#main").shadowRoot.querySelector(
        "settings-basic-page").shadowRoot.querySelector("#basicPage > settings-section:nth-child(
        10) > settings-privacy-page").shadowRoot.querySelector(
        "settings-clear-browsing-data-dialog").shadowRoot.querySelector("#clearBrowsingDataConfirm").click()
        """
        for _ in range(15):
            try:
                self.driver.execute_script(script)
            except JavascriptException:
                time.sleep(1)
            else:
                return True
        return False

    def text(self, by, value, timeout=10, js_text=True, multiple=False, joiner=', ', ignore_values=(),
             ignore_exceptions=(StaleElementReferenceException, NoSuchElementException),
             ):
        i = 0
        while True:
            try:
                if multiple:
                    e = self.driver.find_elements(by, value)
                    ts = []
                    for _e in e:
                        ts.append(_e.text)
                    t = joiner.join(ts)
                else:
                    e = self.driver.find_element(by, value)
                    if js_text:
                        t = self.driver.execute_script('return arguments[0].textContent;', e)
                    else:
                        t = e.text
                    if not t:
                        raise NoSuchElementException
            except ignore_exceptions:
                time.sleep(1)
            else:
                if ignore_values and t in ignore_values:
                    time.sleep(1)
                else:
                    return t.strip()

            i += 1
            if i == timeout:
                break

        raise NoSuchElementException

    def stale_click(self, by, value, js_click=False, timeout=30):
        i = 0
        while True:
            try:
                e = self.driver.find_element(by, value)
                if js_click:
                    self.click_js(e)
                else:
                    e.click()
            except (StaleElementReferenceException, JavascriptException, NoSuchElementException):
                time.sleep(1)
            else:
                return True

            i += 1
            if i == timeout:
                break

        raise NoSuchElementException

    def href(self, by, value, timeout=10):
        return self.get_attribute(by, value, 'href', timeout=timeout, ignore_values=None)

    def src(self, by, value, timeout=30, filter_empty=True):
        """ Get src attribute of image """
        igv = None
        if filter_empty:
            igv = (None, '')
        return self.get_attribute(by, value, 'src', timeout=timeout, ignore_values=igv)

    def id(self, by, value, timeout=10, ignore_values=(None,)):
        return self.get_attribute(by, value, 'id', timeout, ignore_values)

    def get_attribute(self, by, value, attr, timeout=10, ignore_values=(None,)):
        i = 0
        while True:
            try:
                a = self.driver.find_element(by, value).get_attribute(attr)
                if ignore_values is not None:
                    if a not in ignore_values:
                        return a
                else:
                    return a
            except (StaleElementReferenceException, NoSuchElementException):
                time.sleep(1)

            i += 1
            if i == timeout:
                break

        raise NoSuchElementException

    def move_human(self, element=None, x=0, y=0):
        """
        Human like mouse movement performed
        -> xoffset and element cannot be None
        :param element: input element, move to the center of element (Optional)
        :param x: move to specified x coordinate with respect to current scrolled position (Optional)
        :param y: move to specified y coordinate with respect to current scrolled position (Optional)
        """
        assert element or x or y, "XY And Element Cannot be None!"
        logger.debug(f"Simulating human mouse movement with x={x}, y={y}, and element={'element' if element else None}")
        if element:
            rect = self.driver.execute_script("return arguments[0].getBoundingClientRect()", element)
            x = int(rect['x'] + rect['width'] / 2)
            y = int(rect['y'] + rect['height'] / 2)
        x, y = self.current_position[0] + x, self.current_position[1] + y
        points = self.wind_mouse(*self.current_position, x, y, W_0=7, M_0=8, rel_points=True)
        for point in points:
            try:
                self.actions.move_by_offset(xoffset=point[0], yoffset=point[1]).perform()
            except MoveTargetOutOfBoundsException:
                pass
        self.current_position = (x, y)

    def click_human(self, element=None, x=None, y=None, action_click=True, delay=0.1):
        """
        Human like mouse movement performed and then clicked on element
        -> xoffset and element cannot be None
        :param element: input element (Optional)
        :param x: move x offset (Optional)
        :param y: move y offset (Optional)
        :param action_click: Use action chains to click on element
        :param delay: Sleep in seconds after clicking on element
        :return: None
        """
        self.move_human(element, x, y)
        if action_click:
            self.click_action()
        else:
            assert element is not None, "How can you click_js without knowing element?"
            self.click_js(element)
        time.sleep(delay)

    def stop_page_loading(self):
        self.driver.execute_cdp_cmd("Page.stopLoading", {})

    def slow_type(self, element, content, value='default', click_human=False):
        """ Type slowly like human with random speed """
        logger.debug(f"Sending {content} to webelement")
        if click_human:
            self.click_human(element)
        for x in content:
            if value == 'js':
                self.driver.execute_script(f'arguments[0].value += "{x}"', element)
            else:
                element.send_keys(x)
            time.sleep(random.uniform(0.1, 0.4))

    def set_value(self, e, value):
        """ Set value using javascript or simply send keys to input box """
        self.driver.execute_script(f'arguments[0].value = {value}', e)

    def find_element(self, by, value, ignore_exceptions: tuple = (Exception,)):
        """ Find element given by and value, also return None in case of ignore_exception """
        try:
            return self.driver.find_element(by, value)
        except ignore_exceptions:
            logger.debug(f"Failed to find element at {by, value}")
            return None

    def find_elements(self, by, value, ignore_exceptions: tuple = (Exception,)):
        """ Find elements given by and value, also return None in case of ignore_exception """
        try:
            return self.driver.find_elements(by, value)
        except ignore_exceptions:
            logger.debug(f"Failed to find elements at {by, value}")
            return None

    def click_action(self, elm=None):
        """ Click on given element or current location using ActionChains click """
        logger.debug("Performing click on element if possible else on current location")
        if elm is not None:
            ActionChains(self.driver).move_to_element(elm).click().perform()
        else:
            ActionChains(self.driver).click().perform()

    def click_js(self, arg, scroll_to_element_if_needed=False):
        """
        The method first checks if the arg parameter is a tuple, if it is then it uses that locator to find the element
        Then, it checks if scroll_to_element_if_needed is set to True, if it is then it calls scrollIntoViewIfNeeded method
        that scrolls the page to the element if needed
        Finally, it clicks on the element by calling the execute_script method of the WebDriver
        and passing in the element and the JavaScript click function
        """
        if isinstance(arg, tuple):
            logger.debug(f"Finding element with {arg}")
            arg = self.driver.find_element(*arg)
        if scroll_to_element_if_needed:
            self.scrollIntoViewIfNeeded(arg)

        logger.debug(f"Element clicked using javascript executor")
        self.driver.execute_script("arguments[0].click()", arg)

    def multiWaitNsec(self, locators, levels_of_persistency, refresh_url_every_n_sec=None):
        """ multiWait function should be persistent for given time """
        persistency = 0
        _prev_id = None
        ID = None
        while levels_of_persistency != persistency:
            ID = self.multiWait(locators, refresh_url_every_n_sec=refresh_url_every_n_sec)
            if ID != _prev_id and _prev_id is not None:
                logger.info(f"Break: {locators[ID]}")
                persistency = 0
            _prev_id = ID
            logger.info(f"Visible locator: {locators[ID]} && Persistency: {persistency + 1} second")
            time.sleep(1)
            persistency += 1
        return ID

    def multiWait(self, locators, output_type='id', refresh_url_every_n_sec=None):
        """ Same as multiWait with driver and timeout param filled """
        return multiWait(self.driver, locators, self.timeout, output_type, refresh_url_every_n_sec)

    def is_element_in_viewport(self, element):
        """ Is element visible on viewport """
        size = element.size
        location = element.location
        res = location['y'] >= 0 and location['y'] + size['height'] <= self.driver.execute_script("return window.innerHeight;")
        logger.debug("Element is not in viewport")
        return res

    def textContent(self, element):
        return self.driver.execute_script("return arguments[0].textContent;", element)

    def scrollIntoViewIfNeeded(self, element):
        """ Scroll to element if it is not visible on viewport """
        if not self.is_element_in_viewport(element):
            logger.debug("Element needed to be scrolled")
            self.scrollIntoView(element)
        logger.debug("Element does not need to be scrolled")

    def scrollIntoView(self, element, block='center'):
        """ Scroll to element, choose block: start, center, end, nearest """
        logger.debug("Scrolled into element")
        scroll_behaviour = "{behavior: 'smooth', block: '%s'}" % block
        self.driver.execute_script(f"arguments[0].scrollIntoView({scroll_behaviour});", element)

    def remove_element(self, element):
        """ Remove element from html document """
        logger.debug("Removed element from DOM!")
        self.driver.execute_script("arguments[0].remove();", element)

    def get(self, url):
        """ Go to the specified url """
        logger.info(f"Getting {url}")
        self.driver.get(url)

    def quit(self):
        """ Exit webdriver, also stop recording if needed """
        logger.info("Quitting driver")
        self.driver.quit()

    def refresh(self):
        """ Refresh webpage """
        logger.info("Refreshing web-page")
        self.driver.refresh()

    def debug_mouse(self):
        """ Debug mouse actions by drawing red circle on current mouse location """
        logger.info("Adding red color over mouse location to debug mouse")
        script = \
            """
            document.addEventListener('mousemove', function(event) {
            var x = event.clientX + window.scrollX;
            var y = event.clientY + window.scrollY;
            console.log("Mouse:", x, y)

            var dot = document.createElement('div');
            dot.style.position = 'absolute';
            dot.style.left = x + 'px';
            dot.style.top = y + 'px';
            dot.style.width = '3px';
            dot.style.height = '3px';
            dot.style.backgroundColor = 'red';

            document.body.appendChild(dot);
            });
            """
        self.driver.execute_script(script)

    def scroll(self, x, y, element="body", method="incremental", incremental_stepX=5, incremental_stepY=5, sleep=0,
               func="scrollTo"):
        """
        Scroll webpage or webelement by given coordinate::
        :param x: x coordinate
        :param y: y coordinate
        :param element: body or webelement
        :param method: direct or incremental
        :param incremental_stepX: increase step X
        :param incremental_stepY: increase step Y
        :param sleep: sleep on each step
        :param func: function name (scrollTo | scrollBy)
        """
        logger.debug(f"Method: {method}, (x, y): {x, y}, IncrementalStepX-Y: {incremental_stepX, incremental_stepY}, "
                     f"Sleep on each step: {sleep}")
        if method == "direct":
            if element == "body":
                self.driver.execute_script(f"window.{func}({x}, {y});")
            else:
                self.driver.execute_script(f"arguments[0].{func}({x}, {y});", element)
        elif method == "incremental":
            is_x, is_y = False, False
            _x, _y = 0, 0
            if element == "body":
                while True:
                    if _x <= x:
                        self.driver.execute_script(f"window.{func}({incremental_stepX}, 0);")
                        _x += incremental_stepX
                    else:
                        is_x = True
                    if _y <= y:
                        self.driver.execute_script(f"window.{func}(0, {incremental_stepY});")
                        _y += incremental_stepY
                    else:
                        is_y = True
                    time.sleep(sleep)

                    if is_x and is_y:
                        break
            else:
                while True:
                    if _x <= x:
                        self.driver.execute_script(f"arguments[0].{func}({incremental_stepX}, 0);", element)
                        _x += incremental_stepX
                    else:
                        is_x = True
                    if _y <= y:
                        self.driver.execute_script(f"arguments[0].{func}(0, {incremental_stepY});", element)
                        _y += incremental_stepY
                    else:
                        is_y = True
                    time.sleep(sleep)

                    if is_x and is_y:
                        break

        else:
            raise WebDriverException("No such method detected!")

    def scrollBy(self, x, y, element="body", method="incremental", incremental_stepX=5, incremental_stepY=5, sleep=0):
        return self.scroll(x, y, element, method, incremental_stepX, incremental_stepY, sleep, func="scrollBy")

    def scrollTo(self, x, y, element="body", method="incremental", incremental_stepX=5, incremental_stepY=5, sleep=0):
        return self.scroll(x, y, element, method, incremental_stepX, incremental_stepY, sleep, func="scrollTo ")

    def scrollToBottom(self, element="body"):
        if element == "body":
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", element)


class length_of_window_handles_become(object):
    """ Wait until length of window handles changes """

    def __init__(self, window_handles_length):
        self.expected_count = window_handles_length

    def __call__(self, driver):
        logger.debug(f"Length of window_handles changes to {len(driver.window_handles)}")
        return len(driver.window_handles) == self.expected_count


class length_of_window_handles_greater_than(object):
    """ Wait until length of window handles changes """

    def __init__(self, window_handles_length):
        self.expected_count = window_handles_length

    def __call__(self, driver):
        logger.debug(f"Length of window_handles changes to {len(driver.window_handles)}")
        return len(driver.window_handles) > self.expected_count


class length_of_window_handles_less_than(object):
    """ Wait until length of window handles changes """

    def __init__(self, window_handles_length):
        self.expected_count = window_handles_length

    def __call__(self, driver):
        logger.debug(f"Length of window_handles changes to {len(driver.window_handles)}")
        return len(driver.window_handles) < self.expected_count


def _multiWait(driver, locators, max_polls, output_type):
    """ multiWait in given timeout """
    logger.debug(f"Locators: {locators} and Max-Polls: {max_polls}")
    wait = WebDriverWait(driver, 1)
    cp = 0
    while cp < max_polls:
        cp += 1
        for i, loc in enumerate(locators):
            if isinstance(loc, dict):
                func = loc.get('func')
                if func is not None:
                    function_args = loc.get('args')
                    if function_args is None:
                        function_args = ()
                    function_kwds = loc.get('kwargs')
                    if function_kwds is None:
                        function_kwds = {}
                    if func(*function_args, **function_kwds):
                        return i
                    time.sleep(1)
                else:
                    ec = loc.get('ec')
                    if ec is None:
                        ec = EC.presence_of_element_located(loc.get('locator'))
                    methods = loc.get('methods')
                    try:
                        element = wait.until(ec)
                        logger.debug(f"Element found at {loc.get('locator')}")
                        if methods is not None:
                            logger.debug(f"{loc.get('locator')} - Methods: {methods}")
                            if not all([eval(f"element.{m}()", {'element': element}) for m in methods]):
                                raise TimeoutException
                        logger.debug(f"All methods exist on {loc.get('locator')}")
                        return i if output_type == 'id' else element
                    except TimeoutException:
                        pass
            else:
                if callable(loc):
                    if loc():
                        return i
                    time.sleep(1)
                else:
                    try:
                        element = wait.until(EC.presence_of_element_located(loc))
                        logger.debug(f"Element found at {loc}")
                        return i if output_type == 'id' else element
                    except TimeoutException:
                        pass

        logger.debug(f"Current-Polls: {cp}")


def multiWait(
        driver: webdriver,
        locators: List[Union[Callable, Tuple, Dict]],
        max_polls: int,
        output_type: str = 'id',
        refresh_url_every_n_sec: Optional[int] = None) -> Any:
    """
    Wait until any element found in the DOM
    :param driver: a WebDriver instance
    :type locators: list[func, tuples] or list[dict[func, loc]]
    :param locators: a list of locators or locator with its method like is_displayed
    :param max_polls: max number of time check given locator
    :param output_type: 'id' to get locator id or 'element' to get the resulting element
    :param refresh_url_every_n_sec: refresh the url every n seconds, if provided
    :return: output as specified by the output parameter
    :raises: TimeoutException if none of the elements are present in the DOM
    """
    iters = 0
    if refresh_url_every_n_sec is not None:
        iters = int(max_polls / refresh_url_every_n_sec)
        max_polls = refresh_url_every_n_sec

    resp = _multiWait(driver, locators, max_polls, output_type)
    if refresh_url_every_n_sec is not None:
        for _ in range(iters - 1):
            if resp is None:
                driver.refresh()
            else:
                return resp
        resp = _multiWait(driver, locators, max_polls, output_type)

    if resp is None:
        raise TimeoutException("None of the given element is present in the DOM!")
    return resp


def multiWaitNsec(driver, locators, _time, timeout, refresh_url_every_n_sec=None):
    """ MultiWait should be persistent for given time """
    ID = None
    for i in range(_time):
        ID = multiWait(driver, locators, timeout, refresh_url_every_n_sec=refresh_url_every_n_sec)
        logger.info(f"Visible locator: {locators[ID]} && Persistency: {i + 1} seconds")
        time.sleep(1)
    return ID


def slow_type(element, content):
    """ Type slowly with custom speed """
    logger.debug(f"Sending {content} to web-element")
    for x in content:
        element.send_keys(x)
        time.sleep(random.uniform(0.2, 0.4))


from selenium.webdriver.common.by import By


class TableScraper:
    @staticmethod
    def extract_links(element):
        return element.get_attribute("href") if 'http' in element.get_attribute("href") else element.get_attribute("src")

    def extract_cell_data(self, cells, extract_links=False, include_elements=False, attribute=None):
        row_data = []
        for cell in cells:
            cell_data = {'text': cell.text}
            if extract_links:
                links = [self.extract_links(link_element) for link_element in cell.find_elements(By.TAG_NAME, "a")]
                cell_data['links'] = links
            if include_elements:
                cell_data['element'] = cell
            if attribute:
                cell_data['attr'] = cell.get_attribute(attribute)
            if not (extract_links or include_elements or attribute):
                row_data.append(cell.text)
            else:
                row_data.append(cell_data)
        return row_data

    def scrape(self, table_element, number_of_rows=0, number_of_columns=0, include_header=False, extract_links=False,
               reverse=False, include_elements=False, attribute=None):
        """
        Scrape given table element
            -> extract_links or include_elements cannot be true at a time
        :param table_element: webdriver table element
        :param number_of_rows: number of rows to scrape
        :param number_of_columns: number of columns to scrape
        :param include_header: include header or not
        :param extract_links: get associated links or not
        :param reverse: reverse the table or not
        :param include_elements: get associated element or not
        :param attribute: function to get custom property from cell element
        :return: dict of thead and tbody containing list of table elements text or list of dict of table element, text and custom properties
        """
        scraped_data = {
            "thead": [],
            "tbody": [],
        }
        # Table head
        if include_header:
            table_header = table_element.find_element(By.TAG_NAME, "thead")
            header_rows = table_header.find_elements(By.TAG_NAME, "tr")
            if reverse:
                header_rows.reverse()
            for header_row in header_rows:
                header_cells = header_row.find_elements(By.TAG_NAME, "th")
                if reverse:
                    header_cells.reverse()
                if number_of_columns == 0:
                    number_of_columns = len(header_cells)
                scraped_data["thead"].append(
                    self.extract_cell_data(header_cells[:number_of_columns], extract_links, include_elements, attribute))

        # Table Body
        table_body = table_element.find_element(By.TAG_NAME, "tbody")
        body_rows = table_body.find_elements(By.TAG_NAME, "tr")
        if reverse:
            body_rows.reverse()
        if number_of_rows == 0:
            number_of_rows = len(body_rows)
        for body_row in body_rows[:number_of_rows]:
            body_cells = body_row.find_elements(By.TAG_NAME, "td")
            if reverse:
                body_cells.reverse()
            if number_of_columns == 0:
                number_of_columns = len(body_cells)
            scraped_data["tbody"].append(
                self.extract_cell_data(body_cells[:number_of_columns], extract_links, include_elements, attribute))
        return scraped_data
