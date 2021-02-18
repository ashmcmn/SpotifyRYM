import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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

driver = webdriver.Chrome('chromedriver', chrome_options=chrome_options)

client_id = 'SPOTIFY_CLIENT_ID_HERE'
client_secret = 'SPOTIFY_CLIENT_SECRET_HERE'
username = 'RYM_USERNAME_HERE'
password = 'RYM_PASSWORD_HERE'

client_credentials_manager = spotipy.oauth2.SpotifyClientCredentials(client_id, client_secret)
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

artist_id = '[Artistxxxxxxx]'
artist_id = artist_id[7:-1]
spotify_url = 'spotify:album:xxxxxxxxxxxxxxxxxx' # has to be an release uri

driver.get('https://rateyourmusic.com/account/login')
driver.find_element(By.ID, 'username').send_keys(username)
driver.find_element(By.ID, 'password').send_keys(password)

with wait_for_page_load(driver):
    driver.find_element(By.ID, 'login_submit').click()

driver.get('https://rateyourmusic.com/releases/ac?artist_id={}'.format(artist_id))

try:
    myElem = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, '//*[@id="categorye"]')))
except TimeoutException:
    print "timed out"

album = spotify.album(spotify_url)

if album['album_type'] == 'single':
    if len(album['tracks']['items']) > 1:
        driver.find_element(By.XPATH, '//*[@id="categorye"]').click()
    else:
        driver.find_element(By.XPATH, '//*[@id="categoryi"]').click()

date = str(album['release_date']).split('-')

year = Select(driver.find_element(By.ID, 'year'))
year.select_by_value(date[0])

month = Select(driver.find_element(By.ID, 'month'))
month.select_by_value(date[1])

day = Select(driver.find_element(By.ID, 'day'))
day.select_by_value(date[2])

title = album['name']
driver.find_element(By.ID, 'title').send_keys(title)

driver.find_element(By.ID, 'format59').click()  # select lossless digital
driver.find_element(By.ID, 'attrib122').click()  # select downloadable
driver.find_element(By.ID, 'attrib123').click()  # select streaming

track_info = ''
i = 1
for track in album['tracks']['items']:
    minutes, seconds = divmod(int(track['duration_ms']) / 1000, 60)
    track_info += '{} | {} | {:0>2.0f}:{:0>2.0f}\n'.format(i, track['name'], minutes, seconds)
    i += 1

driver.find_element(By.ID, 'goAdvancedBtn').click()  # select advanced track entry
driver.find_element(By.ID, 'track_advanced').send_keys(track_info)  # enter tracks
driver.find_element(By.ID, 'goSimpleBtn').click()  # swap back to simple entry for submission

driver.find_element(By.ID, 'notes').send_keys(album['external_urls']['spotify'])  # leave spotify url in source

driver.find_element(By.ID, 'previewbtn').click()  # enter preview for user validation
