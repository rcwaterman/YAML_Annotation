# YAML Annotation Tool

Yet another markup language (YAML) is a common annotation/labeling theme for computer vision and object detection ML models. YAML annotation provides a standardized method for calling out object classification, making fine tuning pre-trained models highly efficient.

## YAML Formatting

YAML files follow the convention, below. The 'yaml_example.yaml' file can provide further context for the structure of yaml documents.

> #Data locations:
>    - train: ../train/images
>    - val: ../valid/images
>    - test: ../test/images

> #Number of categories:
>    - nc: 6

> #Category names
>   - names: ["Scratch", "Dig", "Watermark", "Concave Region", "Convex Region", "Lens Perimeter"]

Data locations refer to the training, validation, and test image directories. It is up to the user to organize and maintain/edit this structure for the application. Additionally, the user can edit the data location structure, so long as the data load is modified accordingly during the model fine tuning stage.

## Annotation Tool: How-To

The YAML Annotation Tool (./YAML/annotation.py) is designed to automatically generate and store label files in [Ultraltics YOLO format](https://docs.ultralytics.com/datasets/detect/). The tool also supports real time editing of existing labels for a given directory of labels through the GUI. 

Directory structure is critical for annotation tool functionality. Every data folder must have an adjacent folder with a '_labels' suffix.
