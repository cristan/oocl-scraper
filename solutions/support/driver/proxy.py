import shutil
from pathlib import Path


class Proxy:
    def __init__(self, proxy_str=None, extension_dir='proxy_extension', replace_extension=True):
        """
        Proxy class to use with Selenium and Requests.

        This class is designed to handle proxy configurations for HTTP(S) requests and Selenium WebDriver.

        Parameters:
            :param proxy_str: A string representing the proxy:
                Format: [protocol]://username:password@host:port OR [protocol]://host:port
            :param extension_dir: path to directory where extension can be created
            :param replace_extension: This can be false in case where old extension_dir is used

        Properties:
            - protocol (str): The proxy protocol (e.g., 'http' or 'https'). Defaults to 'http'.
            - username (str or None): The proxy username. Defaults to None.
            - password (str or None): The proxy password. Defaults to None.
            - host (str): The proxy server's hostname or IP address.
            - port (int): The proxy server's port.

        Methods:
            - to_dict (dict): Returns the proxy as a dictionary.
            - chrome_proxy (dict): Returns the proxy configuration for Chrome.
            - create_proxy_extension (str): Creates a Chrome extension with the proxy configuration.
            - remove_chrome_extension (None): Removes the created Chrome proxy extension directory.
        """
        self.proxy_str = proxy_str
        self.extension_dir = Path(extension_dir).resolve()
        self.replace_extension = replace_extension

        self.protocol = None
        self.username = None
        self.password = None
        self.host = None
        self.port = None

        if proxy_str:
            self._parse_proxy()

    def __iter__(self):
        yield 'proxy_str', self.proxy_str
        yield 'protocol', self.protocol
        yield 'username', self.username
        yield 'password', self.password
        yield 'host', self.host
        yield 'port', self.port

    def to_dict(self):
        return dict(self.__iter__())

    @property
    def has_credentials(self):
        return '@' in self.proxy_str

    def _parse_proxy(self):
        """
        Parses the proxy string to extract protocol, username, password, hostname, and port.
        """
        if '://' in self.proxy_str:
            self.protocol = self.proxy_str[:self.proxy_str.find("://")]
            proxy_str = self.proxy_str[self.proxy_str.find("://") + 3:]  # Remove protocol part
        else:
            self.protocol = 'http'  # Default to HTTP if no protocol is specified
            proxy_str = self.proxy_str

        # Check if the string contains '@' (username:password)
        if '@' in proxy_str:
            username_and_password = proxy_str.split("@")[0]
            proxy_str = proxy_str.split("@")[1]
            self.username = username_and_password.split(":")[0]
            self.password = username_and_password.split(":")[1]
        self.host = proxy_str.split(":")[0]
        self.port = int(proxy_str.split(":")[1])

    @property
    def requests_proxy(self):
        """Returns the proxy as a dictionary for use in requests"""
        return {
            'http': self.proxy_str,
            'https': self.proxy_str
        }

    @property
    def chrome_proxy(self):
        """
        Returns the proxy configuration as a dictionary ready to be used with Selenium WebDriver.
        """
        if not self.protocol or not self.host or not self.port:
            raise ValueError("Invalid proxy configuration")

        if not self.has_credentials:
            return f'--proxy-server={self.protocol}://{self.host}:{self.port}'
        else:
            self.create_proxy_extension()
            return f'--load-extension={self.extension_dir.absolute()}'

    def create_proxy_extension(self):
        """
        Generates a proxy extension for Chrome with the given proxy settings.
        :return: Path to the proxy extension.
        """
        bg_js_p1 = """
        authCredentials: {
            username: "%s",
            password: "%s"
        }
        """ % (self.username, self.password)

        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version": "22.0.0"
        }
        """

        background_js = """
        var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "%s",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
            }
        };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                %s
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
        );
        """ % (self.protocol, self.host, self.port, bg_js_p1)

        if self.replace_extension and self.extension_dir.exists():
            shutil.rmtree(self.extension_dir)
        self.extension_dir.mkdir(parents=True, exist_ok=True)

        with open(self.extension_dir / 'manifest.json', 'w') as f:
            f.write(manifest_json)
        with open(self.extension_dir / 'background.js', 'w') as f:
            f.write(background_js)

    def remove_chrome_extension(self):
        """
        Remove proxy extension directory.
        """
        shutil.rmtree(self.extension_dir, ignore_errors=True)
