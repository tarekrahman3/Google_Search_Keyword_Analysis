import pandas as pd
import json
import os
import time
import undetected_chromedriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import PySimpleGUI as sg
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote


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
        except:
            pass
    driver.get('https://google.com')


def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1
    return path


def main():
    event, values = ui()
    if event == 'Cancel':
        exit()
    print(values)
    our_domain = values[0].strip()
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
    for keyword in keywords:
        # WebDriverWait(driver, 5).until(
        #     EC.presence_of_element_located((By.XPATH, '//input')))
        driver.get(
            f"https://www.google.com/search?q={quote(keyword.strip())}&gl=us&hl=en&pws=0")
        time.sleep(1.5)
        if "and not a robot" in driver.page_source:
            print('captcha !!! please solve the puzzle...')
            while True:
                if not "and not a robot" in driver.page_source:
                    break
        exist = False
        try:
            driver.execute_script('arguments[0].remove()', driver.find_element(
                By.XPATH, '//span[text()="People also ask"]/ancestor::div[3]'))
        except:
            pass
        search_results = driver.find_elements(
            By.XPATH, '//*[@class="yuRUbf" or @class="ct3b9e"]')
        for index, search_result in enumerate(search_results):
            search_result_title = search_result.find_element(
                By.XPATH, './/h3').text
            search_result_url = search_result.find_element(
                By.XPATH, './/a').get_attribute('href')
            if our_domain in search_result_url:
                print(keyword, "; Matched at: ", index+1, '; Title: ',
                      search_result_title, '; URL: ', search_result_url)
                output.append({
                    'Google Search URL': driver.current_url,
                    'Total Results': len(search_results),
                    'Found': True,
                    'Keyword': keyword,
                    'Matched at': index+1,
                    'search result title': search_result_title,
                    'search result url': search_result_url
                })
                exist = True
                break
        if exist == False:
            output.append({
                'Google Search URL': driver.current_url,
                'Total Results': len(search_results),
                'Found': False,
                'Keyword': keyword,
                'Matched at': None,
                'search result title': None,
                'search result url': None
            })
            print('Not found ! -- ', keyword)
    driver.quit()
    filename = uniquify('output.csv')
    pd.DataFrame(output).to_csv(filename, index=False)
    sg.Popup("Keyword analysis has been finished", title='Done',)


if __name__ == '__main__':
    main()
