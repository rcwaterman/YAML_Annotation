import tkinter as tk
from tkinter import filedialog, Label, StringVar
from PIL import ImageTk, Image
import os
import cv2

"""
This software tool aims to make object detection annotation more efficient for a custom dataset.

The user will select a data directory, then the program will recursively open each image in the directory and allow the user to annotate the image.
"""

tk.Tk().withdraw() # prevents an empty tkinter window from appearing

def select_dir(change_dir=False, change_dataset=False):
    global img_list
    global label_dir
    global image_dir
    global max_index
    global classifiers
    global data_dir
    classifiers = []

    #If the directory is being changed
    if not change_dir and not change_dataset:
        #Choose the initial data directory
        data_dir = filedialog.askdirectory()

    #Default to the training folder.
    if not change_dataset:
        image_dir = os.path.join(data_dir, r'original_images\images')
        label_dir = os.path.join(data_dir, r'original_images\labels')
    else:
        image_dir = os.path.join(data_dir, rf'{dirs.get()}\images')
        label_dir = os.path.join(data_dir, rf'{dirs.get()}\labels')

    img_list = []

    #Pull all of the images and append to list
    for file in sorted(os.listdir(image_dir)):
        if file.endswith(".png") or file.endswith(".jpg"):
            img_list.append(file)
    
    #Filter through the files in the label directory to find the .yaml file
    for file in os.listdir(data_dir):
        if file.endswith('.yaml'):
            #Open the file
            f = open(os.path.join(data_dir, file), "r")
            #Read the lines of a file into a list
            lines = f.readlines()
            #loop through each line to find the line that contains the classifiers
            for line in lines:
                #If the line contains the classifier
                if "names:" in line:
                    #Split the line by the first occurrence of a space and grab the list (at index -1)
                    cls = line.split(" ", 1)[-1]
                    #Get each element of the text list
                    cls = cls.split(',')
                    #Loop through each element
                    for ele in cls:
                        #If the open or closed bracket is in the element, remove it
                        if '[' in ele or ']' in ele or '"' in ele:
                            ele = ele.replace('[','')
                            ele = ele.replace(']','')
                            ele = ele.replace('"','')
                        #Append the element to the classifier list
                        classifiers.append(ele)

    max_index = len(img_list)-1

    #If this is being called from a directory change, update the class selections and load the new image
    if change_dir:
        menu=select_class["menu"]
        menu.delete(0,"end")
        for cls in classifiers:
            menu.add_command(label=cls,command=lambda value=cls: obj_class.set(value)) 
        obj_class.set(f'{classifiers[0]}')
        init_x, init_y, x, y,index = 0,0,0,0,0
        loadAnnotations(index)

    #If the dataset is being changed, re-show the image and annotations
    if change_dataset:
        init_x, init_y, x, y,index = 0,0,0,0,0
        loadAnnotations(index)

#Define global variables
global index
global label_list
global init_x, init_y, x, y
global img_list
global classifiers

#Select the initial directory. This must be done prior to variable definition as the variables are dependent on the classifier list
select_dir()

#Initialize tkinter gui
gui = tk.Tk(className = ' YAML Annotation')

#Initialize the frame and specify a grid structure
frm = tk.Frame(gui)
frm.grid() 

#define variables
label_list = []
tool_list = ["Rectangle", "Circle"]
directory_list = ["original_images","train", "test", "valid"]
img_size = (960, 720)
init_x, init_y, x, y,index = 0,0,0,0,0
text_offset = 10
obj_class = StringVar(frm)
tools = StringVar(frm)
dirs = StringVar(frm)
obj_class.set(f'{classifiers[0]}')
tools.set(tool_list[0])
dirs.set(directory_list[0])

#Set up image feed
feed = Label(frm)
feed.grid(row = 0, column = 0, padx = 5, pady = 5, columnspan = 5, rowspan=3, sticky = "nsew")

def getInitOrigin(eventorigin):
    global init_x, init_y
    init_x = eventorigin.x if eventorigin.x>=0 else 0
    init_y = eventorigin.y if eventorigin.y>=0 else 0
    init_x = init_x if init_x <= img_size[0] else img_size[0]-1
    init_y = init_y if init_y <= img_size[1] else img_size[1]-1

def getOrigin(eventorigin):
    global x,y
    x = eventorigin.x if eventorigin.x>=0 else 0
    y = eventorigin.y if eventorigin.y>=0 else 0
    x = x if x <= img_size[0] else img_size[0]-1
    y = y if y <= img_size[1] else img_size[1]-1
    showImage(True)

def updateLabel(eventorigin):
    global init_x, init_y, x, y, index
    #Stop clicking from saving the image
    if abs(x-init_x) > 2 and abs(y-init_y) > 2 and init_x > 0:
        saveAnnotations()
    init_x, init_y, x, y = 0,0,0,0

feed.bind("<Button-1>", getInitOrigin)
feed.bind("<B1-Motion>",getOrigin)
feed.bind("<ButtonRelease-1>", updateLabel)
    
def showImage(from_origin=False):
    global index
    global label_list
    global init_x, init_y, x, y

    img = os.path.join(image_dir, img_list[index])
    #Grab image from cam and convert to tkinter friendly format
    cv2image=cv2.cvtColor(cv2.imread(img),cv2.COLOR_BGR2RGB)
    cv2image=cv2.resize(cv2image, img_size)

    #Draw the newest label in real time, only if the x coord is not zero.
    #This fixes a bug where a bounding box is drawn in the top right corner
    if from_origin:
        #Compute the top left corner of the bounding box
        center = (int((init_x + x)/2), int((init_y + y)/2))
        width = abs(init_x-x)
        height = abs(init_y-y)
        tl = (center[0]-int(width/2)-text_offset, center[1]-int(height/2)-text_offset)

        if tools.get() == "Rectangle":
            cv2image = cv2.rectangle(cv2image, (init_x,init_y), (x,y), color=(0,255,0), thickness=1)
            cv2image = cv2.putText(cv2image, f'{obj_class.get()}', tl, cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,0,255),1)
        elif tools.get() == "Circle":
            radius = int((width+height)/2)
            cv2image = cv2.circle(cv2image, center, radius=radius, color=(0,255,0), thickness=1)

        for label in label_list:
            cls, center_x, center_y, width, height = int(label[0]), label[1], label[2], label[3], label[4]
            cv2image = cv2.rectangle(cv2image, (center_x-int(width/2),center_y-int(height/2)), (center_x+int(width/2),center_y+int(height/2)), color=(0,255,0), thickness=1)
            cv2image = cv2.putText(cv2image, f'{classifiers[cls]}', (center_x-int(width/2)-text_offset,center_y-int(height/2)-text_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,0,255),1)
    else:
        for label in label_list:
            cls, center_x, center_y, width, height = int(label[0]), label[1], label[2], label[3], label[4]
            cv2image = cv2.rectangle(cv2image, (center_x-int(width/2),center_y-int(height/2)), (center_x+int(width/2),center_y+int(height/2)), color=(0,255,0), thickness=1)
            cv2image = cv2.putText(cv2image, f'{classifiers[cls]}', (center_x-int(width/2)-text_offset,center_y-int(height/2)-text_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,0,255),1)

    tkinterframe = Image.fromarray(cv2image)
    displayImage = ImageTk.PhotoImage(master = frm, image = tkinterframe)
    feed.displayImage = displayImage
    feed.configure(image = displayImage)

def loadAnnotations(idx):
    global index
    global label_list
    index = idx

    #Clear the label list
    label_list = []

    #If index is greater than the max index, go to beginning
    if index > max_index:
        index=0
    #If index is less than zero, go to end
    elif index < 0:
        index=max_index

    label_file = f'{os.path.join(label_dir, img_list[index].split('.')[0])}.txt'
    if os.path.exists(label_file):
        f = open(label_file, "r")
        for idx, line in enumerate(f):
            if idx+1 > len(label_list):
                items = line.split()
                cls = items[0]
                center_x = int(img_size[0]*float(items[1]))
                center_y = int(img_size[1]*float(items[2]))
                width = int(img_size[0]*float(items[3]))
                height = int(img_size[1]*float(items[4]))

                label_list.append((cls, center_x, center_y, width, height))
    else:
        label_list = []

    showImage()   

def nextAnnotation():
    """
    Finds the next image in the list that needs to be annotated, assuming the user is annotating the images in order.
    """
    global index, img_list
    last_label = [file for file in sorted(os.listdir(label_dir)) if file.endswith('.txt')][-1]
    for idx, name in enumerate(img_list):
        if last_label.split('.')[0] in name.split('.')[0]:
            index = idx+1
    loadAnnotations(index)

def saveAnnotations():
    global init_x, init_y, release_x, release_y, img_list, classifiers, index
    #Normalize the bounding box coordinates
    norm_init_x, norm_init_y, norm_release_x, norm_release_y = init_x/img_size[0], init_y/img_size[1], release_x/img_size[0], release_y/img_size[1]

    cls = classifiers.index(f'{obj_class.get()}')
    if tools.get() == "Rectangle":
        x_center = (norm_init_x + norm_release_x)/2
        y_center = (norm_init_y + norm_release_y)/2
        width = abs(norm_release_x-norm_init_x)
        height = abs(norm_release_y-norm_init_y)
    elif tools.get() == "Circle":
        x_center = (norm_init_x + norm_release_x)/2
        y_center = (norm_init_y + norm_release_y)/2
        radius = ((abs(norm_release_x-norm_init_x))+(abs(norm_release_y-norm_init_y)))
        width = radius*(img_size[1]/img_size[0]) #scale the width to the height so the normalized values are accurate.
        height = radius
        
    f = open(f'{os.path.join(label_dir, img_list[index].split('.')[0])}.txt', 'a')
    """
    Lines must be written to the annotation file in the following format:

    Class   x_center    y_center    width   height
    
    """
    f.write(f'{cls} {x_center} {y_center} {width} {height}\n')
    f.close()

    loadAnnotations(index)

def clearAllAnnotations():
    global label_list
    label_list = []
    f = open(f'{os.path.join(label_dir, img_list[index].split('.')[0])}.txt', 'w').close()
    loadAnnotations(index)

def clearLastAnnotation():
    global label_list
    label_list = []
    #Open the file in read/write mode
    f = open(f'{os.path.join(label_dir, img_list[index].split('.')[0])}.txt', 'r+')
    #Read the lines of the file into a list and remove the last list element
    lines = f.readlines()
    lines.pop(-1)
    #Close the file
    f.close()
    #Reopen the file in write mode
    f = open(f'{os.path.join(label_dir, img_list[index].split('.')[0])}.txt', 'w')
    #Write the remaining lines back to the file
    f.writelines(lines)
    #Close the file
    f.close()
    #Load the annotations and draw them to the image
    loadAnnotations(index)

prev_image = tk.Button(frm, text='Previous Image', command=lambda: loadAnnotations(index-1), font = ('calibre',16,'bold'), fg = "green").grid(column=0, row=3)

clear_last_annotation = tk.Button(frm, text='Clear Last Annotation', command=clearLastAnnotation, font = ('calibre',16,'bold'), fg = "red").grid(column=1, row=3)

change_dir = tk.Button(frm, text='Change Directory', command=lambda: select_dir(change_dir=True), font = ('calibre',16,'bold'), fg = "Black").grid(column=2, row=3)

clear_annotations = tk.Button(frm, text='Clear All Annotations', command=clearAllAnnotations, font = ('calibre',16,'bold'), fg = "red").grid(column=3, row=3)

next_image = tk.Button(frm, text='Next Image', command=lambda: loadAnnotations(index+1), font = ('calibre',16,'bold'), fg = "green").grid(column=4, row=3)

select_tool = tk.OptionMenu(frm, tools, *tool_list)
select_tool.grid(column=5, row=0)

select_class = tk.OptionMenu(frm, obj_class, *classifiers)
select_class.grid(column=5, row=1)

select_directory = tk.OptionMenu(frm, dirs, *directory_list)
select_directory.grid(column=5, row=2)

loadAnnotations(index)

#Perform this at the end so the select_dir function isn't called twice on launch
dirs.trace_add("write", lambda *args: select_dir(False, True))

#this starts the mainloop for the gui
gui.mainloop()
