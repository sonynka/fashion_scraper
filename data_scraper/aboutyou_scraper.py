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

    URL = 'https://aboutyou.de'
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

    CATEGORIES = ['Kleider']
    IMAGE_FORMAT = '.jpg'

    def __init__(self,
                 data_path=DATA_PATH,
                 chromedriver_path=CHROMEDRIVER_PATH,
                 color_names=COLORS.keys(),
                 categories=CATEGORIES,
                 img_format=IMAGE_FORMAT):

        self.data_path = data_path
        self.chromedriver_path = chromedriver_path

        self.colors = {color_name: self.COLORS[color_name] for color_name in color_names}
        self.categories = categories

        self.df_product_info = pd.DataFrame()
        self.image_format = img_format


    def download_data(self):

        for category in self.categories:
            self.download_category(category)

    def download_category(self, category):

        category_data_path = os.path.join(self.data_path, category)
        if not os.path.exists(category_data_path):
            os.makedirs(category_data_path)

        category_url = self.URL_CLOTHES + '/' + category

        print('\nDownloading category: {} to {}'.format(category, category_data_path))
        print(50 * '-')

        subcategories = self.get_subcategories(category)

        for subcat_idx, subcategory in enumerate(subcategories):

            print('Downloading sub-category [{:02}/{:02}]: {}'.format(subcat_idx, len(subcategories), subcategory))
            subcategory_link = category_url + '/' + subcategory

            for color_name, color_code in self.colors.items():

                subcategory_color_link = subcategory_link + '?bi_color={}'.format(color_code)
                products = self.download_subcategory_products(subcategory_color_link)
                print('Color {}: {} products'.format(color_name, len(products)))

                for product in products:
                    name, img_id, img_link, details = self.get_product_info(product)

                    # save product image
                    img_filepath = os.path.join(category_data_path, img_id + self.image_format)
                    self.save_product_image(img_link, img_filepath, width=400)

                    # save product to dataframe
                    product_dict = {'img_path': img_filepath,
                                    'img_url': img_link,
                                    'category': category,
                                    'subcategory': subcategory,
                                    'color': color_name,
                                    'product_name': name,
                                    'attributes': details}

                    self.df_product_info = self.df_product_info.append(product_dict, ignore_index=True)

            # save csv after each subcategory
            self.df_product_info = self.df_product_info[['img_path', 'img_url', 'category', 'subcategory', 'color', 'product_name', 'attributes']]
            csv_file = os.path.join(self.data_path, category + '.csv')
            self.df_product_info.to_csv(csv_file, index=False)
            print('Writing sub-category data to: {}'.format(csv_file))


    def get_product_info(self, product):

        product_link = self.URL + product.a['href']
        product_page = requests.get(product_link)
        product_soup = BeautifulSoup(product_page.content, 'html.parser')

        # get product details
        product_name = product_soup.find('h1', class_='productName_192josg').text
        product_details = product_soup.find('div', class_='wrapper_1w5lv0w')
        tags = []
        for detail_section in product_details.find_all('div', class_='container_iv4rb4'):
            for tag in detail_section.find_all('li'):
                tags.append(tag.text.strip())

        # get product image
        product_img = product.find('div', class_='img_162hfdi-o_O-imgTrimmed_16d3go2')['style']
        product_img_link = 'https:' + product_img.split('"')[1].split('?')[0]
        product_img_id = product_img_link.split('/')[-1]

        return product_name, product_img_id, product_img_link, product_details

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
        driver.find_element_by_class_name('button_6u2hqh').click()

        # download Produktansicht page and close driver
        subcat_soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.close()

        # avoid taking 'Weitere Produkte' section, which are products that don't match the filter
        color_products = subcat_soup.find('div', class_='wrapper_8yay2a')
        products = color_products.find_all('div', class_='categoryTileWrapper_e296pg')

        return products


    def get_subcategories(self, category):
        url_category = self.URL_CLOTHES + '/' + category
        response = requests.get(url_category)

        category_soup = BeautifulSoup(response.content, 'html.parser')

        # find sub-categories of category
        category_list = category_soup.find('li', title=category).parent
        sub_categories = []
        for sub_category in category_list.find_all('a'):
            sub_categories.append(sub_category.text)

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
    scraper = Scraper()
    scraper.download_data()


if __name__ == '__main__':
    main()








