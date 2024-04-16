"""
As it currently stands, all images will be loaded into the "original_images" folder of the data directory. 
The image directory will need to be augmented and split amongst the train, test, and valid folders. 

Critical features for this process:
    1. Randomly split the images in the "images" folder between the images/test, images/train, and images/valid folders. 
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
import cv2
import random
from tkinter import filedialog

#Ask the user for the original data dir
original_data_dir = filedialog.askdirectory()

image_dir = os.path.join(original_data_dir, 'images')
label_dir = os.path.join(original_data_dir, 'labels')

#Load all of the image/label file names into arrays
#For now, the label array will be the limiting factor because annotation is incomplete.
label_files = [os.path.join(label_dir,label) for label in sorted(os.listdir(label_dir))]

#Save variables for the test, train, and validation image dirs
test_img_dir = os.path.join(os.path.dirname(original_data_dir), 'images/test')
train_img_dir = os.path.join(os.path.dirname(original_data_dir), 'images/train')
valid_img_dir = os.path.join(os.path.dirname(original_data_dir), 'images/valid')

#Save label dirs
test_lbl_dir = os.path.join(os.path.dirname(original_data_dir), 'labels/test')
train_lbl_dir = os.path.join(os.path.dirname(original_data_dir), 'labels/train')
valid_lbl_dir = os.path.join(os.path.dirname(original_data_dir), 'labels/valid')

#Crawls the list of labels and finds gaps, assuming the label names have a multi-digit numerical ending.
def find_missing():
    prev_num = 0
    for idx,file in enumerate(label_files):
        if int(file.split('.')[0][-2::]) - prev_num > 1 and idx>0:    
            print(label_files[idx-1], label_files[idx])
        prev_num = int(file.split('.')[0][-2::])

def loadAnnotations(index):
    #Clear the label list
    bboxes = []
    classes = []

    label_file = f'{os.path.join(label_dir, label_files[index].split('.')[0])}.txt'

    if os.path.exists(label_file):
        f = open(label_file, "r")
        for idx, line in enumerate(f):
            if idx+1 > len(bboxes):
                items = line.split()
                cls = int(items[0])
                center_x = float(items[1])
                center_y = float(items[2])
                width = float(items[3])
                height = float(items[4])

                bboxes.append([center_x, center_y, width, height])
                classes.append(cls)
    else:
        bboxes = []
        classes = []

    return bboxes, classes

#Cut doen the label count for testing
label_count = len(label_files)
image_list = [os.path.join(image_dir,img) for img in sorted(os.listdir(image_dir))]
#Drop all of the extra images
image_list = image_list[0:label_count]

#Uncomment to verify that the lists are the same length and the final file is the same
#print(label_count, len(image_list))
#print(f'{label_list[-1]}\n', f'{image_list[-1]}\n')

#Create the transformation
transform = A.Compose([
    A.RandomCrop(450,350, p=0.4),
    A.CenterCrop(300,300,p=0.4),
    A.HorizontalFlip(p=0.4),
    A.VerticalFlip(p=0.4),
    A.RandomBrightnessContrast(p=0.4),
    A.Blur(p=0.4)
], bbox_params=A.BboxParams(format='yolo',label_fields=['class_labels']))

for idx,image in enumerate(image_list):
    #Create 5 augmentations for each image
    for i in range(10):
        #Load the image and convert the color
        img = cv2.imread(image)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        #load the bounding boxes
        bbox, cls = loadAnnotations(idx)
        #transform the image
        transformed = transform(image=img, bboxes=bbox, class_labels=cls)
        transformed_image = transformed['image']
        transformed_bboxes = list(transformed['bboxes'])
        
        #NOTE: There is only one class for this model, so this can be ommitted. the 'cls' variable above defines the class.
        #transformed_class_labels = transformed['class_labels']
        
        #Split the image between train, valid, and test folders (70/20/10 ratio, respectively)
        number = random.random()
        if number <= 0.7:
            cv2.imwrite(rf'{train_img_dir}\{image.split('\\')[-1].split('.')[0]}_{i}.jpg', cv2.cvtColor(transformed_image, cv2.COLOR_RGB2BGR))
            f = open(rf'{train_lbl_dir}\{label_files[idx].split('\\')[-1].split('.')[0]}_{i}.txt', "w")
            for bbx in transformed_bboxes:
                f.write(f'{cls[0]} {bbx[0]} {bbx[1]} {bbx[2]} {bbx[3]}\n')
            f.close()
            print(rf'{train_img_dir}\{image.split('\\')[-1].split('.')[0]}_{i}.jpg saved')

        elif number <= 0.9 and number > 0.7:
            cv2.imwrite(rf'{valid_img_dir}\{image.split('\\')[-1].split('.')[0]}_{i}.jpg', cv2.cvtColor(transformed_image, cv2.COLOR_RGB2BGR))
            f = open(rf'{valid_lbl_dir}\{label_files[idx].split('\\')[-1].split('.')[0]}_{i}.txt', "w")
            for bbx in transformed_bboxes:
                f.write(f'{cls[0]} {bbx[0]} {bbx[1]} {bbx[2]} {bbx[3]}\n')
            f.close()
            print(rf'{test_img_dir}\{image.split('\\')[-1].split('.')[0]}_{i}.jpg saved')

        elif number > 0.9:
            cv2.imwrite(rf'{test_img_dir}\{image.split('\\')[-1].split('.')[0]}_{i}.jpg', cv2.cvtColor(transformed_image, cv2.COLOR_RGB2BGR))
            f = open(rf'{test_lbl_dir}\{label_files[idx].split('\\')[-1].split('.')[0]}_{i}.txt', "w")
            for bbx in transformed_bboxes:
                f.write(f'{cls[0]} {bbx[0]} {bbx[1]} {bbx[2]} {bbx[3]}\n')
            f.close()

            print(rf'{test_img_dir}\{image.split('\\')[-1].split('.')[0]}_{i}.jpg saved')


