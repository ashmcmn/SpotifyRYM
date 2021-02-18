import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib
import spotipy

def wait_for(condition_function):
    start_time = time.time()
    while time.time() < start_time + 3:
        if condition_function():
            return True
        else:
            time.sleep(0.1)
    raise Exception('Timeout waiting')

class wait_for_page_load(object):
    def __init__(self, browser):
        self.browser = browser

    def __enter__(self):
        self.old_page = self.browser.find_element_by_tag_name('html')

    def page_has_loaded(self):
        new_page = self.browser.find_element_by_tag_name('html')
        return new_page.id != self.old_page.id

    def __exit__(self, *_):
        wait_for(self.page_has_loaded)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

rym_url = str(raw_input('RYM Link: ')) # if using in ide, add space before pressing enter to avoid opening url

driver = webdriver.Chrome('chromedriver', chrome_options=chrome_options)

client_id = 'SPOTIFY_CLIENT_ID_HERE'
client_secret = 'SPOTIFY_CLIENT_SECRET_HERE'
username = 'RYM_USERNAME_HERE'
password = 'RYM_PASSWORD_HERE'

client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id, client_secret)
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

artist = rym_url.split('/')[5].replace('-', ' ')
title = rym_url.split('/')[6].replace('-', ' ')

spotify_url = spotify.search(artist+' '+title, type="album")['albums']['items'][0]['external_urls']['spotify']
driver.get(spotify_url)

image_url = driver.find_element(By.XPATH, '/html/head/meta[8]').get_attribute('content')
imgpath = 'img/'+artist.replace(' ', '')+title.replace(' ', '')+'.jpeg'

driver.get('https://rateyourmusic.com/account/login')
driver.find_element(By.ID, 'username').send_keys(username)
driver.find_element(By.ID, 'password').send_keys(password)

with wait_for_page_load(driver):
    driver.find_element(By.ID, 'login_submit').click()

driver.get(rym_url)

img = urllib.urlretrieve(image_url, imgpath)

driver.find_element(By.XPATH, '//*[@id="content"]/div[8]/div[3]/div/div/a[3]').click()

driver.find_element(By.ID, 'upload_file').send_keys(os.getcwd()+'/'+imgpath)
driver.find_element(By.ID, 'source').send_keys(spotify_url)
