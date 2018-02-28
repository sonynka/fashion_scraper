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


class Scraper():

    DATA_PATH = '/Users/sonynka/HTW/IC/data/aboutyou/'
    CHROMEDRIVER_PATH = '../chromedriver/chromedriver'

    URL = 'https://www.aboutyou.de'
    URL_CLOTHES = URL + '/frauen/bekleidung'

    COLORS = {'black': 38932,
              'white': 38935,
              'red': 38931,
              'blue': 38920,
              'green': 38926,
              'yellow': 38923,
              'pink': 38930,
              'gray': 38925,
              'beige': 38919
              }

    CATEGORIES = ['ponchos & kimonos','kleider', 'pullover']
    IMAGE_FORMAT = '.jpg'

    def __init__(self,
                 data_path=DATA_PATH,
                 chromedriver_path=CHROMEDRIVER_PATH,
                 color_names=list(COLORS.keys()),
                 categories=CATEGORIES,
                 img_format=IMAGE_FORMAT):

        self.data_path = data_path
        self.chromedriver_path = chromedriver_path

        self.colors = {color_name: self.COLORS[color_name] for color_name in color_names}
        self.categories = categories

        self.df_product_info = pd.DataFrame(columns=['img_path', 'img_url', 'category', 'subcategory',
                                                     'color', 'product_name', 'attributes'])
        self.image_format = img_format


    def download_data(self):

        for category in self.categories:
            try:
                self.download_category(category)
            except Exception as e:
                print('Problem with download of category: {}'.format(category), e)

    def download_category(self, category):

        print('\nDownloading category: {}'.format(category))
        print(50 * '#')

        subcategories = self.get_subcategories(category)

        for subcategory, subcategory_link in subcategories.items():

            print('Downloading sub-category: {}'.format(subcategory))
            print(50 * '-')

            try:
                self.download_subcategory(category, subcategory, subcategory_link)
            except Exception as e:
                print('Problem with download of subcategory: {}'.format(subcategory), e)

    def download_subcategory(self, category, subcategory, subcategory_link):

        subcategory_data_path = os.path.join(os.path.join(self.data_path, category), subcategory)
        if not os.path.exists(subcategory_data_path):
            os.makedirs(subcategory_data_path)

        for color_name, color_code in self.colors.items():

            subcategory_color_link = subcategory_link + '?bi_color={}'.format(color_code)

            products = self.download_subcategory_products(subcategory_color_link)
            print('Color {}: {} products'.format(color_name, len(products)))

            for product in products:
                name, img_id, img_link, details = self.get_product_info(product)

                # save product image
                img_filepath = os.path.join(subcategory_data_path, img_id + self.image_format)
                self.save_product_image(img_link, img_filepath, width=400)

                # save product to dataframe
                product_dict = {'img_path': img_filepath,
                                'img_url': img_link,
                                'category': category,
                                'subcategory': subcategory,
                                'color': color_name,
                                'product_name': name,
                                'attributes': ','.join(details)}

                self.df_product_info = self.df_product_info.append(product_dict, ignore_index=True)

        # save csv
        csv_file = os.path.join(self.data_path, category + '.csv')
        self.df_product_info.to_csv(csv_file, index=False, encoding='latin1', sep=';')
        print('Writing sub-category data to: {}'.format(csv_file))

    def get_product_info(self, product):

        product_link = self.URL + product.a['href']
        product_page = requests.get(product_link)
        product_soup = BeautifulSoup(product_page.content, 'html.parser')

        # get product details
        product_name = product_soup.find('h1', class_='productName_192josg').text
        product_details = product_soup.find('div', class_='wrapper_1w5lv0w')
        product_attributes = []
        for detail_section in product_details.find_all('div', class_='container_iv4rb4'):
            for tag in detail_section.find_all('li'):
                product_attributes.append(tag.text.strip())

        # get product image
        product_img = product.find('div', class_='img_162hfdi-o_O-imgTrimmed_16d3go2')['style']
        product_img_link = 'https:' + product_img.split('"')[1].split('?')[0]
        product_img_id = product_img_link.split('/')[-1]

        return product_name, product_img_id, product_img_link, product_attributes

    def save_product_image(self, img_link, img_filepath, width=400):

        if not os.path.exists(img_filepath):
            img_link = img_link + '?width={}'.format(str(width))
            img = requests.get(img_link)
            if img.status_code == requests.codes.ok:
                with open(img_filepath, 'wb') as file:
                    file.write(img.content)
        else:
            print('Image file already exists')

    def download_subcategory_products(self, subcategory_link):

        # start driver to click on Produktansicht button
        driver = webdriver.Chrome(self.chromedriver_path)
        driver.get(subcategory_link)

        products = []

        # for categories that don't have any products for the given filter, chrome opens a shortened url without
        # the filter
        if driver.current_url == subcategory_link:
            driver.find_element_by_class_name('button_6u2hqh').click()

            # download Produktansicht page and close driver
            subcat_soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.close()

            # avoid taking 'Weitere Produkte' section, which are products that don't match the filter
            color_products = subcat_soup.find('div', class_='wrapper_8yay2a')
            products = color_products.find_all('div', class_='categoryTileWrapper_e296pg')
        else:
            driver.close()
            print('No products found')

        return products



    def get_subcategories(self, category):

        category_url_name = category
        if ' ' in category_url_name:
            category_url_name = category_url_name.replace(' ', '')
        if '&' in category_url_name:
            category_url_name = category_url_name.replace('&','-und-')

        url_category = self.URL_CLOTHES + '/' + category_url_name
        response = requests.get(url_category)

        category_soup = BeautifulSoup(response.content, 'html.parser')

        # find sub-categories of category
        category_list = category_soup.find('li', title=category.title()).parent
        sub_categories = {}
        for sub_category in category_list.find_all('a'):
            name = sub_category.text.lower()
            link = self.URL + sub_category['href']
            sub_categories[name] = link

        # if no subcategories exists, take the category as subcategory
        if len(sub_categories) == 0:
            sub_categories[category] = url_category

        print('Found {} subcategories for {}'.format(len(sub_categories), category))
        return sub_categories


    @staticmethod
    def get_response(url):
        response = requests.get(url)
        try:
            return response.content
        except ValueError:
            print("Problem downloading response content for: {} Response Code: {}".format(url, response.status_code))




def main():
    scraper = Scraper(color_names=['yellow'])
    scraper.download_data()


if __name__ == '__main__':
    main()








