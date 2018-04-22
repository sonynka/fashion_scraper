import requests
import pandas as pd
import time
import os
from abc import ABCMeta, abstractmethod


class Scraper(object, metaclass=ABCMeta):
    """
    Scrapes a website for images of fashion items with their attributes such as category, color etc.
    Saves the images in the given folder data path and a csv file describing each image's desscription.
    """
    @property
    def url(self):
        raise NotImplementedError

    @property
    def url_clothes(self):
        raise NotImplementedError

    @property
    def url_category_color(self):
        raise NotImplementedError

    def __init__(self,
                 data_path,
                 img_width,
                 colors,
                 categories):
        """
        :param data_path: path where to save the scraped data
        :param colors: dictionary with color names and their codes for website filtering
        :param categories: list of categories to scrape
        :param img_width: width of the image to be downloaded
        """

        self.data_path = data_path
        self.data_csv = os.path.join(self.data_path, 'data.csv')

        self.colors = colors
        self.categories = categories

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

            max_page = self.get_number_of_pages(category, self.colors[color])
            print('Color {}: {} pages'.format(color, max_page))
            print('-' * 50)

            for page in range(1, max_page+1):
                print('Downloading page: ', page)

                try:
                    self.download_page(category, color, page)
                except Exception as e:
                    print('Download of page #{} failed'.format(page), e)

    @abstractmethod
    def get_number_of_pages(self, category, color_code):
        """
        For the given category and color, get the maximum amount of pages available from the pagination wrapper
        :param category: name of the category
        :param color_code: code of color as in url
        :return: number of the last product page for that category and color
        """
        raise NotImplementedError

    def download_page(self, category, color, page):
        """
        Download and save all product info and images from a given page
        :param category: category to download
        :param color: color name to download
        :param page: number of the page to download
        """

        category_color_link = self.url_category_color.format(category=category, color=self.colors[color])
        page_link = category_color_link + '&page={}'.format(page)

        # get the products list from the page
        products = self.download_products(page_link)

        # get information for each product
        for prod_idx, product in enumerate(products):
            try:
                name, img_id, img_link, details = self.get_product_info(product)

                # save product image
                img_path = os.path.join(category, img_id + '.jpg')
                img_filepath = os.path.join(self.data_path, img_path)
                self.save_product_image(img_link, img_filepath, img_width=self.image_width)

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

    @abstractmethod
    def get_product_info(self, product):
        """
        Get all the information of the product, such as description, name and url to the image.
        :param product: html object from the product_soup
        :return: name of the product, unique image ID, url to the image, list of image tags
        """
        raise NotImplementedError

    def save_product_image(self, img_link, img_filepath, img_width):
        """
        Save the given image from the url to the given image file path.
        :param img_link: URL of the image
        :param img_filepath: path where to save the image
        :param img_width: width size of the image
        """

        if not os.path.exists(img_filepath):
            img = self.get_response(img_link)
            if img.status_code == requests.codes.ok:
                with open(img_filepath, 'wb') as file:
                    file.write(img.content)
        else:
            print('Image file already exists: ', img_filepath)

    @abstractmethod
    def download_products(self, url):
        """
        Download all the product html from the category page
        :param url: URL to the category website
        :return: HTML for all the products on the website
        """
        raise NotImplementedError

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

    @staticmethod
    def validate_colors(color_names, allowed_colors):
        if not isinstance(color_names, list):
            raise ValueError('Color names must be a list')

        if not set(color_names).issubset(set(allowed_colors)):
            raise ValueError('Invalid color names. Allowed colors are: {}'.format(allowed_colors))

    @staticmethod
    def validate_categories(category_list, allowed_categories):
        if not isinstance(category_list, list):
            raise ValueError('Category names must be a list')

        if not set(category_list).issubset(set(allowed_categories)):
            raise ValueError('Invalid category names. Allowed categories are: {}'.format(allowed_categories))










