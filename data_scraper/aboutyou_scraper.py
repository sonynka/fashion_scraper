import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import sys
import cssutils
from selenium import webdriver

import logging
cssutils.log.setLevel(logging.CRITICAL)


# Print iterations progress
def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    """ Call in a loop to create terminal progress bar """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s ' % (prefix, bar, percent, suffix), end="")
    # Print New Line on Complete
    if iteration == total:
        print()

data_path = '/Users/sonynka/HTW/IC/data/aboutyou2/'
chromedriver_path = '../chromedriver/chromedriver'

url = 'https://aboutyou.de'
url_clothes = url + '/frauen/bekleidung'

colors = {'black':  38932,
          'white':  38935,
          'red':    38931,
          'blue':   38920,
          'green':  38926,
          'yellow': 38923,
          'pink':   38930,
          'gray':   38925,
          'beige':  38919
          }
categories = {'Kleider': ['Cocktailkleider', 'Abendkleider', 'Minikleider', 'Maxikleider', 'Midikleider'],
              'Hosen': ['Shorts', 'Stoffhosen', 'Leggings'],
              'Strick': ['Strickjacken', 'Feinstrickpullover', 'Grobstrickpullover', 'Boleros'],
              'Jumpsuits-und-Overalls': ['Lange-Jumpsuits', 'Kurze-Jumpsuits']}
# categories = {'Jumpsuits-und-Overalls': ['Lange-Jumpsuits', 'Kurze-Jumpsuits']}

for category, sub_categories in categories.items():

    print('\n')
    print('Downloading category: {}'.format(category))
    print(50 * '-')

    df = pd.DataFrame()

    url_category = url_clothes + '/' + category
    data_path_category = os.path.join(data_path, category)
    if not os.path.exists(data_path_category):
        os.makedirs(data_path_category)

    for sub_category_idx, sub_category in enumerate(sub_categories):
        print('Downloading sub-category [{}/{}]: {}'.format(str(sub_category_idx), str(len(sub_categories)), sub_category))
        sub_category_url = url_category + '/' + sub_category

        for color, color_code in colors.items():
            sub_category_color_url = sub_category_url + '?bi_color={}'.format(color_code)

            driver = webdriver.Chrome(chromedriver_path)
            driver.get(sub_category_color_url)
            driver.find_element_by_class_name('button_6u2hqh').click()

            sub_cat_soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.close()

            # avoid taking 'Weitere Produkte' section, which are products that don't match the filter
            color_products = sub_cat_soup.find('div', class_='wrapper_8yay2a')
            products = color_products.find_all('div', class_='categoryTileWrapper_e296pg')

            l = len(products)
            print_progress_bar(0, l, prefix=color + ':', length=50)
            unsaved_products = []

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
                        for tag in detail_section.find_all('li'):
                            tags.append(tag.text.strip())

                    product_img = product.find('div', class_='img_162hfdi-o_O-imgTrimmed_16d3go2')['style']
                    product_img_link = 'https:' + product_img.split('"')[1].split('?')[0] + '?width=400'

                    img_name = product_img.split('"')[1].split('?')[0]
                    img_file_name = '{}_{}_{}.jpg'.format(sub_category, color, img_name)
                    img_file_path = os.path.join(data_path_category, img_file_name)

                    img = requests.get(product_img_link)
                    if img.status_code == requests.codes.ok:
                        with open(img_file_path, 'wb') as file:
                            file.write(img.content)

                    df = df.append({'img_path': os.path.join(category, img_file_name),
                                    'img_url': product_img_link,
                                    'category': category,
                                    'sub_category': sub_category,
                                    'color': color,
                                    'product_name': product_name,
                                    'attributes': tags}, ignore_index=True)

                    print_progress_bar(idx + 1, l, prefix=color + ':', suffix='Complete', length=50)

                except Exception as e:
                    # remember indexes that were not downloaded to be printed after progress bar is over
                    unsaved_products.append({idx: e})

            if len(unsaved_products) > 0:
                print('Errors: ', unsaved_products)

        df = df[['img_path', 'img_url', 'category', 'sub_category', 'color', 'product_name', 'attributes']]
        csv_file = os.path.join(data_path, category + '.csv')
        df.to_csv(csv_file, index=False)
        print('Writing sub-category data to: {}'.format(csv_file))



