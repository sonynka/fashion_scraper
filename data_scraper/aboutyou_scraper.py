import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from selenium import webdriver


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
    # special characters need to be replaced according to the url
    CATEGORIES = ['kleider', 'strick', 'jeans', 'jacken', 'blusen-und-tuniken',
                  'roecke', 'shirts', 'hosen', 'jumpsuits-und-overalls', 'tops']

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
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        self.data_csv = os.path.join(self.data_path, 'data.csv')

        self.chromedriver_path = chromedriver_path

        self.colors = {color_name: self.COLORS[color_name] for color_name in color_names}
        self.categories = categories

        # dataframe to hold all images information
        self.image_format = img_format

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

            for page in range(1, max_page+1):
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

        category_color_link = '{}/{}?sort=new&bi_color={}'.format(self.URL_CLOTHES, category, color_code)

        response = self.get_response(category_color_link)
        category_soup = BeautifulSoup(response.content, 'html.parser')

        try:
            pagination = category_soup.find('div', class_='paginationWrapper_1wdi4uz')
            max_page = int(pagination.find_all('li', class_='pageNumbers_ffrt32')[-1].text)
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

        page_link = '{}/{}?sort=new&bi_color={}&page={}'.format(self.URL_CLOTHES, category, self.colors[color], page)

        # get the products list from the page
        products = self.download_products(page_link)

        # get information for each product
        for prod_idx, product in enumerate(products):
            try:
                name, img_id, img_link, details = self.get_product_info(product)

                # save product image
                img_path = os.path.join(category, img_id + self.image_format)
                img_filepath = os.path.join(self.data_path, img_path)
                self.save_product_image(img_link, img_filepath, width=400)

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

    def download_products(self, url):
        """
        Download all the product html from the category page
        :param url: URL to the category website
        :return: HTML for all the products on the website
        """

        # start driver to click on Produktansicht button
        driver = webdriver.Chrome(self.chromedriver_path)
        driver.get(url)

        products = []

        # for categories that don't have any products for the given filter, chrome opens a shortened url without
        # the filter, therefore need to check if it is the correct one
        if driver.current_url == url:
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


def main():
    scraper = AboutYouScraper(data_path='/Users/sonynka/HTW/IC/data/aboutyou_paging',
                              categories=['tops'])
    scraper.download_data()


if __name__ == '__main__':
    main()








