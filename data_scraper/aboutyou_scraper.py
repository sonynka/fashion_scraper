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


class AboutYouScraper():
    """
    Scrapes the website www.aboutyou.de for images of fashion items with their attributes such as category, color etc.
    Saves the images in the given folder data path and a csv file describing each image's desscription.
    """

    DATA_PATH = './data/'
    CHROMEDRIVER_PATH = '../chromedriver/chromedriver'

    URL = 'https://www.aboutyou.de'
    URL_CLOTHES = URL + '/frauen/bekleidung'

    # list of colors and their codes on the aboutyou website
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

    # list of clothes categories on the aboutyou website
    CATEGORIES = ['kleider', 'strick', 'jeans', 'jacken', 'blusen & tuniken',
                  'röcke', 'shirts', 'hosen', 'jumpsuits & overalls', 'tops']

    IMAGE_FORMAT = '.jpg'

    def __init__(self,
                 data_path=DATA_PATH,
                 chromedriver_path=CHROMEDRIVER_PATH,
                 color_names=list(COLORS.keys()),
                 categories=CATEGORIES,
                 img_format=IMAGE_FORMAT):
        """
        :param data_path: path where to save the scraped data
        :param chromedriver_path: path to chromedriver
        :param color_names: list of color names to scrape (optional)
        :param categories: list of categories to scrape (optional)
        :param img_format: format in which scraped images should be saved
        """

        self.data_path = data_path
        self.chromedriver_path = chromedriver_path

        self.colors = {color_name: self.COLORS[color_name] for color_name in color_names}
        self.categories = categories

        # dataframe to hold all images information
        self.df_product_info = pd.DataFrame(columns=['img_path', 'img_url', 'category', 'subcategory',
                                                     'color', 'product_name', 'attributes'])
        self.image_format = img_format

    def download_data(self):
        """
        Download all data and save the description in data.csv. The flow is the following:
        -> for each category: get all subcategories links from the menu
            -> for each subcategory:
                -> for each color: download all products and save their images and descriptions
        """

        for category in self.categories:
            try:
                self.download_category(category)
            except Exception as e:
                print('Problem with download of category: {}'.format(category), e)

        # save all data csv
        csv_file = self.data_path + 'data.csv'
        self.append_csv_file(csv_file, self.df_product_info)

    def download_category(self, category):
        """
        Download all category's data. Write it to a {category}.csv.
        """

        print('\nDownloading category: {}'.format(category))
        print(50 * '#')

        subcategories = self.get_subcategories(category)

        for subcategory, subcategory_link in subcategories.items():

            print(50 * '-')
            print('Downloading sub-category: {}'.format(subcategory))

            try:
                self.download_subcategory(category, subcategory, subcategory_link)
            except Exception as e:
                print('Problem with download of subcategory: {}'.format(subcategory), e)

        # save csv to category file (only select rows with category, since df is accumulating all data)
        csv_file = os.path.join(self.data_path, category + '.csv')
        print('Writing category data to: {}'.format(csv_file))
        df_category = self.df_product_info[self.df_product_info.category == category]
        self.append_csv_file(csv_file, df_category)

    def download_subcategory(self, category, subcategory, subcategory_link):
        """
        For all colors, download the subcategory's products, save the images and store the data in the dataframe.
        :param category: category
        :param subcategory: subcategory of the category
        :param subcategory_link: url for the subcategory webpage
        :return:
        """

        # where to save the subcategory images
        subcategory_data_path = os.path.join(os.path.join(self.data_path, category), subcategory)
        if os.path.exists(subcategory_data_path):
            print('Subcategory already downloaded')
            return
        else:
            os.makedirs(subcategory_data_path)

        # download all colors
        for color_name, color_code in self.colors.items():

            subcategory_color_link = subcategory_link + '?bi_color={}'.format(color_code)

            # get the products list from the subcategory page
            products = self.download_subcategory_products(subcategory_color_link)
            print('Color {}: {} products'.format(color_name, len(products)))

            # get information for each product
            for prod_idx, product in enumerate(products):
                try:
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
                except Exception as e:
                    print('Problem with downloading product: ', e)

                # sleeep 2 seconds after each product
                time.sleep(2)
                self.print_progress_bar(prod_idx + 1, len(products), length=50)

            # save csv to category file (only select rows with category, since df is accumulating all data)
            csv_file = os.path.join(os.path.join(self.data_path, category), subcategory + '.csv')
            df_subcategory = self.df_product_info[self.df_product_info.subcategory == subcategory]
            self.append_csv_file(csv_file, df_subcategory)

    def get_product_info(self, product):
        """
        Get all the information of the product, such as description, name and url to the image.
        :param product: html object from the product_soup
        :return: name of the product, unique image ID, url to the image, image tags
        """

        product_link = self.URL + product.a['href']
        product_page = self.get_response(product_link)
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
        """
        Save the given image from the url to the given image file path.
        :param img_link: URL of the image
        :param img_filepath: path where to save the image
        :param width: (optional) width size of the image
        """

        if not os.path.exists(img_filepath):
            img_link = img_link + '?width={}'.format(str(width))
            img = self.get_response(img_link)
            if img.status_code == requests.codes.ok:
                with open(img_filepath, 'wb') as file:
                    file.write(img.content)
        else:
            print('Image file already exists: ', img_filepath)

    def download_subcategory_products(self, subcategory_link):
        """
        Download all the product html from the subcategory page
        :param subcategory_link: URL to the subcategory website
        :return: HTML for all the products on the website
        """

        # start driver to click on Produktansicht button
        driver = webdriver.Chrome(self.chromedriver_path)
        driver.get(subcategory_link)

        products = []

        # for categories that don't have any products for the given filter, chrome opens a shortened url without
        # the filter, therefore need to check if it is the correct one
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
        """
        For the given category, get all the names and URLs of all the subcategories in the left menu.
        :param category: Category for which to get subcategories
        :return: dictionary with subcategory names and URLs
        """

        category_url_name = category
        if ' ' in category_url_name:
            category_url_name = category_url_name.replace(' ', '')
        if '&' in category_url_name:
            category_url_name = category_url_name.replace('&','-und-')

        url_category = self.URL_CLOTHES + '/' + category_url_name
        response = self.get_response(url_category)

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

    def append_csv_file(self, csv_file, df):
        """
        Write csv file with the scraped data. If such CSV file already exists, append the existing one with new data
        and delete duplicates.
        :param csv_file: Path of the csv file
        :param df: Dataframe to append/write
        """
        try:
            df_to_save = pd.DataFrame()

            if os.path.exists(csv_file):
                df_to_save = pd.read_csv(csv_file, sep=';')

            df_to_save = df_to_save.append(df)
            df_to_save = df_to_save.drop_duplicates()
            df_to_save.to_csv(csv_file, index=False, sep=';')
        except Exception as e:
            print('Problem with writing category dataframe to csv: {}'.format(csv_file), e)

    @staticmethod
    def print_progress_bar(iteration, total, prefix='', suffix='', length=100, fill='█'):
        """
        Print the progress bar in the console.
        """
        percent = ("{0:.0f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print('\r{} |{}| {}% {}'.format(prefix, bar, percent, suffix), end='')

        if iteration == total:
            print()

    @staticmethod
    def get_response(url):
        """
        Get response for an URL and evaluate the status code.
        """
        response = requests.get(url, timeout=10)
        try:
            return response
        except ValueError:
            print("Problem downloading response content for: {} Response Code: {}".format(url, response.status_code))


def main():
    scraper = AboutYouScraper(categories=['strick', 'jeans'], data_path='/Users/sonynka/HTW/IC/data/aboutyou/')
    scraper.download_data()


if __name__ == '__main__':
    main()








