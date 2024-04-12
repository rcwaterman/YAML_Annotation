import tkinter as tk
from tkinter import filedialog, Label, StringVar
from PIL import ImageTk, Image
import os
import cv2

class Annotate:
    def __init__(self):
        #Choose the initial data directory
        self.data_dir = filedialog.askdirectory()

        #Set default image/label directories
        self.folder_list = sorted([folder for folder in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, folder))])
        self.image_dir = os.path.join(os.path.join(self.data_dir,self.folder_list[0]),'images')
        self.label_dir = os.path.join(os.path.join(self.data_dir,self.folder_list[0]),'labels')

        self.img_list = []
        self.classifiers = []
        self.last_annotation = []
        self.img_size = (1280, 960)
        self.init_x, self.init_y, self.x, self.y, self.index = 0,0,0,0,0
        self.from_origin = False #Flag to track whether the showImage function is being called from the getOrigin function. 
        self.drawing = False #This is a flag to fix a bug where clicking on the image draws a bounding box from ((0,0), (x,y))

        #Pull all of the images and append to list
        for file in os.listdir(self.image_dir):
            if file.endswith(".png") or file.endswith(".jpg"):
                self.img_list.append(file)

        #Filter through the files in the directory to find the .yaml file
        for file in sorted(os.listdir(self.data_dir)):
            if file.endswith('.yaml'):
                #Open the file
                f = open(os.path.join(self.label_dir, file), "r")
                #Read the lines of a file into a list
                lines = f.readlines()
                #loop through each line to find the line that contains the self.classifiers
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
                                ele = ele.replace('\n','')
                            #Append the element to the classifier list
                            self.classifiers.append(ele)

        self.max_index = len(self.img_list)-1

        #After defining the directory, create the gui.
        self.createGUI()

    def createGUI(self):
        #Initialize tkinter gui
        self.gui = tk.Tk(className = ' YAML Annotation')

        #Initialize the frame and specify a grid structure
        self.frm = tk.Frame(self.gui)
        self.frm.grid() 

        #Define variables
        self.tool_list = ["Rectangle", "Circle"]
        self.text_offset = 10

        #Define lists for option menus
        self.obj_class = StringVar(self.frm)
        self.tools = StringVar(self.frm)
        self.subfolders = StringVar(self.frm)

        #Set lists to default settings
        self.obj_class.set(f'{self.classifiers[0]}')
        self.tools.set(self.tool_list[0])
        self.subfolders.set(self.folder_list[0].split(r'\\')[-1])

        #Set up image feed
        self.feed = Label(self.frm)
        self.feed.grid(row = 0, column = 0, padx = 5, pady = 5, columnspan = 5, rowspan=2, sticky = "nsew")

        #Bind mouse presses and scroll wheel to different functions
        self.feed.bind("<Button-1>", self.getInitOrigin)
        self.feed.bind("<B1-Motion>", self.getOrigin)
        self.feed.bind("<ButtonRelease-1>", self.updateLabel)
        self.feed.bind_all("<MouseWheel>", self.changeImage)

        #Bind key presses to undo and redo last annotation. Used for ctrl-z and ctrl-y functionality
        self.frm.bind_all("<Control-z>", self.clearLastAnnotation)
        self.frm.bind_all("<Control-y>", self.redoLastAnnotation)

        self.change_directory = tk.Button(self.frm, text='Change Directory', command=self.change_dir, font = ('calibre',14,'bold'), fg = "Black").grid(column=1, row=2)

        self.clear_annotations = tk.Button(self.frm, text='Clear All Annotations', command=self.clearAllAnnotations, font = ('calibre',14,'bold'), fg = "red").grid(column=2, row=2)

        self.next_annotation = tk.Button(self.frm, text='Next Annotation', command=self.nextAnnotation, font = ('calibre',14,'bold'), fg = "green").grid(column=4, row=2)

        self.select_tool = tk.OptionMenu(self.frm, self.tools, *self.tool_list)
        self.select_tool.grid(column=5, row=0)

        self.select_class = tk.OptionMenu(self.frm, self.obj_class, *self.classifiers)
        self.select_class.grid(column=5, row=1)

        self.select_directory = tk.OptionMenu(self.frm, self.subfolders, *self.folder_list)
        self.select_directory.grid(column=5, row=2)

        self.loadAnnotations()

        #Perform this at the end so the select_dir function isn't called twice on launch
        self.subfolders.trace_add("write",self.change_folder)

        self.gui.mainloop()

    def change_dir(self):
        """
        Change the top level data directory.
        """

        self.data_dir = filedialog.askdirectory()
        self.folder_list = sorted([folder for folder in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, folder))])
        self.image_dir = os.path.join(os.path.join(self.data_dir,self.folder_list[0]),r'images')
        self.label_dir = os.path.join(os.path.join(self.data_dir,self.folder_list[0]),r'labels')
        self.img_list = []
        self.classifiers = []
        self.last_annotation = []
        
        #Pull all of the images and append to list
        for file in os.listdir(self.image_dir):
            if file.endswith(".png") or file.endswith(".jpg"):
                self.img_list.append(file)

        #Filter through the files in the directory to find the .yaml file
        for file in sorted(os.listdir(self.data_dir)):
            if file.endswith('.yaml'):
                #Open the file
                f = open(os.path.join(self.label_dir, file), "r")
                #Read the lines of a file into a list
                lines = f.readlines()
                #loop through each line to find the line that contains the self.classifiers
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
                            self.classifiers.append(ele)

        self.max_index = len(self.img_list)-1

        #If this is being called from a directory change, update the class selections and load the new image
        self.menu=self.select_class["menu"]
        self.menu.delete(0,"end")
        for cls in self.classifiers:
            self.menu.add_command(label=cls,command=lambda value=cls: self.obj_class.set(value)) 
        self.obj_class.set(f'{self.classifiers[0]}')
        self.init_x, self.init_y, self.x, self.y, self.index = 0,0,0,0,0
        self.loadAnnotations()

    def change_folder(self, *args):
        """
        Function to change the subfolder of the data directory that the user is working within.
        """
        #Set image and label dirs
        self.image_dir = os.path.join(os.path.join(self.data_dir,self.subfolders.get()),'images')
        self.label_dir = os.path.join(os.path.join(self.data_dir,self.subfolders.get()),'labels')

        self.img_list = []
        self.last_annotation = []
        self.init_x, self.init_y, self.x, self.y, self.index = 0,0,0,0,0

        #Pull all of the images and append to list
        for file in os.listdir(self.image_dir):
            if file.endswith(".png") or file.endswith(".jpg"):
                self.img_list.append(file)

        self.loadAnnotations()

    def loadAnnotations(self):
        #Clear the label list
        self.label_list = []

        #If index is greater than the max index, go to beginning
        if self.index > self.max_index:
            self.index=0
        #If index is less than zero, go to end
        elif self.index < 0:
            self.index=self.max_index

        self.label_file = f'{os.path.join(self.label_dir, self.img_list[self.index].split('.')[0])}.txt'
        if os.path.exists(self.label_file):
            f = open(self.label_file, "r")
            for idx, line in enumerate(f):
                if idx+1 > len(self.label_list):
                    items = line.split()
                    cls = items[0]
                    center_x = int(self.img_size[0]*float(items[1]))
                    center_y = int(self.img_size[1]*float(items[2]))
                    width = int(self.img_size[0]*float(items[3]))
                    height = int(self.img_size[1]*float(items[4]))

                    self.label_list.append((cls, center_x, center_y, width, height))
        else:
            self.label_list = []

        self.showImage()

    def changeImage(self, event):
        """
        Change the image based on the passed event the image list. Clear the last_annotation list so ctrl-y functions don't affect the new image.

        This function is called when the scroll wheel is scrolled up. Tkinter passes events to any function called by the event handler,
        so an un-used event variable is taken as an argument.
        """

        if event.delta > 0:
            self.index = self.index+1
            self.last_annotation = []
            self.loadAnnotations()
        else:
            self.index = self.index-1
            self.last_annotation = []
            self.loadAnnotations()

    def getInitOrigin(self, eventorigin):
        self.init_x = eventorigin.x if eventorigin.x>=0 else 0
        self.init_y = eventorigin.y if eventorigin.y>=0 else 0
        self.init_x = self.init_x if self.init_x <= self.img_size[0] else self.img_size[0]-1
        self.init_y = self.init_y if self.init_y <= self.img_size[1] else self.img_size[1]-1

    def getOrigin(self, eventorigin):
        self.x = eventorigin.x if eventorigin.x>=0 else 0
        self.y = eventorigin.y if eventorigin.y>=0 else 0
        self.x = self.x if self.x <= self.img_size[0] else self.img_size[0]-1
        self.y = self.y if self.y <= self.img_size[1] else self.img_size[1]-1
        self.drawing = True #This is a flag to fix a bug where clicking on the image draws a bounding box from ((0,0), (x,y))
        self.from_origin = True
        self.showImage()

    def updateLabel(self, eventorigin):
        #Stop clicking from saving the image
        if abs(self.x-self.init_x) > 2 and abs(self.y-self.init_y) > 2 and self.init_x > 0 and self.drawing:
            self.saveAnnotations()
            self.drawing = False #This is a flag to fix a bug where clicking on the image draws a bounding box from ((0,0), (x,y))
        else:
            self.loadAnnotations()
        self.init_x, self.init_y, self.x, self.y = 0,0,0,0

    def showImage(self):
        self.img = os.path.join(self.image_dir, self.img_list[self.index])
        #Grab image from cam and convert to tkinter friendly format
        cv2image=cv2.cvtColor(cv2.imread(self.img),cv2.COLOR_BGR2RGB)
        cv2image=cv2.resize(cv2image, self.img_size)

        #Draw the newest label in real time, only if the x coord is not zero.
        #This fixes a bug where a bounding box is drawn in the top right corner
        if self.from_origin:
            #Compute the top left corner of the bounding box
            #This information is not stored to the class because it is only used to compute the bounding box, which is stored in the label file.
            center = (int((self.init_x + self.x)/2), int((self.init_y + self.y)/2))
            width = abs(self.init_x-self.x)
            height = abs(self.init_y-self.y)
            tl = (center[0]-int(width/2)-self.text_offset, center[1]-int(height/2)-self.text_offset)

            if self.tools.get() == "Rectangle":
                cv2image = cv2.rectangle(cv2image, (self.init_x,self.init_y), (self.x,self.y), color=(0,255,0), thickness=1)
                cv2image = cv2.putText(cv2image, f'{self.obj_class.get()}', tl, cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,0,255),1)

            elif self.tools.get() == "Circle":
                radius = int((width+height)/2)
                cv2image = cv2.circle(cv2image, center, radius=radius, color=(0,255,0), thickness=1)

            for label in self.label_list:
                cls, center_x, center_y, width, height = int(label[0]), label[1], label[2], label[3], label[4]
                cv2image = cv2.rectangle(cv2image, (center_x-int(width/2),center_y-int(height/2)), (center_x+int(width/2),center_y+int(height/2)), color=(0,255,0), thickness=1)
                cv2image = cv2.putText(cv2image, f'{self.classifiers[cls]}', (center_x-int(width/2)-self.text_offset,center_y-int(height/2)-self.text_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,0,255),1)
            
            #Reset the flag
            self.from_origin=False
        else:
            for label in self.label_list:
                cls, center_x, center_y, width, height = int(label[0]), label[1], label[2], label[3], label[4]
                cv2image = cv2.rectangle(cv2image, (center_x-int(width/2),center_y-int(height/2)), (center_x+int(width/2),center_y+int(height/2)), color=(0,255,0), thickness=1)
                cv2image = cv2.putText(cv2image, f'{self.classifiers[cls]}', (center_x-int(width/2)-self.text_offset,center_y-int(height/2)-self.text_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,0,255),1)

        tkinterframe = Image.fromarray(cv2image)
        displayImage = ImageTk.PhotoImage(master = self.frm, image = tkinterframe)
        self.feed.displayImage = displayImage
        self.feed.configure(image = displayImage)

    def saveAnnotations(self):
        #Normalize the bounding box coordinates
        self.norm_init_x, self.norm_init_y, self.norm_x, self.norm_y = self.init_x/self.img_size[0], self.init_y/self.img_size[1], self.x/self.img_size[0], self.y/self.img_size[1]
        
        #Get the classifier
        cls = self.classifiers.index(f'{self.obj_class.get()}')

        if self.tools.get() == "Rectangle":
            x_center = (self.norm_init_x + self.norm_x)/2
            y_center = (self.norm_init_y + self.norm_y)/2
            width = abs(self.norm_x-self.norm_init_x)
            height = abs(self.norm_y-self.norm_init_y)
        elif self.tools.get() == "Circle":
            x_center = (self.norm_init_x + self.norm_x)/2
            y_center = (self.norm_init_y + self.norm_y)/2
            diameter = ((abs(self.norm_x-self.norm_init_x))+(abs(self.norm_y-self.norm_init_y)))
            width = diameter*(self.img_size[1]/self.img_size[0]) #scale the width to the height so the normalized values are accurate.
            height = diameter

            #If the width puts the bounding box outside of the image, compute the difference to set the dimension to either 0 or 1
            if x_center - (diameter*(self.img_size[1]/self.img_size[0]))/2 < 0:
                width = 2*(width + (x_center - width))
            elif x_center + (diameter*(self.img_size[1]/self.img_size[0]))/2 > 1:
                width = 2*(width + (1-(x_center + width)))

            #If the height puts the bounding box outside of the image, compute the difference to set the dimension to either 0 or 1
            if y_center - height/2 < 0:
                height = 2*(height + (y_center - height))
            elif y_center + height/2 > 1:
                height = 2*(height + (1-(y_center + height)))
            
        f = open(f'{os.path.join(self.label_dir, self.img_list[self.index].split('.')[0])}.txt', 'a')
        """
        Lines must be written to the annotation file in the following format:

        Class   x_center    y_center    width   height
        
        """
        f.write(f'{cls} {x_center} {y_center} {width} {height}\n')
        f.close()

        self.loadAnnotations()

    def nextAnnotation(self):
        """
        Finds the next image in the list that needs to be annotated, assuming the user is annotating the images in order.
        """
        self.last_label = [file for file in sorted(os.listdir(self.label_dir)) if file.endswith('.txt')][-1]
        for idx, name in enumerate(self.img_list):
            if self.last_label.split('.')[0] in name.split('.')[0]:
                self.index = idx+1
        self.loadAnnotations()

    def clearAllAnnotations(self):
        #Clear the label list
        self.label_list = []
        f = open(f'{os.path.join(self.label_dir, self.img_list[self.index].split('.')[0])}.txt', 'w').close()
        self.loadAnnotations()

    def clearLastAnnotation(self, event):

        #clear the label list
        self.label_list = []
        #Open the file in read/write mode
        f = open(f'{os.path.join(self.label_dir, self.img_list[self.index].split('.')[0])}.txt', 'r+')
        #Read the lines of the file into a list and remove the last list element
        self.lines = f.readlines()
        self.last_annotation.append(self.lines[-1])
        self.lines.pop(-1)
        #Close the file
        f.close()
        #Reopen the file in write mode
        f = open(f'{os.path.join(self.label_dir, self.img_list[self.index].split('.')[0])}.txt', 'w')
        #Write the remaining lines back to the file
        f.writelines(self.lines)
        #Close the file
        f.close()
        #Load the annotations and draw them to the image
        self.loadAnnotations()

    def redoLastAnnotation(self, event):

        if len(self.last_annotation)>0:
            #Open the file in read/write mode
            f = open(f'{os.path.join(self.label_dir, self.img_list[self.index].split('.')[0])}.txt', 'a')
            #Write the last annotation in the list
            f.write(self.last_annotation[-1])
            f.close()
            #Remove the last annotation
            self.last_annotation.pop(-1)

            self.loadAnnotations()


def main() -> None:
    tk.Tk().withdraw() # prevents an empty tkinter window from appearing

    #Instantiate the Annotation class
    Annotate()

if __name__ == '__main__':
    main()