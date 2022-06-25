import pandas as pd
import json
import time
import undetected_chromedriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import PySimpleGUI as sg
from webdriver_manager.chrome import ChromeDriverManager

"""
pip3 install undetected_chromedriver PySimpleGUI selenium selenium_stealth pandas webdriver_manager
"""


def ui():
    layout = [
        [sg.Text('Domain', size=(15, 1)), sg.InputText(size=(42, 1))],
        [sg.Text('Keywords', size=(15, 1)), sg.Multiline(
            size=(40, 10), key='textbox')],
        [sg.Text('Cookie File', size=(15, 1)), sg.Text('None selected', size=(
            30, 1)), sg.FileBrowse(file_types=(("JSON Files", "*.json"),))],
        [sg.Submit('Start Analysis'), sg.Cancel()]
    ]
    window = sg.Window('Google Search Result Analysis',
                       layout, element_justification='c')
    event, values = window.read()
    window.close()
    return event, values


def readyDriver():
    # executable_path="chromedriver.exe"
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    driver.maximize_window()
    return driver


def injectCookies(driver, cookie_file):
    f = open(cookie_file)
    cookies = json.load(f)
    driver.get('https://google.com')
    for cookie in cookies:
        try:
            c = {'name': cookie['name'], 'value': cookie['value'],
                 'domain': cookie['domain']}
            driver.add_cookie(c)
            # print(c)
        except:
            pass
    driver.get('https://google.com')


def main():
    event, values = ui()
    if event == 'Cancel':
        exit()
    print(values)
    our_domain = values[0]
    if our_domain == '':
        sg.Popup('Error! no domain provided. the program is exiting')
        exit()
    if values['textbox'] == '':
        sg.Popup('Error! no keyword provided, the program is exiting')
        exit()
    cookie_file = values['Browse']
    if cookie_file == '':
        sg.Popup('Error! No cookie file was provided')
        exit()
    keywords = values['textbox'].split('\n')
    driver = readyDriver()
    injectCookies(driver, cookie_file)
    output = []
    driver.get('https://www.google.com/?gl=us&hl=en&pws=0')
    driver.find_element(
        By.XPATH, '//input[@name="q"]').send_keys('This is a test')
    driver.find_element(By.XPATH, '//input[@name="q"]').send_keys(Keys.ENTER)
    time.sleep(2)
    if "captcha" in (driver.page_source):
        print('captcha !!! please solve the puzzle...')
        while True:
            if not "captcha" in (driver.page_source):
                break
    for keyword in keywords:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//input')))
        driver.find_element(By.XPATH, '//input').clear()
        driver.find_element(By.XPATH, '//input').send_keys(keyword)
        driver.find_element(
            By.XPATH, '//input[@name="q"]').send_keys(Keys.ENTER)
        time.sleep(1)
        if "captcha" in (driver.page_source):
            print('captcha !!! please solve the puzzle...')
            while True:
                if not "captcha" in (driver.page_source):
                    break
        exist = False
        search_results = driver.find_elements(
            By.XPATH, '//div[@data-async-context and div[contains(@class,"g")]]/div[contains(@class,"g")]')
        for index, search_result in enumerate(search_results):
            search_result_title = search_result.find_element(
                By.XPATH, './/h3').text
            search_result_url = search_result.find_element(
                By.XPATH, './/a[@href and @data-ved]').get_attribute('href')
            if our_domain in search_result_url:
                print(keyword, "; Matched at: ", index+1, '; Title: ',
                      search_result_title, '; URL: ', search_result_url)
                output.append({
                    'Found': True,
                    'Keyword': keyword,
                    'Matched at': index,
                    'search_result_title': search_result_title,
                    'search_result_url': search_result_url
                })
                exist = True
        if exist == False:
            output.append({
                'Found': False,
                'Keyword': keyword,
                'Matched at': None,
                'search_result_title': None,
                'search_result_url': None
            })
            print('Not found ! ', keyword)
    pd.DataFrame(output).to_csv('output.csv', index=False)


if __name__ == '__main__':
    main()
