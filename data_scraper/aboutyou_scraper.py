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
    url_sorting = 'sort=new'
    url_category_color = url_clothes + '/{category}?bi_color={color}&' + url_sorting
    url_page_extension = 'page'

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
                 img_width,
                 download_imgs,
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

        super().__init__(data_path, img_width, colors, categories, download_imgs)

    def get_number_of_pages(self, url):
        """
        For the given category and color, get the maximum amount of pages available from the pagination wrapper
        :param url: url to download the pages for
        :return: number of the last product page for that category and color
        """

        response = self.get_response(url)
        category_soup = BeautifulSoup(response.content, 'html.parser')

        try:
            pagination = category_soup.find('div', class_='styles__paginationWrapper--SrlgQ')
            max_page = int(pagination.find_all('li', class_='styles__pageNumbers--1Lsj_')[-1].text)
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
        product_brand = product.find('div', class_='styles__brandName--2XS22').text
        product_name = product.find('div', class_='styles__productName--2z0ZU').text

        product_page = self.get_response(product_link)
        product_soup = BeautifulSoup(product_page.content, 'html.parser')

        # get product details
        product_id = product_soup.find('li', class_='styles__articleNumber--1UszN').text.split(':')[-1].strip()
        product_details = product_soup.find('div', class_='col-sm-6 styles__detailsContainer--1ku-C')
        product_attributes = []
        for detail_section in product_details.find_all('div', class_='styles__accordionContainer--1dPP0'):
            for tag in detail_section.find_all('li'):
                product_attributes.append(tag.text.strip())

        # product images
        # main product image
        product_img_link = product.find('div', class_='styles__img--R5yfd styles__imgTrimmed--1j_b9')['style']
        product_img_link = 'https:' + product_img_link.split('(')[1].split('?')[0].replace('"', '')

        # model images
        product_img_thumbs = product_soup.find('div', class_='styles__images--wD0M5').find('div', class_='slider')
        product_img_thumbs = product_img_thumbs.find_all('div', class_='styles__img--R5yfd')

        img_links = []
        for img_thumb in product_img_thumbs:
            img_link = 'https:' + img_thumb['style'].split('(')[1].split('?')[0]
            img_links.append(img_link)
        img_links.remove(product_img_link)

        return {'name': product_name,
                'brand': product_brand,
                'id': product_id,
                'img_url': product_img_link,
                'product_url': product_link,
                'model_img_urls': ', '.join(img_links),
                'attributes': ', '.join(product_attributes)}


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
            # for categories that don't have any products for the given filter,
            # chrome opens a shortened url without the filter, therefore need
            #   to check if it is the correct one
            if driver.current_url == url:
                try:
                    product_view = \
                    '//*[@id="app"]/section/div[2]/div/div[2]/div/div/div[1]/div[2]/div/div[2]/div[1]/div/span[2]'
                    driver.find_element_by_xpath(product_view).click()
                except:
                    product_view = \
                    '//*[@id="app"]/section/div[1]/div/div[2]/div/div/div[1]/div[2]/div/div[2]/div[1]/div/span[2]'
                    driver.find_element_by_xpath(product_view).click()

                # download Produktansicht page and close driver
                subcat_soup = BeautifulSoup(driver.page_source, 'html.parser')
                driver.close()

                # avoid taking 'Weitere Produkte' section, which are products that don't match the filter
                color_products = subcat_soup.find('div', class_='styles__container--1bqmB')
                products = color_products.find_all('div', class_='styles__tile--2s8XN col-sm-6 col-md-4 col-lg-4')
            else:
                driver.close()
                print('No products found')

        except Exception as e:
            print('Problem with downloading products at {}:'.format(url), e)
            driver.close()

        return products


