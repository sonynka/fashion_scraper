# Data Processing

The notebooks in this package can be used for processing of the scraped data.

#### data_cleaning
Cleans the downloaded data by checking that all images are included in the CSV file and vice versa.

#### data_merging_and_attributes_selection
- Merges data from the scraped website into one folder and one CSV file
- Selects attributes from the attributes list and translates them from German into English.
- Creates a dummy attribute file for training

#### image_processing
- Resizes all scraped images to a uniform size
- Removes alpha channels, if given

#### model_images
Downloads model images for each product, from URLs saved in the CSV file

### train_test_split
- Splits the images into a train, validation and test set
- Creates respective CSV files with list of images belonging to each split.