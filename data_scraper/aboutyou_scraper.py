from scraper import Scraper
from bs4 import BeautifulSoup
from selenium import webdriver


class AboutYouScraper(Scraper):
    """
    Scrapes the website www.aboutyou.de for images of fashion items with their attributes such as category, color etc.
    Saves the images in the given folder data path and a csv file describing each image's desscription.
    """

    url = 'https://www.aboutyou.de'
    url_clothes = url + '/frauen/bekleidung'
    url_category_color = url_clothes + '/{category}?sort=new&bi_color={color}'

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

        super().validate_colors(color_names, self.COLORS.keys())
        super().validate_categories(categories, self.CATEGORIES)

        colors = {color_name: self.COLORS[color_name] for color_name in color_names}
        categories = categories

        self.chromedriver_path = chromedriver_path

        super().__init__(data_path, img_format, img_width, colors, categories)

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
            pagination = category_soup.find('div', class_='paginationWrapper_1wdi4uz')
            max_page = int(pagination.find_all('li', class_='pageNumbers_ffrt32')[-1].text)
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

        product_img_link = product_img_link + '?width={}'.format(str(self.image_width))

        return product_name, product_img_id, product_img_link, product_attributes


    def download_products(self, url):
        """
        Download all the product html from the category page
        :param url: URL to the category website
        :return: HTML for all the products on the website
        """
        products = []

        # start driver to click on Produktansicht button
        driver = webdriver.Chrome(self.chromedriver_path)

        try:
            driver.get(url)
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

        except Exception as e:
            print('Problem with downloading products at {}:'.format(url), e)
            driver.close()

        return products


