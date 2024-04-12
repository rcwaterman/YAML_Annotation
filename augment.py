"""
As it currently stands, all images will be loaded into the "original_images" folder of the data directory. 
The image directory will need to be augmented and split amongst the train, test, and valid folders. 

Critical features for this process:
    1. Randomly split the images in the "images" folder between the test, train, and valid folders. 
        - Keep the original images and bounding boxes in the original_images and labels folders, respectively
        - Generate n number of augmented images in a temp folder based on the original images
            - Naming convention: {image name}_{n}.jpg
        - Randomly split the augmented images between the train, valid, and test folders (70/20/10 ratio, respectively)
    2. Augmentation via the following methods:
        - Random rotate
        - Random crop 
        - Random blur
        - Random horizontal flip
        - Random vertical flip
    3. Using the albumentations library, the yolo annotated bounding boxes can be drawn into the augmented image.
"""

import albumentations as A
import os
from tkinter import filedialog

data_dir = filedialog.askdirectory()


