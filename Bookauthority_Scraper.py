from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
import undetected_chromedriver as uc
import pandas as pd
import time
import unidecode
import csv
import sys
import numpy as np

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = 'normal'
    chrome_options.add_argument("--disable-notifications")
    # disable location prompts & disable images loading
    prefs = {"profile.default_content_setting_values.geolocation": 2, "profile.managed_default_content_settings.images": 2, "profile.default_content_setting_values.cookies": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(300)

    return driver

def scrape_bookauthority(path):

    start = time.time()
    print('-'*75)
    print('Scraping bookauthority.org ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame()

    # if no books links provided then get the links
    if path == '':
        name = 'bookauthority_data.csv'
        # getting the books under each category
        cats = ['https://bookauthority.org/books/best-business-books', 'https://bookauthority.org/books/best-leadership-books', 'https://bookauthority.org/categories/personal-development/productivity', 'https://bookauthority.org/books/best-self-help-books', 'https://bookauthority.org/books/best-self-improvement-books', 'https://bookauthority.org/books/best-happiness-books', 'https://bookauthority.org/categories/personal-development/interpersonal-and-social-skills', 'https://bookauthority.org/books/best-world-history-books', 'https://bookauthority.org/books/best-women-in-history-books', 'https://bookauthority.org/books/best-slavery-books', 'https://bookauthority.org/books/best-world-war-ii-books', 'https://bookauthority.org/books/best-world-war-i-books', 'https://bookauthority.org/books/best-american-civil-war-books', 'https://bookauthority.org/books/best-iraq-war-books', 'https://bookauthority.org/categories/history/united-states-history', 'https://bookauthority.org/categories/biographies/biographies', 'https://bookauthority.org/books/best-sociology-books']
        
        links = []
        ncats = len(cats)
        # scraping books under each category
        for j, link in enumerate(cats):        
            try:
                print(f'Scraping books urls under Category {j+1}/{ncats}')
                driver.get(link)
                if '/books/' in link:
                    header = wait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).get_attribute('textContent')
                    cat = header.split('Best')[-1].replace('Books of All Time', '').strip()
                    links.append((link, cat))
                elif '/categories/' in link:
                    header = wait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).get_attribute('textContent')
                    cat = header.replace('Explore', '').replace('Books By Category', '').strip()
                    spans = wait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.cat3-wrapper")))
                    for span in spans:
                        url = wait(span, 5).until(EC.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('href')
                        if '/books/' in url:
                            links.append((url, cat))
            except Exception as err:
                print(f'Warning: Failed to get the links of category link {j+1}/{ncats} due to the following error:')
                print(err)
                pass

        # saving the links to a csv file
        print('Exporting links to a csv file ....')
        with open('bookauthority_links.csv', 'w', newline='\n', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Link', 'Category'])
            for row in links:
                writer.writerow([row[0], row[1]])


    scraped = []
    if path != '':
        df_links = pd.read_csv(path)
    else:
        df_links = pd.read_csv('bookauthority_links.xlsx')

    links = df_links['Link'].values.tolist()
    cats = df_links["Category"].values.tolist()
    name = path.split('\\')[-1][:-4]
    name = name + '_data.xlsx'
    try:
        data = pd.read_csv(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass
    # scraping books details
    print('-'*75)
    print('Scraping Books Info...')
    n = 0
    for i, link in enumerate(links):
        try:
            cat = cats[i]
            print('-'*75)
            print(f'Scraping Category: {cat}')         
            if link in scraped: continue
            driver.get(link)
            time.sleep(2)
            books = wait(driver, 30).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='book accepted normal']")))
            for book in books:
                details = {}
                details['Category'] = cat
                print(f'Scraping the info for book {n+1}')
                n += 1
                title, subtitle = '', ''
                try:
                    title = wait(book, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.main"))).get_attribute('textContent').title().strip()
                    subtitle = wait(book, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3.sub"))).get_attribute('textContent').strip()
                except:
                    pass

                details['Title'] = title
                details['Subtitle'] = subtitle
                details['Title Link'] = link

                author, author_link = '', ''
                try:
                    h3 = wait(book, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3.authors")))
                    tags = wait(h3, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                    for tag in tags:
                        author += tag.get_attribute('textContent') + ', '
                        author_link += tag.get_attribute('href') + ', '
                    author = author[:-2]
                    author_link = author_link[:-2]
                except:
                    pass

                details['Author'] = author
                details['Author Link'] = author_link

                # date
                date = ''
                try:
                    date = wait(book, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.date"))).get_attribute('textContent').split('|')[-1].strip()
                except:
                    pass          
                
                details['Release Year'] = date                
                
                # rating
                rating = ''
                try:
                    rating = wait(book, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.our-rating"))).get_attribute('textContent').strip()
                except:
                    pass          
                
                details['Rating'] = rating                
                
                # Amazon Link
                Amazon = ''
                try:
                    Amazon = wait(book, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.book-title"))).get_attribute('href')
                    if 'amazon.com' not in Amazon:
                        Amazon = ''
                except:
                    pass          
                
                details['Amazon Link'] = Amazon
                                         
                # appending the output to the datafame            
                data = data.append([details.copy()])
                # saving data to csv file each 100 links
                if np.mod(i+1, 100) == 0:
                    print('Outputting scraped data to csv file ...')
                    data.to_csv(name, encoding='UTF-8', index=False)
        except:
            pass

    # optional output to Excel
    data.to_excel(name, index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'bookauthority.org scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":
    
    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_bookauthority(path)

