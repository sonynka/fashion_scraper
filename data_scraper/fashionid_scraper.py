import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from selenium import webdriver


class FashionIdScraper():
    """
    Scrapes the website www.aboutyou.de for images of fashion items with their attributes such as category, color etc.
    Saves the images in the given folder data path and a csv file describing each image's desscription.
    """

    DATA_PATH = './data/'

    URL = 'https://www.fashionid.de'
    URL_CLOTHES = URL + '/damen'

    # list of colors and their codes on the aboutyou website
    COLORS = {'black': 'grau-schwarz',
              'white': 'weiss',
              'red': 'rot',
              'blue': 'blau-turkis',
              'green': 'grun',
              'yellow': 'gelb',
              'pink': 'rose',
              'beige': 'braun'
              }

    # list of clothes categories on the aboutyou website
    # special characters need to be replaced according to the url
    CATEGORIES = ['kleider', 'pullover-strick', 'jeans', 'jacken', 'blusen',
                  'roecke', 'shirts', 'hosen', 'jumpsuits', 'shorts-bermudas']


    def __init__(self,
                 data_path,
                 chromedriver_path,
                 img_format,
                 img_width,
                 color_names=list(COLORS.keys()),
                 categories=CATEGORIES):
        """
        :param data_path: path where to save the scraped data
        :param chromedriver_path: path to chromedriver
        :param color_names: list of color names to scrape (optional)
        :param categories: list of categories to scrape (optional)
        :param img_format: format in which scraped images should be saved
        """

        self.validate_colors(color_names)
        self.validate_categories(categories)

        self.data_path = data_path
        self.data_csv = os.path.join(self.data_path, 'data.csv')

        self.colors = {color_name: self.COLORS[color_name] for color_name in color_names}
        self.categories = categories

        # dataframe to hold all images information
        self.image_format = img_format
        self.image_width = img_width

    def download_data(self):
        """
        Download all data and save the description in data.csv. The flow is the following:
        -> for each category:
            -> for each color: get number of pages
                ->for each page: download all products and save their images and descriptions
        """

        for category in self.categories:
            try:
                self.download_category(category)
            except Exception as e:
                print('Problem with download of category: {}'.format(category), e)


    def download_category(self, category):
        """
        Download all products from all colors for the given category
        :param category: category to download
        """

        print('\nDownloading category: {}'.format(category))
        print(50 * '#')

        category_data_path = os.path.join(self.data_path, category)
        if not os.path.exists(category_data_path):
            os.makedirs(category_data_path)

        for color in self.colors:

            color_df = pd.DataFrame()

            max_page = self.get_number_of_pages(category, self.colors[color])
            print('Color {}: {} pages'.format(color, max_page))
            print('-' * 50)

            for page in range(1, max_page + 1):
                print('Downloading page: ', page)

                try:
                    page_df = self.download_page(category, color, page)
                    color_df.append(page_df)
                except Exception as e:
                    print('Download of page #{} failed'.format(page), e)


    def get_number_of_pages(self, category, color_code):
        """
        For the given category and color, get the maximum amount of pages available from the pagination wrapper
        :param category: name of the category
        :param color_code: code of color as in url
        :return: number of the last product page for that category and color
        """

        category_color_link = '{url}/{category}/farbe-{color}/?sortby=newness'.format(
            url=self.URL_CLOTHES, category=category, color=color_code)

        response = self.get_response(category_color_link)
        category_soup = BeautifulSoup(response.content, 'html.parser')

        try:
            pagination = category_soup.find('ul', class_='pagination')
            max_page = int(pagination.find_all('a', class_='js-togglePage')[-2].text)
        except:
            max_page = 1

        return max_page

    def download_page(self, category, color, page):
        """
        Download and save all product info and images from a given page
        :param category: category to download
        :param color: color name to download
        :param page: number of the page to download
        """

        page_link = '{url}/{category}/farbe-{color}/?sortby=newness&page={page}'.format(
            url=self.URL_CLOTHES, category=category, color=self.colors[color], page=page)

        # get the products list from the page
        products = self.download_products(page_link)

        # get information for each product
        for prod_idx, product in enumerate(products):
            try:
                name, img_id, img_link, details = self.get_product_info(product)

                # save product image
                img_path = os.path.join(category, img_id + self.image_format)
                img_filepath = os.path.join(self.data_path, img_path)
                self.save_product_image(img_link, img_filepath, width=self.image_width)

                # save product to dataframe
                product_dict = {'img_path': img_path,
                                'img_url': img_link,
                                'category': category,
                                'color': color,
                                'product_name': name,
                                'attributes': ','.join(details)}

                self.append_csv_file(csv_file=self.data_csv, df=product_dict)
            except Exception as e:
                print('Problem with downloading product: ', e)

            # sleeep 2 seconds after each product
            time.sleep(2)

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
        product_name = product_soup.find('h1').text
        product_details = product_soup.find('ul', class_='list-column qa-description-bullet-points-list').find_all('li')
        product_attributes = []
        for detail in product_details:
            product_attributes.append(detail.text.strip())


        # get product image
        product_gallery = product_soup.find('div', class_='product-gallery col-xs-6')
        product_img_src = product_gallery.find_all('li')[0].img['src']
        product_img_link = 'https:' + ','.join(product_img_src.split(',')[:-1]) + '.jpg'
        product_img_id = product_img_src.split('_')[-1].split(',')[0]

        return product_name, product_img_id, product_img_link, product_attributes

    def save_product_image(self, img_link, img_filepath, width=400):
        """
        Save the given image from the url to the given image file path.
        :param img_link: URL of the image
        :param img_filepath: path where to save the image
        :param width: (optional) width size of the image
        """

        if not os.path.exists(img_filepath):
            img_link = img_link.split('.jpg')[0] + ',{}.jpg'.format(width)
            img = self.get_response(img_link)
            if img.status_code == requests.codes.ok:
                with open(img_filepath, 'wb') as file:
                    file.write(img.content)
        else:
            print('Image file already exists: ', img_filepath)

    def download_products(self, url):
        """
        Download all the product html from the category page
        :param url: URL to the category website
        :return: HTML for all the products on the website
        """

        products_page = self.get_response(url)
        products_soup = BeautifulSoup(products_page.content, 'html.parser')

        products_wrapper = products_soup.find('div', class_='prvWrapper qa-prv-wrapper')
        products = products_wrapper.find_all('div', class_='product-item qa-product-item')

        return products

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
                df_to_save = pd.read_csv(csv_file, sep=';', encoding='utf-8')

            df_to_save = df_to_save.append(df, ignore_index=True)
            df_to_save = df_to_save.drop_duplicates()
            df_to_save.to_csv(csv_file, index=False, sep=';', encoding='utf-8')
        except Exception as e:
            print('Problem with writing dataframe to csv: {}'.format(csv_file), e)

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

    def validate_colors(self, color_names):
        if not isinstance(color_names, list):
            raise ValueError('Color names must be a list')

        if not set(color_names).issubset(set(self.COLORS.keys())):
            raise ValueError('Invalid color names. Allowed colors are: {}'.format(self.COLORS.keys()))

    def validate_categories(self, categories):
        if not isinstance(categories, list):
            raise ValueError('Category names must be a list')

        if not set(categories).issubset(set(self.CATEGORIES)):
            raise ValueError('Invalid category names. Allowed categories are: {}'.format(self.CATEGORIES))





