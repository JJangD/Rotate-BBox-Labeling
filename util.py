import math
import cv2 as cv
import copy
import numpy as np
from sys import float_info
from enum import Enum,auto

# returns rect that was clicked by mouse, closest one more if more than one
def mouse_in_rect(r_rect_stack, x, y):

    maxx = 0
    maxy = 0


    minidx = -1
    mindis = float('inf')

    if len(r_rect_stack):
        for i, r in enumerate(r_rect_stack):

            print('h')

            r = np.array(r)
            r_roll = np.roll(r, -1, axis=0)

            mp = (r[0]+r[2])/2


            abc = np.stack([r_roll[:, 1] - r[:, 1],
                   r[:, 0] - r_roll[:, 0],
                   r_roll[:, 0] * r[:, 1] - r_roll[:, 1] * r[:, 0]],axis=1)

            val = abc[:,0] * x + abc[:,1] * y + abc[:,2]
            print(all(val<0))

            cur_dis = (mp[0] - x) ** 2 + (mp[1] - y) ** 2

            if all(val<0):

                if cur_dis < mindis:
                    mindis = cur_dis
                    minidx = i

    if minidx != -1:
        return minidx
    else:
        return False

def trans_scale(p, s_w,s_h):
    return [p[0]*s_w, p[1]*s_h]


def get_distance(p1,p2):
    return math.sqrt((p1[0]-p2[0])*(p1[0]-p2[0])+(p1[1]-p2[1])*(p1[1]-p2[1]))

def rotate(p,costh,sinth):
    x = p[0]
    y = p[1]

    x_o = x * costh - y * sinth
    y_o = y * costh + x * sinth
    return [x_o, y_o]


def parallel(p,dx,dy):
    x = p[0]
    y = p[1]
    return [x+dx, y+dy]


def fpoint2ipoint (p):
    return [int(round(p[0])), int(round(p[1]))]


def draw_rotate_rectangle(showimage,rp1,rp2,rp3,rp4,color,thickness):
    cv.line(showimage, rp1, rp2, color, thickness=thickness)
    cv.line(showimage, rp2, rp3, color, thickness=thickness)
    cv.line(showimage, rp3, rp4, color, thickness=thickness)
    color2 = (0, 0, 255)
    #blue line for the tail side
    cv.line(showimage, rp4, rp1, color2, thickness=thickness)

def xyxy2xyhw( label):

    rp1 = label[0]
    rp2 = label[1]
    rp3 = label[2]
    rp4 = label[3]

    mx = (rp1[0] + rp3[0]) / 2
    my = (rp1[1] + rp3[1]) / 2

    # parrallel
    rp1_a = parallel(rp1, -mx, -my)
    rp2_a = parallel(rp2, -mx, -my)
    rp3_a = parallel(rp3, -mx, -my)
    rp4_a = parallel(rp4, -mx, -my)

    # rotate
    l = math.sqrt((rp1_a[0] - rp2_a[0]) * (rp1_a[0] - rp2_a[0]) + (rp1_a[1] - rp2_a[1]) * (rp1_a[1] - rp2_a[1]))
    costh = (rp2_a[0] - rp1_a[0]) / l
    sinth = (rp2_a[1] - rp1_a[1]) / l

    rp1_b = rotate(rp1_a, costh, -sinth)
    rp2_b = rotate(rp2_a, costh, -sinth)
    rp3_b = rotate(rp3_a, costh, -sinth)
    rp4_b = rotate(rp4_a, costh, -sinth)

    # parrallel
    s_rp1 = parallel(rp1_b, mx, my)
    s_rp2 = parallel(rp2_b, mx, my)
    s_rp3 = parallel(rp3_b, mx, my)
    s_rp4 = parallel(rp4_b, mx, my)

    th = math.degrees(math.atan2(sinth,costh))

    # -180 ~ 180 -> 0 ~ 360
    if th < -0.5:
        th += 360

    # -180 ~ 180 -> -90 ~ 90
    # if th>90:
    #     th = th-180
    # elif th<=-90:
    #     th = th+180


    x = int(round(mx))
    y = int(round(my))
    w = int(round(s_rp3[0] - s_rp1[0]))
    h = int(round(s_rp3[1] - s_rp1[1]))
    th = int(round(th))

    return [x,y,w,h,th]


def xyhw2xyxy(x,y,w,h,th):

    # rotate
    costh = math.cos(math.radians(th))
    sinth = math.sin(math.radians(th))


    rp1 = [x - 0.5 * costh * w + 0.5 * sinth * h, y - 0.5 * sinth * w - 0.5 * costh * h]
    rp2 = [x + 0.5 * costh * w + 0.5 * sinth * h, y + 0.5 * sinth * w - 0.5 * costh * h]
    rp3 = [x + 0.5 * costh * w - 0.5 * sinth * h, y + 0.5 * sinth * w + 0.5 * costh * h]
    rp4 = [x - 0.5 * costh * w - 0.5 * sinth * h, y - 0.5 * sinth * w + 0.5 * costh * h]


    return [rp1, rp2, rp3, rp4]


class rot_rect():
    def __init__(self, mp1=[0,0],mp2=[0,0],hp=[0,0],rp1=[0,0],rp2=[0,0],rp3=[0,0],rp4=[0,0],lineready=False, rectready=False):
        self.mp1 = mp1
        self.mp2 = mp2
        self.hp = hp
        self.rp1 = rp1
        self.rp2 = rp2
        self.rp3 = rp3
        self.rp4 = rp4
        self.h =0



    def load_r_rect(self, r_rect):

        self.rp1 = r_rect[0]
        self.rp2 = r_rect[1]
        self.rp3 = r_rect[2]
        self.rp4 = r_rect[3]


    def rotate(self,th):
        #TODO 깔끔하게
        mx = (self.rp1[0] + self.rp3[0]) / 2
        my = (self.rp1[1] + self.rp3[1]) / 2

        # parrallel
        rp1_a = parallel(self.rp1, -mx, -my)
        rp2_a = parallel(self.rp2, -mx, -my)
        rp3_a = parallel(self.rp3, -mx, -my)
        rp4_a = parallel(self.rp4, -mx, -my)

        # rotate
        costh = math.cos(math.radians(th))
        sinth = math.sin(math.radians(th))

        rp1_b = rotate(rp1_a, costh, sinth)
        rp2_b = rotate(rp2_a, costh, sinth)
        rp3_b = rotate(rp3_a, costh, sinth)
        rp4_b = rotate(rp4_a, costh, sinth)

        # parrallel
        self.rp1 = parallel(rp1_b, mx, my)
        self.rp2 = parallel(rp2_b, mx, my)
        self.rp3 = parallel(rp3_b, mx, my)
        self.rp4 = parallel(rp4_b, mx, my)

    def move_x(self,delta):
        # parrallel
        self.rp1[0] = self.rp1[0] + delta
        self.rp2[0] = self.rp2[0] + delta
        self.rp3[0] = self.rp3[0] + delta
        self.rp4[0] = self.rp4[0] + delta

    def move_y(self,delta):
        # parrallel
        self.rp1[1] = self.rp1[1] + delta
        self.rp2[1] = self.rp2[1] + delta
        self.rp3[1] = self.rp3[1] + delta
        self.rp4[1] = self.rp4[1] + delta



    def intvalue(self):
        val1 = tuple([int(round(i1)) for i1 in self.rp1])
        val2 = tuple([int(round(i2)) for i2 in self.rp2])
        val3 = tuple([int(round(i3)) for i3 in self.rp3])
        val4 = tuple([int(round(i4)) for i4 in self.rp4])

        return val1, val2, val3, val4

    def get_rectangle(self):
        l = get_distance(self.mp1, self.mp2)

        # mp1_a = None
        # mp2_a = None


        # if self.mp2[0] < self.mp1[0]:
        #     mp1_a = self.mp2
        #     mp2_a = self.mp1
        # else:
        #     mp1_a = self.mp1
        #     mp2_a = self.mp2

        mx = (self.mp1[0] + self.mp2[0]) / 2
        my = (self.mp1[1] + self.mp2[1]) / 2

        # parrallel move
        mp1_a = parallel(self.mp1, -mx, -my)
        mp2_a = parallel(self.mp2, -mx, -my)
        hp_a = parallel(self.hp, -mx, -my)

        # rotate
        costh = 2 * mp2_a[0] / l
        sinth = 2 * mp2_a[1] / l

        mp1_b = rotate(mp1_a, costh, -sinth)
        mp2_b = rotate(mp2_a, costh, -sinth)
        hp_b = rotate(hp_a, costh, -sinth)

        self.h = abs(hp_b[1])

        rp1 = [-l / 2, -self.h]
        rp2 = [l / 2, -self.h]
        rp3 = [l / 2, self.h]
        rp4 = [-l / 2, self.h]

        rp1_a = rotate(rp1, costh, sinth)
        rp2_a = rotate(rp2, costh, sinth)
        rp3_a = rotate(rp3, costh, sinth)
        rp4_a = rotate(rp4, costh, sinth)

        self.rp1 = parallel(rp1_a, mx, my)
        self.rp2 = parallel(rp2_a, mx, my)
        self.rp3 = parallel(rp3_a, mx, my)
        self.rp4 = parallel(rp4_a, mx, my)

class StrEnum(str,Enum):
    def _generate_next_value_(name,start,count,last_value):
        return name
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name

class StateEnum(StrEnum):
        INIT = auto()
        POINTREADY = auto()
        LINEREADY = auto()
        MODIFY = auto()


