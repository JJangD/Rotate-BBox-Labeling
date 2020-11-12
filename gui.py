# list 에서 이미지 클릭 -> 그 이미지로 넘어감
# 키보드 좌우 -> 이미지 넘기기
# 키보드 위아래 -> change thr
# txt 파일 형태러 각 이미지 마다 thr 값 저장
# 목록 저장 사용자에게 파일명 입력 받아서
# 창을 클릭하면 키보드 입력이되게 수정
# v파일 불러온상태에서 또 불러오면 추가되도록 오류나지 않고
# txt 파일이 있는 놈들은 표시해줌
# img 위치와 thr 값을 tuple로 변경



import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import QtCore  # QtCore를 명시적으로 보여주기 위해

from util import *
#import cv2 as cv
import qimage2ndarray
import os.path

import threading
import time
#import copy
#import math
#from enum import Enum,auto

global img
img = None

class MyWindow(QWidget):
    def __init__(self,r_rect):
        super().__init__()
        self.image_paths = []
        self.setupUI()
        self.setFocusPolicy(Qt.ClickFocus)
        self.rec_label_list = []
        self.r_rect = r_rect
        self.current_class = 0
        self.rec_label = 0
        self.cur_rect_idx = 0
        self.r_rect_stack = []
        self.class_list = []
        self.class_stack = []
        self.scale_list = {}

    def keyPressEvent(self, e):
        global STATE

        def isPrintable(key):
            printable = [
                Qt.Key_L,
                Qt.Key_W,
                Qt.Key_A,
                Qt.Key_S,
                Qt.Key_D,
                Qt.Key_R,
                Qt.Key_F,
                Qt.Key_Escape,
                Qt.Key_Up,
                Qt.Key_Down
            ]

            if key in printable:
                return True
            else:
                return False


        if e.key()== Qt.Key_Up:
            currentindex = self.listView.selectionModel().currentIndex().row()
            if currentindex == 0:
                self.listView.setCurrentIndex(self.listView_model.index(self.listView.model().rowCount()-1,0))
            else :
                self.listView.setCurrentIndex(self.listView_model.index(currentindex-1,0))

        elif e.key() == Qt.Key_Down:
            currentindex = self.listView.selectionModel().currentIndex().row()
            if currentindex == self.listView.model().rowCount()-1:
                self.listView.setCurrentIndex(self.listView_model.index(0,0))
            else :
                self.listView.setCurrentIndex(self.listView_model.index(currentindex+1,0))

        #if self.cur_rect_idx== len(self.r_rect_stack):
        if STATE != 'MODIFY':
            if e.key()==Qt.Key_Escape:
                self.r_rect.__init__()
                STATE = StateEnum.INIT
        elif STATE == 'MODIFY':
            #elif self.cur_rect_idx < len(self.r_rect_stack):

            if e.key()==Qt.Key_W:  # w
                self.r_rect.move_y(-1)
                self.saveRECT()
            elif e.key()==Qt.Key_S:  # s
                self.r_rect.move_y(1)
                self.saveRECT()
            elif e.key()==Qt.Key_A:  # a
                self.r_rect.move_x(-1)
                self.saveRECT()
            elif e.key()==Qt.Key_D:  # d
                self.r_rect.move_x(1)
                self.saveRECT()
            elif e.key()==Qt.Key_F:  # F
                self.r_rect.rotate(1)
                self.saveRECT()
            elif e.key()==Qt.Key_R:  # R
                self.r_rect.rotate(-1)
                self.saveRECT()

            elif e.key()==Qt.Key_Delete:
                del self.r_rect_stack[self.cur_rect_idx]
                del self.class_stack[self.cur_rect_idx]

                self.cur_rect_idx = 0

                if len( self.r_rect_stack):
                    [self.r_rect.rp1, self.r_rect.rp2, self.r_rect.rp3, self.r_rect.rp4] = self.r_rect_stack[self.cur_rect_idx]
                else: # when no rect left go to create mode
                    self.r_rect.__init__()
                    STATE = StateEnum.INIT

            elif e.key()==Qt.Key_Escape:
                #MODIFY MODE -> CREATE MODE
                self.cur_rect_idx = len( self.r_rect_stack)
                self.r_rect.__init__()
                STATE = StateEnum.INIT
                #self.saveRECT()

        self.SetImage()

    def setupUI(self):

        self.label_width = 800
        self.label_height = 600


        self.setWindowTitle("R-BBOX LABELING")
        self.setGeometry(300,300,1020,650)

        #TODO GUI for class display and selection
        
        #load image button
        self.LoadImage = QPushButton("Load Image",self)
        self.LoadImage.setGeometry(QRect(850, 560, 140, 20))
        self.LoadImage.clicked.connect(self.LoadImageClicked)
        self.LoadImage.setObjectName("Load Image")

        #image list
        self.listView = QListView(self)
        self.listView.setGeometry(QRect(850, 20, 140, 500))
        self.listView.setObjectName("listView")

        self.listView_model = QStandardItemModel()
        self.listView.setModel(self.listView_model)
        self.listView.selectionModel().selectionChanged.connect(self.ListViewSelChange)

        #image label
        self.label = QLabel(self)
        self.label.setGeometry(QRect(20, 20, self.label_width, self.label_height))
        self.label.setObjectName("Image")
        self.label.setStyleSheet("border-style: solid; border-width: 2px; border-color: black; border-radius: 10px; ")

        #class num control
        self.spinBox = QSpinBox(self)
        self.spinBox.setGeometry(QRect(850, 530, 140, 20))
        self.spinBox.setObjectName("spinBox")

        self.spinBox.setSingleStep(1)
        self.spinBox.setMinimum(0)
        self.spinBox.setMaximum(255)
        self.spinBox.setValue(0)
        self.spinBox.valueChanged.connect(self.spinBoxChanged)


        #save
        self.SaveFile = QPushButton("Save",self)
        self.SaveFile.setGeometry(QRect(850, 590, 140, 20))
        self.SaveFile.clicked.connect(self.SaveFileClicked)
        self.SaveFile.setObjectName("SaveFile")



    def spinBoxChanged(self):

        self.current_class = self.spinBox.value()

        if STATE == 'MODIFY':
            self.class_stack[self.cur_rect_idx] = self.current_class





    #when img list view selection were changed
    def ListViewSelChange(self):

        global STATE
        #get image and image dimension
        self.img = cv.imread(self.image_paths[self.listView.currentIndex().row()])
        h, w, c = self.img.shape

        #when no saved label
        if not self.rec_label_list[self.listView.currentIndex().row()]:
            self.r_rect_stack = []
            self.class_stack=[]

        #load rects if exists
        else:

            self.r_rect_stack = self.rec_label_list[self.listView.currentIndex().row()]
            self.class_stack = self.class_list[self.listView.currentIndex().row()]
            # set first b_box from label as current rect
            [self.r_rect.rp1, self.r_rect.rp2, self.r_rect.rp3, self.r_rect.rp4] = self.r_rect_stack[0]

            self.current_class = self.class_stack[0]
            self.cur_rect_idx = 0




        #to create mode
        self.cur_rect_idx = len(self.r_rect_stack)
        r_rect.__init__()
        STATE = StateEnum.INIT


        #display image
        self.SetImage()


    # Image show on label
    def SetImage(self):
        global STATE
        showimg = copy.deepcopy(self.img)
        showimg=cv.cvtColor(showimg, cv.COLOR_BGR2RGB)



        if STATE == 'INIT' or STATE == 'POINTREADY':
            cv.line(showimg, tuple(self.r_rect.mp1), tuple(self.r_rect.mp2), (0, 255, 0), 2)

        elif STATE == 'LINEREADY':
            self.r_rect.get_rectangle()
            rp1, rp2, rp3, rp4 = self.r_rect.intvalue()
            draw_rotate_rectangle(showimg, rp1, rp2, rp3, rp4, (0, 255, 0), 2)
            cv.line(showimg, tuple(self.r_rect.mp1), tuple(self.r_rect.mp2), (0, 255, 0), 2)

        elif STATE == 'MODIFY':
            if len(self.r_rect_stack):
                rp1, rp2, rp3, rp4 = self.r_rect_stack[self.cur_rect_idx]
                rp1 = tuple(fpoint2ipoint(rp1))
                rp2 = tuple(fpoint2ipoint(rp2))
                rp3 = tuple(fpoint2ipoint(rp3))
                rp4 = tuple(fpoint2ipoint(rp4))

                draw_rotate_rectangle(showimg, rp1, rp2, rp3, rp4, (255, 0, 0), 2)

        if len(self.r_rect_stack):

            for i,r in enumerate(self.r_rect_stack):
                rp1, rp2, rp3, rp4 = r

                rp1 = tuple(fpoint2ipoint(rp1))
                rp2 = tuple(fpoint2ipoint(rp2))
                rp3 = tuple(fpoint2ipoint(rp3))
                rp4 = tuple(fpoint2ipoint(rp4))

                if i != self.cur_rect_idx:
                    draw_rotate_rectangle(showimg, rp1, rp2, rp3, rp4, (0, 255, 255), 2)

        qimage = qimage2ndarray.array2qimage(showimg)
        pixmap = QPixmap.fromImage(qimage)

        self.label.setPixmap(pixmap.scaled(self.label.size()))

    def SaveFileClicked(self):
        f=open("output.txt",'w')
        for i,(path, rec_label_stack,c_stack) in enumerate(zip(self.image_paths, self.rec_label_list, self.class_list)):
                path_split = path.split('/')
                path_mod = str('imgs/')+path_split[-1]
                f.write(f'{path_mod}\n')
                label_path = path.replace(".jpg", ".txt").replace(".JPG",".txt")


                if rec_label_stack:
                    f_label = open(label_path, 'w')

                    for rec_label,c in zip(rec_label_stack,c_stack):

                        labelforsave_temp = xyxy2xyhw(rec_label)
                        labelforsave= [0,0,0,0,0,0]
                        width_scale, height_scale = self.scale_list[self.image_paths[i]]

                        labelforsave[0] = c
                        labelforsave[1] = labelforsave_temp[0] / (width_scale * self.label_width)
                        labelforsave[2] = labelforsave_temp[1] / (height_scale * self.label_height)
                        labelforsave[3] = labelforsave_temp[2] / (width_scale * self.label_width)
                        labelforsave[4] = labelforsave_temp[3] / (height_scale * self.label_height)
                        labelforsave[5] = labelforsave_temp[4]

                        for l in labelforsave:
                            f_label.write(str(l))
                            f_label.write(' ')
                        f_label.write('\n')
                        
                    f_label.close()

        f.close()

    #When load image button is clicked
    def LoadImageClicked(self):
        global STATE
        #show image list
        self.listView.setModel(self.listView_model)

        # list view display
        temp = self.listView.currentIndex().row()  # -1 for first press

        #img file read
        fileopen = QFileDialog.getOpenFileNames(self, 'Open file', "", "jpg file (*.jpg)", '/home')[0]


        for imgpath in fileopen:

            #count =0

            if imgpath not in self.image_paths:
                self.image_paths.append(imgpath)
                label_file = imgpath.replace(".jpg", ".txt").replace(".JPG", ".txt")
                item = imgpath.replace("JPG", "jpg")
                item = [i for i in item.split('/') if i.endswith(".jpg")]

                self.listView_model.appendRow(QStandardItem(item[0]))

                # getimage dimension
                img = cv.imread(imgpath)
                img_h, img_w, img_c = img.shape

                width_scale = img_w / self.label_width
                height_scale = img_h / self.label_height

                self.scale_list[imgpath] = [width_scale, height_scale]

                #label file 존재하면 초록색으로 표시, rect값 읽어서 저장
                if os.path.isfile(label_file):
                    f_label = open(label_file, 'r')

                    readlabel_alllines = f_label.readlines()
                    rec_stack = []
                    c_stack = []
                    if len(readlabel_alllines):

                        for readlabel in readlabel_alllines:
                            readlabel = readlabel.split(' ')

                            #change to actual dimension
                            c = int(readlabel[0])
                            x = float(readlabel[1])*img_w
                            y = float(readlabel[2])*img_h
                            w = float(readlabel[3])*img_w
                            h = float(readlabel[4])*img_h
                            th = float(readlabel[5])

                            rec =  xyhw2xyxy(x, y, w, h, th)
                            rec_stack.append(rec)
                            c_stack.append(c)

                    else:
                        rec_stack = []

                    self.rec_label_list.append(rec_stack)
                    self.class_list.append(c_stack)

                    if rec_stack:
                        self.listView.model().setData(self.listView_model.index(len(self.rec_label_list) - 1, 0),
                                                      QBrush(Qt.green),
                                                      Qt.BackgroundColorRole)
                else:
                    self.class_list.append([-1])
                    self.rec_label_list.append([])


        #to create rect mode
        self.cur_rect_idx = len(self.r_rect_stack)
        r_rect.__init__()
        STATE = StateEnum.INIT


        #show selected image
        if temp == -1 :
            self.listView.setCurrentIndex(self.listView_model.index(0, 0))

        else:
            self.listView.setCurrentIndex(self.listView_model.index(temp, 0))
            #self.SetImage()

        #self.SetImage()

        self.ListViewSelChange()

        self.setMouseTracking(True)
        self.label.setMouseTracking(True)





    def mousePressEvent(self, event):
        global STATE

        if len(self.image_paths):
            if 0 <= event.x() - 20 <= self.label_width and 0 <= event.y() - 20 <= self.label_height:
                width_scale, height_scale = self.scale_list[self.image_paths[self.listView.currentIndex().row()]]
                x = int(round(width_scale * (event.x() - 20)))
                y = int(round(height_scale * (event.y() - 20)))

                if event.buttons() == Qt.LeftButton:
                    # create rect mode
                    if STATE == 'INIT':
                        STATE = StateEnum.POINTREADY
                        self.r_rect.mp1 = [x, y]
                        self.r_rect.mp2 = [x, y]

                        #when rect exists and mouse click in circle contiguous to rect, select rect closest to click

                        minidx = mouse_in_rect(self.r_rect_stack, x, y)

                        if minidx is not False:
                            self.cur_rect_idx = minidx
                            self.spinBox.setValue(self.class_stack[self.cur_rect_idx])
                            self.r_rect.load_r_rect(self.r_rect_stack[self.cur_rect_idx])

                            STATE = 'MODIFY'

                    elif STATE == 'POINTREADY':
                        STATE = StateEnum.LINEREADY
                        self.r_rect.mp2 = [x, y]
                        self.r_rect.hp = [x, y]

                    elif STATE == 'LINEREADY':
                        self.saveRECT()
                        STATE = StateEnum.MODIFY

                    # MODIFY MODE
                    elif STATE == 'MODIFY':

                        minidx = mouse_in_rect(self.r_rect_stack, x, y)
                        print(minidx)
                        if minidx is not False:
                            print('here')

                            self.cur_rect_idx = minidx
                            self.spinBox.setValue(self.class_stack[self.cur_rect_idx])
                            self.r_rect.load_r_rect(self.r_rect_stack[self.cur_rect_idx])
                self.SetImage()

    def mouseMoveEvent(self, event):
        global STATE

        if 0 <= event.x() - 20 <= self.label_width and 0 <= event.y() - 20 <= self.label_height:
            width_scale, height_scale = self.scale_list[self.image_paths[self.listView.currentIndex().row()]]

            x = int(round(width_scale * (event.x() - 20)))
            y = int(round(height_scale * (event.y() - 20)))

            # create rect MODE
            if STATE == 'POINTREADY':
                self.r_rect.mp2 = [x, y]
                self.SetImage()

            elif STATE == 'LINEREADY':
                self.r_rect.hp = [x,y]
                self.SetImage()

    def saveRECT(self):
        #create rect mode
        if STATE !='MODIFY':
        #if self.cur_rect_idx == len(self.r_rect_stack):
            self.r_rect_stack.append([self.r_rect.rp1, self.r_rect.rp2, self.r_rect.rp3, self.r_rect.rp4])
            self.class_stack.append(self.current_class)
            self.cur_rect_idx = len(self.r_rect_stack) -1

        #modify mode
        elif STATE =='MODIFY':
            self.r_rect_stack[self.cur_rect_idx] = [self.r_rect.rp1, self.r_rect.rp2, self.r_rect.rp3, self.r_rect.rp4]
            self.class_stack[self.cur_rect_idx] = self.current_class

        #save current RECT to RECT list
        self.rec_label_list[self.listView.currentIndex().row()] = self.r_rect_stack
        self.class_list[self.listView.currentIndex().row()] = self.class_stack

        #make green on the img list
        self.listView.model().setData(self.listView_model.index(self.listView.currentIndex().row(), 0), QBrush(Qt.green),Qt.BackgroundColorRole)



if __name__ == "__main__":
    global STATE
    STATE = StateEnum.INIT
    r_rect = rot_rect()



    app = QApplication(sys.argv )
    window = MyWindow(r_rect)
    window.show()
    app.exec_()

