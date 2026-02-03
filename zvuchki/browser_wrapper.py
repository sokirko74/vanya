import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from googleapiclient.discovery import build
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains, ActionBuilder
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import json
import time
import urllib.parse
import re


class TBrowser:
    def __init__(self, logger, use_cache=True):
        self.browser = None
        self.logger = logger
        self.use_cache = use_cache
        self.cache_path = os.path.join(os.path.dirname(__file__), "search_request_cache.txt")
        self.all_requests = dict()
        self.all_requests_without_spaces = dict()
        self.last_channel_name = None
        self.google_cse = build(
            "customsearch", "v1",
            developerKey=os.environ.get('GOOGLE_API_KEY')
        )

        if os.path.exists(self.cache_path) and self.use_cache:
            with open(self.cache_path) as inp:
                s = inp.read()
                if len(s) > 0:
                    self.all_requests = json.loads(s)
                    for k, v  in self.all_requests.items():
                        self.all_requests_without_spaces[k.replace(' ', '')] = v

    def init_chrome(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--verbose")
        options.add_argument("--log-path=chromedriver.log")
        options.add_argument("enable-automation")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        self.browser = webdriver.Chrome(
            options=options,
            )
        self.browser.set_page_load_timeout(20)
        self.browser.set_script_timeout(18)
        self.browser.set_window_position(0, 0)

    def start_browser(self):
        #self.init_firefox()
        self.init_chrome()

    def attach_to_browser(self, address):
        options = webdriver.ChromeOptions()
        assert not address.startswith('http')
        options.debugger_address = address
        options.add_argument("enable-automation")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        self.logger.info ("attach to chrome {}..".format(address))
        self.browser = webdriver.Chrome(
            options=options)
        self.browser.set_page_load_timeout(20)
        self.browser.set_script_timeout(18)

    def close_all_windows(self):
        for handle in self.browser.window_handles[1:]:
            self.browser.switch_to.window(handle)
            self.browser.close()
        self.browser.get('about:blank')

    def close_browser(self):
        if self.browser is not None:
            self.browser.close()
            time.sleep(1)
            self.browser.quit()

    def mouse_click(self, x, y):
        self.browser.execute_script('el = document.elementFromPoint({}, {}); el.click();'.format(x, y))

    def send_ctrl_end(self, timeout=2):
        self.logger.info('send_ctrl_end and wait ...')
        ActionChains(self.browser) \
            .key_down(Keys.CONTROL) \
            .key_down(Keys.END) \
            .perform()
        time.sleep(timeout)


    def send_left(self):
        ActionChains(self.browser) \
            .key_down(Keys.LEFT) \
            .perform()

    def send_right(self):
        try:
            self.logger.info('send_right')
            element = self.browser.switch_to.active_element
            time.sleep(0.1)
            element.send_keys(Keys.RIGHT)
        except WebDriverException as exp:
            print("exception: {}".format(exp))
            return False

        # ActionChains(self.browser) \
        #     .key_down(Keys.RIGHT) \
        #     .perform()

    def send_ctrl_home(self, timeout=1):
        self.logger.info('send_ctrl_home')
        ActionChains(self.browser) \
            .key_down(Keys.CONTROL) \
            .key_down(Keys.HOME) \
            .perform()
        time.sleep(timeout)

    def send_shift_n(self):
        ActionChains(self.browser) \
            .key_down(Keys.SHIFT) \
            .key_down('n') \
            .perform()

    def send_shift_p(self):
        ActionChains(self.browser) \
            .key_down(Keys.SHIFT) \
            .key_down('p') \
            .perform()

    # def send_f(self):
    #     ActionChains(self.browser) \
    #         .key_down('f') \
    #         .perform()

    def navigate(self, url):
        try:
            self.browser.get(url)
        except selenium.common.exceptions.TimeoutException as e:
            print("exception in navigate: {}".format(e))
            time.sleep(2)

    def send_f(self):
        try:
            element = self.browser.switch_to.active_element
            time.sleep(0.2)
            print ("send f")
            element.send_keys("f")
        except WebDriverException as exp:
            print("exception: {}".format(exp))
            return False


    def play_youtube(self, url):
        try:
            self.last_channel_name = None
            time.sleep(1)
            print("play {}".format(url))
            self.navigate(url)

            print ("sleep 3 sec")
            time.sleep(3)


            element = self.browser.switch_to.active_element
            time.sleep(2)


            # print ("send к")
            # element.send_keys("k")
            # time.sleep(1)

            #time.sleep(0.5)
            #print ("send f")
            #element.send_keys("f")

            #time.sleep(0.5)
            #print ("send p")
            #element.send_keys("p")
            # Source - https://stackoverflow.com/a
            # Posted by undetected Selenium, modified by community. See post 'Timeline' for change history
            # Retrieved 2026-01-29, License - CC BY-SA 4.0

            channel_elem_class = "ytd-channel-name"

            try:
                channel_elem = WebDriverWait(self.browser, 20).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, channel_elem_class)))
                #channel_name_elem = self.browser.find_element(By.CLASS_NAME, channel_elem_class)
                if channel_elem:
                    channel_name = str(channel_elem.text)
                    self.logger.info('play channel "{}"'.format(channel_name))
                    self.last_channel_name = channel_name
            except TimeoutException:
                self.logger.error("cannot find(wait) element {}".format(channel_elem_class))

            return True
        except WebDriverException as exp:
            print("exception: {}".format(exp))
            return False

    def _parse_serp(self):
        search_results = []
        self.send_ctrl_end()
        self.send_ctrl_end()
        self.send_ctrl_end()
        self.send_ctrl_home()
        for element in self.browser.find_elements(By.TAG_NAME, "a"):
            url = element.get_attribute("href")
            if url is not None and url != '#' and url.startswith('http'):
                if "youtube.com/watch" in url and re.search('t=[0-9]', url) is None:
                    if url not in search_results:
                        search_results.append(url)
        return search_results

    def get_cached_request(self, request):
        return self.all_requests_without_spaces.get(request.replace(' ', ''))

    def _cache_request(self, request, search_results):
        self.all_requests.get(request.replace(' ', ''))
        self.all_requests[request] = search_results
        self.all_requests_without_spaces[request.replace(' ', '')] = search_results
        if search_results:
            with open(self.cache_path, "w") as outp:
                json.dump(self.all_requests, outp, ensure_ascii=False, indent=4)

    def send_request_old(self, search_engine_request):
        self.browser.get("https://www.google.ru/videohp?hl=ru")
        time.sleep(3)
        element = self.browser.switch_to.active_element
        element.send_keys(search_engine_request)
        time.sleep(1)
        element.send_keys(Keys.RETURN)
        time.sleep(3)
        search_results = self._parse_serp()
        self.logger.info("found {} links in serp".format(len(search_results)))
        self._cache_request(search_engine_request, search_results)
        return search_results

    def send_request_as_human(self, search_engine_request):
        q = urllib.parse.quote(search_engine_request + " site:youtube.com")
        url  = "https://www.google.ru/search?hl=ru&tbm=vid&q=" + q
        self.navigate(url)
        time.sleep(1)
        search_results = self._parse_serp()
        self.logger.info("found_as_human {} links in serp".format(len(search_results)))

        self._cache_request(search_engine_request, search_results)
        return search_results

    def send_request_via_api(self, search_engine_request):
        res = (
            self.google_cse.cse()
            .list(
                q=search_engine_request,
                cx="23bc393c3e0864c5d",
            )
            .execute()
        )
        search_results =   list(i['link'] for i in res['items'])
        return search_results

    def send_request(self, search_engine_request):
        return self.send_request_as_human(search_engine_request)
	
	# на волгарь выдала daewoo
        #return self.send_request_via_api(search_engine_request)


if __name__ == "__main__":
    b = TBrowser()
    b.start_browser()
    b.play_youtube('https://www.youtube.com/watch?v=NaiCfIcutbM', 10)
    time.sleep(10000)
