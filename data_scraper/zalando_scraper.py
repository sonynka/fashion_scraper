from scraper import Scraper
from bs4 import BeautifulSoup
from selenium import webdriver

class ZalandoScraper(Scraper):

    url = 'https://www.zalando.de'
    url_clothes = url + '/damenbekleidung'
    url_category_color = url_clothes + '-{category}/_{color}/?order=activation_date'
    url_page_extension = 'p'

    # list of colors and their codes on the aboutyou website
    COLORS = {'black': 'schwarz',
              'white': 'weiss',
              'red': 'rot',
              'blue': 'blau',
              'green': 'gruen.oliv',
              'yellow': 'gelb',
              'pink': 'lila.pink',
              'gray': 'grau',
              'beige': 'beige'
              }

    # list of clothes categories on the aboutyou website
    # special characters need to be replaced according to the url
    CATEGORIES = ['kleider', 'shirts', 'blusen-tuniken', 'pullover-und-strickjacken', 'jacken-maentel',
                  'roecke', 'hosen', 'jeans', 'hosen-overalls-jumpsuit', 'jacken']

    def __init__(self,
                 data_path,
                 chromedriver_path,
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

        super().validate_colors(color_names, self.COLORS.keys())
        super().validate_categories(categories, self.CATEGORIES)

        colors = {color_name: self.COLORS[color_name] for color_name in color_names}
        categories = categories

        options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        self.driver = webdriver.Chrome(chromedriver_path, chrome_options=options)

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
            pagination = category_soup.find('z-grid-item', class_='cat_paginationWrapper-2rUKy')
            max_page = int(pagination.find('div', class_='cat_label-2W3Y8').text.split(' ')[-1])
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
        product_brand = product_soup.find('h2').text.strip()
        product_name = product_soup.find('h1').text.strip()

        product_details = product_soup.find('div', id='z-pdp-detailsSection')

        product_attributes = []
        for detail_section in product_details.find_all('div', class_='h-container h-flex-no-shrink h-tabs__panel h-align-left'):
            for tag in detail_section.find_all('p'):
                product_attributes.append(tag.text.strip())

        # get product image
        product_img_thumbs = product_soup.find('div', id='z-pdp-topSection')
        product_img_thumbs = product_img_thumbs.find(
            'div', class_='h-container h-carousel h-carousel-thumbnail vertical h-align-left')

        img_links = []
        product_img_link = ''
        for img_thumb in product_img_thumbs.find_all('picture'):
            img_link = img_thumb.find('img')['src'].replace('thumb', 'zoom')
            if 'packshot' in img_link:
                product_img_link = img_link
            else:
                img_links.append(img_link)

        # product_img_link = 'https:' + product_img.split('"')[1].split('?')[0]
        product_img_id = product_img_link.split('/')[-1].split('@')[0]

        return {'name': product_name,
                'brand': product_brand,
                'id': product_img_id,
                'img_url': product_img_link,
                'model_img_urls': ', '.join(img_links),
                'attributes': ', '.join(product_attributes)}

    def download_products(self, url):
        """
        Download all the product html from the category page
        :param url: URL to the category website
        :return: HTML for all the products on the website
        """
        products = []

        try:
            self.driver.get(url)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            subcat_soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            color_products = subcat_soup.find('z-grid', class_='cat_articles')
            products = color_products.find_all('div', class_='cat_articleContain-1Z60A')

        except Exception as e:
            print('Problem with downloading products at {}:'.format(url), e)

        return products


