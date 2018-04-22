# Fashion Data Scraper

This project scrapes fashion websites to download a dataset of fashion item pictures and their attributes (such as 
color, length, etc.) It downloads data from the following websites:

- www.aboutyou.de
- www.fashionid.de

It saves the product images in a folder structure by category and creates a csv file listing each image path, url, 
color, category and a list of attributes found on the website for that garment.
 
### data_scraper
In order to start scraping, run the following command:
```
python data_scraper/main.py --website aboutyou --categories kleider,tops --colors black,white
```

The following parameters are available when running the scraper:
```
python data_scraper/main.py [--website {aboutyou,fashionid}] [--data_path DATA_PATH]
               [--chromedriver_path CHROMEDRIVER_PATH]
               [--img_format IMG_FORMAT] [--img_width IMG_WIDTH]
               [--color_names COLOR_NAMES] [--categories CATEGORIES]
```

### data_processing
The jupyter notebooks can be used for data cleaning and sanity checks, and also as a template for abstracting 
relevant attributes into columns and/or one-hot vector format. There is also a notebook for post-processing of the 
image data, such as resizing and removing alpha channels.

## Requirements

- Setup Anaconda
- Setup conda environment
- Setup local env
- Download selenium chromedriver

### Setup Anaconda
To download Anaconda package manager, go to: <i>https://www.continuum.io/downloads</i>.

After installing locally the conda environment, proceed to setup this project environment.


### Setup local conda environment

For dependency management we are using conda-requirements.txt and requirements.txt. 
Please "cd" into the current repository and build your conda environment based on those conda-requirements and 
requirements:
 
```
conda create -n fashion_scraper python=3.6
source activate fashion_scraper
conda install --file conda_requirements.txt
pip install -r pip_requirements.txt
```


To deactivate this specific virtual environment:
```
source deactivate
```

If you need to completely remove this conda env, you can use the following command:

```
conda env remove --name fashion_scraper
```

### Download Selenium Chromedriver
To download Selenium Chromedriver, use the the following link: 
<i>https://sites.google.com/a/chromium.org/chromedriver/downloads</i>

You need to specify the path to your chromedriver when using the scraper classes.