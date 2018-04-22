from scraper import Scraper
from bs4 import BeautifulSoup


class FashionIdScraper(Scraper):
    """
    Scrapes the website www.fashionid.de for images of fashion items with their attributes such as category, color etc.
    Saves the images in the given folder data path and a csv file describing each image's desscription.
    """

    url = 'https://www.fashionid.de'
    url_clothes = url + '/damen'
    url_category_color = url_clothes + '/{category}/farbe-{color}/?sortby=newness'

    # list of colors and their codes on the website
    COLORS = {'black': 'grau-schwarz',
              'white': 'weiss',
              'red': 'rot',
              'blue': 'blau-turkis',
              'green': 'grun',
              'yellow': 'gelb',
              'pink': 'rose',
              'beige': 'braun'
              }

    # list of clothes categories on the website
    # special characters need to be replaced according to the url
    CATEGORIES = ['kleider', 'pullover-strick', 'jeans', 'jacken', 'blusen',
                  'roecke', 'shirts', 'hosen', 'jumpsuits', 'shorts-bermudas']

    def __init__(self,
                 data_path,
                 img_width,
                 color_names=list(COLORS.keys()),
                 categories=CATEGORIES):
        """
        :param data_path: path where to save the scraped data
        :param color_names: list of color names to scrape (optional)
        :param categories: list of categories to scrape (optional)
        :param img_format: format in which scraped images should be saved
        """

        super().validate_colors(color_names, self.COLORS.keys())
        super().validate_categories(categories, self.CATEGORIES)

        colors = {color_name: self.COLORS[color_name] for color_name in color_names}
        categories = categories

        super().__init__(data_path, img_width, colors, categories)

    def get_number_of_pages(self, category, color_code):
        """
        For the given category and color, get the maximum amount of pages available from the pagination wrapper
        :param category: name of the category
        :param color_code: code of color as in url
        :return: number of the last product page for that category and color
        """

        category_color_link = self.url_category_color.format(category=category, color=color_code)

        response = self.get_response(category_color_link)
        category_soup = BeautifulSoup(response.content, 'html.parser')

        try:
            pagination = category_soup.find('ul', class_='pagination')
            max_page = int(pagination.find_all('a', class_='js-togglePage')[-2].text)
        except:
            max_page = 1

        return max_page

    def get_product_info(self, product):
        """
        Get all the information of the product, such as description, name and url to the image.
        :param product: html object from the product_soup
        :return: name of the product, unique image ID, url to the image, image tags
        """

        product_link = self.url + product.a['href']
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
        product_img_link = product_img_link.split('.jpg')[0] + ',{}.jpg'.format(self.image_width)

        product_img_id = product_img_src.split('_')[-1].split(',')[0]

        return product_name, product_img_id, product_img_link, product_attributes

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




