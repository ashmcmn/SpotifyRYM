import time
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.by import By
from math import ceil
import spotipy
from spotipy import oauth2
import unicodedata


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


client_id = 'SPOTIFY_CLIENT_ID_HERE'
client_secret = 'SPOTIFY_CLIENT_SECRET_HERE'
spotify_username = 'SPOTIFY_USERNAME_HERE'

sp_oauth = oauth2.SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri='http://localhost:8080/callback/', scope='playlist-modify-public playlist-modify-private user-library-read')
token_info = sp_oauth.get_cached_token()

if not token_info:
    auth_url = sp_oauth.get_authorize_url()
    print(auth_url)
    response = str(input('URL: '))

    code = sp_oauth.parse_response_code(response.split('=')[1][:-1])
    token_info = sp_oauth.get_access_token(code)

spotify = spotipy.Spotify(auth=token_info['access_token'])

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

rym_url = str(input('RYM Link: '))

driver = webdriver.Chrome('chromedriver', chrome_options=chrome_options)

driver.get(rym_url)

releases = []

list_name = driver.find_element(By.XPATH, '//*[@id="breadcrumb"]/ul/li[3]').get_attribute('textContent')
table = driver.find_elements(By.CLASS_NAME, 'main_entry')

list_type = 'ranked' if len(driver.find_elements(By.CLASS_NAME, 'number')) > 0 else 'normal'

print('Scraping releases from page 1')

for release in table:
    try:
        artist = release.find_element(By.CLASS_NAME, 'list_artist').get_attribute('textContent')
        name = release.find_element(By.CLASS_NAME, 'list_album').get_attribute('textContent')
        releases.append(unicodedata.normalize('NFKD', artist+' '+name).encode('ascii', 'ignore'))
    except NoSuchElementException:
        print(release.get_attribute('textContent'))

page = 2
lastpage = 1
if len(driver.find_elements(By.CLASS_NAME, 'navlinknum')) > 0:
    if list_type == 'normal':
        if '-' in driver.find_elements(By.CLASS_NAME, 'navlinknum')[-1].get_attribute('textContent'):
            lastpage = int(
                driver.find_elements(By.CLASS_NAME, 'navlinknum')[-1].get_attribute('textContent').split('-')[1])
        else:
            lastpage = int(driver.find_elements(By.CLASS_NAME, 'navlinknum')[-1].get_attribute('textContent'))
    else:
        lastpage = len(driver.find_elements(By.CLASS_NAME, 'navlinknum'))

while page <= lastpage:
    print(f'Scraping releases from page {page}')
    driver.get(rym_url[:-1]+str(page))

    table = driver.find_elements(By.CLASS_NAME, 'main_entry')

    for release in table:
        try:
            artist = release.find_element(By.CLASS_NAME, 'list_artist').get_attribute('textContent')
            name = release.find_element(By.CLASS_NAME, 'list_album').get_attribute('textContent')
            releases.append(unicodedata.normalize('NFKD', artist + ' ' + name).encode('ascii', 'ignore'))
        except NoSuchElementException:
            print(release.get_attribute('textContent'))

    page += 1

uris = []

print('Searching spotify for releases')
for i, r in enumerate(releases):
    if i % (len(releases) // 10) == 0:
        print(f'Searching for release {i+1}/{len(releases)}')
    results = spotify.search(r, type='album')['albums']['items']
    if len(results) > 0:
        tracks = spotify.album_tracks(results[0]['uri'])
        for track in tracks['items']:
            uris.append('spotify:track:'+str(unicodedata.normalize('NFKD', track['id']).encode('ascii', 'ignore'), 'utf-8'))

playlist = spotify.user_playlist_create(spotify_username, list_name)

print(f'Adding {len(uris)} tracks to playlist')
for i in range(int(ceil(len(uris)/100.0))):
    spotify.playlist_add_items(playlist['id'], uris[i*100:min((i+1)*100, len(uris))], 0)
