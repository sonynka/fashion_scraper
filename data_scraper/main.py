import os
import argparse
from data_scraper.aboutyou_scraper import AboutYouScraper
from data_scraper.fashionid_scraper import FashionIdScraper

DATA_PATH = './data/'
CHROMEDRIVER_PATH = '../chromedriver/chromedriver'

IMAGE_FORMAT = '.jpg'
IMAGE_WIDTH = 400


def main(config):

    if not os.path.exists(config.data_path):
        os.makedirs(config.data_path)

    options = dict(data_path=config.data_path,
                   chromedriver_path=config.chromedriver_path,
                   img_format=config.img_format,
                   img_width=config.img_width)

    if config.color_names:
        options['color_names'] = config.color_names

    if config.categories:
        options['categories'] = config.categories

    scraper = None

    if config.website == 'aboutyou':
        scraper = AboutYouScraper(**options)
    elif config.website == 'fashionid':
        scraper = FashionIdScraper(**options)

    scraper.download_data()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--website', type=str, default='aboutyou', choices=['aboutyou', 'fashionid'],
                        help='which website to scrape')

    parser.add_argument('--data_path', type=str, default=DATA_PATH)
    parser.add_argument('--chromedriver_path', type=str, default=CHROMEDRIVER_PATH)
    parser.add_argument('--img_format', type=str, default=IMAGE_FORMAT)
    parser.add_argument('--img_width', type=str, default=IMAGE_WIDTH)

    # optional parameters, if not specified, the parser will take all the default colors and categories on the website
    parser.add_argument("--color_names", required=False, type=str,
                        help="comma separated list of color names, e.g.: black,white,red")
    parser.add_argument("--categories", required=False, type=str,
                        help="comma separated list of category names, e.g.: kleider,jumpsuits-und-overalls,tops "
                             "(special characters need to be replaced according to the url)")

    config = parser.parse_args()
    print(config)
    main(config)