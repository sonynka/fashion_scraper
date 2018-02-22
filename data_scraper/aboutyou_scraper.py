import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys
import cssutils
from selenium import webdriver

import logging
cssutils.log.setLevel(logging.CRITICAL)


# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    sys.stdout.write('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix))
    # Print New Line on Complete
    if iteration == total:
        print()

data_path = '/Users/sonynka/HTW/IC/data/aboutyou/'

df = pd.DataFrame()

url = 'https://aboutyou.de'
url_clothes = url + '/frauen/bekleidung'

colors = {'black': 38932, 'red': 38931}

color = 'red'
category = 'kleider'

url_category = url_clothes + '/' + category
url_category_filter = url_category + '?bi_color={}'.format(colors[color])
data_path_category = os.path.join(data_path, category)

if not os.path.exists(data_path_category):
    os.makedirs(data_path_category)

# Request category page
page = requests.get(url_category_filter)
if page.status_code != requests.codes.ok:
    raise ValueError('Response code not OK. Url: ' + url_category_filter)

soup = BeautifulSoup(page.content, 'html.parser')

# find sub-categories of category
category_list = soup.find('li', title='Kleider').parent
sub_categories = {}
for sub_category in category_list.find_all('a'):
    name = sub_category.text.lower()
    link = url + sub_category['href']
    sub_categories[name] = link

print('Total subcategories for {} found: {}'.format(category, len(sub_categories)))

for sub_cat_name, sub_cat_link in sub_categories.items():

    print('Downloading sub-category: ' + sub_cat_name)

    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome('/Users/sonynka/Downloads/chromedriver')
    driver.get(sub_cat_link)
    driver.find_element_by_class_name('button_6u2hqh').click()

    # sub_cat_page = requests.get(sub_cat_link)
    sub_cat_soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.close()

    products = sub_cat_soup.find_all('div', class_='categoryTileWrapper_e296pg')

    l = len(products)
    printProgressBar(0, l, prefix='Progress:', suffix='Complete', length=50)

    for idx, product in enumerate(products):
        try:
            link = url + product.a['href']
            product_page = requests.get(link)
            product_soup = BeautifulSoup(product_page.content, 'html.parser')

            # get product details
            product_name = product_soup.find('h1', class_='productName_192josg').text
            product_details = product_soup.find('div', class_='wrapper_1w5lv0w')
            tags = []
            for detail_section in product_details.find_all('div', class_='container_iv4rb4'):
                # section_name = detail_section.p.text
                for tag in detail_section.find_all('li'):
                    tags.append(tag.text.strip())

            product_img = product.find('div', class_='img_162hfdi-o_O-imgTrimmed_16d3go2')['style']
            product_img_link = 'https:' + product_img.split('"')[1].split('?')[0]

            img_name = '{:04d}'.format(idx)
            img_file_name = '{}_{}_{}.jpg'.format(sub_cat_name, color, img_name)
            img_file_path = os.path.join(data_path_category, img_file_name)

            img = requests.get(product_img_link)
            if img.status_code == requests.codes.ok:
                with open(img_file_path, 'wb') as file:
                    file.write(img.content)

            df = df.append({'img_path': os.path.join(category, img_file_name),
                       'img_url': product_img_link,
                       'category': category,
                       'sub_category': sub_cat_name,
                       'color': color,
                       'product_name': product_name,
                       'attributes': tags}, ignore_index=True)

            printProgressBar(idx + 1, l, prefix='Progress:', suffix='Complete', length=50)
        except Exception as e:
            print('Unable to download product # {}'.format(idx), e)

    df = df[['img_path', 'img_url', 'category', 'sub_category', 'color', 'product_name', 'attributes']]
    df.to_csv(os.path.join(data_path, category + '.csv'), index=False)

df = df[['img_path', 'img_url', 'category', 'sub_category', 'color', 'product_name', 'attributes']]
df.to_csv(os.path.join(data_path, category + '.csv'), index=False)



