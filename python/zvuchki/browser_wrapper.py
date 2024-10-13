import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains, ActionBuilder

import os
import json
import time
import urllib.parse


class TBrowser:
    def __init__(self):
        self.browser = None
        self.cache_path = os.path.join(os.path.dirname(__file__), "search_request_cache.txt")
        self.all_requests = dict()
        self.all_requests_without_spaces = dict()
        if os.path.exists(self.cache_path):
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

    # def init_firefox(self):
    #     opts =  webdriver.FirefoxOptions()
    #     #opts.log.level = "trace"
    #     self.browser = webdriver.Firefox(
    #             options=opts,
    #             executable_path='/snap/bin/geckodriver',
    #             #service_log_path=os.path.join(os.path.dirname(__file__), 'geckodriver.log')
    #                 service_log_path=None
    #             )

    def start_browser(self):
        #self.init_firefox()
        self.init_chrome()

    def attach_to_browser(self, address):
        options = webdriver.ChromeOptions()
        options.debugger_address = address
        options.add_argument("enable-automation")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
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

    def send_ctrl_end(self):
        ActionChains(self.browser) \
            .key_down(Keys.CONTROL) \
            .key_down(Keys.END) \
            .perform()

    def send_ctrl_home(self):
        ActionChains(self.browser) \
            .key_down(Keys.CONTROL) \
            .key_down(Keys.HOME) \
            .perform()

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

    def navigate(self, url):
        try:
            self.browser.get(url)
        except selenium.common.exceptions.TimeoutException as e:
            print("exception in navigate: {}".format(e))
            time.sleep(2)

    def play_youtube(self, url, max_duration):
        try:
            time.sleep(1)
            print("play {}".format(url))
            self.navigate(url)

            print ("sleep 3 sec")
            time.sleep(3)

            # self.browser.switch_to.default_content()
            # elem = self.browser.find_elements(By.XPATH, "//*[contains(text(), 'Accept all')]")
            # if not elem:
            #     elem = self.browser.find_elements(By.XPATH, "//*[contains(text(), 'Принять все')]")
            #
            # if elem:
            #     for i in range(6):
            #         ActionChains(self.browser).send_keys(Keys.TAB).perform()
            #         time.sleep(1)
            #     ActionChains(self.browser).send_keys(Keys.RETURN).perform()
            #
            #     #print("scroll to  @Accept all")
            #     #ActionChains(self.browser).move_to_element(elem[0]).perform()
            #     #time.sleep(1)
            #
            #     #print("click Accept all")
            #     #elem[0].click()
            # else:
            #     print("no accept cookie button found")
            # time.sleep(1)

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

            print("sleep for  {} seconds (video duration)".format(max_duration))
            time.sleep(max_duration)
            print("time elapsed")
            return True
        except WebDriverException as exp:
            print("exception: {}".format(exp))
            return False

    def _parse_serp(self):
        search_results = []
        self.send_ctrl_end()
        time.sleep(1)
        self.send_ctrl_home()
        time.sleep(1)
        for element in self.browser.find_elements(By.TAG_NAME, "a"):
            url = element.get_attribute("href")
            if url is not None and url != '#' and url.startswith('http'):
                if "youtube" in url:
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
        self._cache_request(search_engine_request, search_results)
        return search_results

    def send_request(self, search_engine_request):
        q = urllib.parse.quote(search_engine_request)
        url  = "https://www.google.ru/search?hl=ru&tbm=vid&q=" + q
        self.navigate(url)
        time.sleep(1)
        search_results = self._parse_serp()
        self._cache_request(search_engine_request, search_results)
        return search_results


if __name__ == "__main__":
    b = TBrowser()
    b.start_browser()
    b.play_youtube('https://www.youtube.com/watch?v=NaiCfIcutbM', 10)
    time.sleep(10000)