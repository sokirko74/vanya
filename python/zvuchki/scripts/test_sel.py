from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service


def main():
    options = ChromeOptions()
    options.debugger_address = "127.0.0.1:" + '8888'
    browser = webdriver.Chrome(
        options=options)
    browser.get("http://aot.ru")


if __name__ == "__main__":
    main()
