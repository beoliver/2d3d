#! /usr/bin/env python3

#  2d3d - merge two 2d images in a 3d space.
#  Copyright (C) 2015  Benjamin Edward Oliver
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

from random import shuffle
from os.path import basename
from sys import argv
from PIL import Image
from collections import defaultdict, namedtuple
from itertools import islice, cycle

Point  = namedtuple('Point', ['point','colorID'])
Points = namedtuple('Points', ['pointX', 'pointY', 'pointZ','colorX', ])

def stringVertices(x,y,z):
    """returns a string representation of min required vertices"""
    x1 = x+1
    y1 = y+1
    z1 = z+1
    vertices = [(x1,y,z),(x1,y1,z),(x1,y,z1),(x1,y1,z1),(x,y,z1),(x,y1,z1)]
    return '\n'.join(map(lambda v: ' '.join(map(str,('v',) + v)), vertices))+'\n'


def stringFaces(n, colorXstring, colorZstring):
    """where n is a multiple of 6"""
    x  = ('f',n+2,n+4,n+5,n+3)
    z  = ('f',n,n+2,n+3,n+1)
    return '\n'.join(["usemtl " + colorXstring,
                      ' '.join(map(str,x)),
                      "usemtl " + colorZstring,
                      ' '.join(map(str,z))])+'\n'


def mtlStringRGB(rgbVal,colorString):
    kd = "Kd " + ' '.join(map(lambda x: str(x/255), list(rgbVal)))
    xs = ["newmtl " + colorString,
          "Ns 100",
          kd,
          "Ks 1 1 1",
          "Ka 0 0 0",
          "Ni 1","d 1",
          "illum 1"]
    return '\n'.join(xs) + '\n\n'


# returns a dict that has y vals as keys with vals of lists [ Point(point=Int,colorID=String) ]
def readPoints(image, colorMapPointer, ignore=(255,255,255)):
    mode     = image.mode
    (mX,mY)  = image.size
    pix      = image.load()
    d        = defaultdict(list)
    stringID = str(id(image))
    for y in range(mY):
        for x in range(mX):
            color = pix[x,y]
            if color != ignore:
                if color not in colorMapPointer:
                    colorMapPointer[color] = stringID + str(y) + str(x)
                d[mY-1-y].append(Point(x, colorMapPointer[color]))
    return d


# returns a dict that has (x,y,z) vals as keys with (colorIDx,colorIDy) as vals
def mergePoints(pointsX, pointsZ):
    mergedPoints = {}
    for (y,xPoints) in pointsX.items():
        if y in pointsZ:
            zPoints = pointsZ.get(y)
            mx = max(len(xPoints),len(zPoints))
            for (x,z) in islice(zip(cycle(xPoints), cycle(zPoints)), mx):
                mergedPoints[(x.point, y, z.point)] = (x.colorID, z.colorID)
    return mergedPoints



def mergePointsRandom(pointsX, pointsZ):
    mergedPoints = {}
    for (y,xPoints) in pointsX.items():
        if y in pointsZ:
            zPoints = pointsZ.get(y)
            mx = max(len(xPoints),len(zPoints))
            xs = list(islice(cycle(xPoints),mx))
            ys = list(islice(cycle(zPoints),mx))
            shuffle(xs)
            shuffle(ys)
            for (x,z) in zip(xs,ys):
                mergedPoints[(x.point, y, z.point)] = (x.colorID, z.colorID)
    return mergedPoints


# mtlWriter only needs the COLORDICT
def mtlWriter(filepath, colorDict):
    with open(filepath+".mtl",'w') as openfile:
        for (rgb,code) in colorDict.items():
            openfile.write(mtlStringRGB(rgb,code))


def objWriter(filepath, mergedPoints):
    index = 1
    with open(filepath+".obj", 'w') as openfile:
        openfile.write("mtllib " + basename(filepath) + ".mtl\n")
        for (x,y,z) in mergedPoints.keys():
            openfile.write(stringVertices(x,y,z))
        for (colorIDx, colorIDz) in mergedPoints.values():
            openfile.write(stringFaces(index, colorIDx, colorIDz))
            index += 6


def run(fileA,fileB,outpath):
    colorDict = {}
    imgA = Image.open(fileA).convert('RGB')
    imgB = Image.open(fileB).convert('RGB')
    d1 = readPoints(imgA, colorDict)
    d2 = readPoints(imgB, colorDict)
    merged = mergePointsRandom(d1,d2)
    # write mtl file
    mtlWriter(outpath, colorDict)
    objWriter(outpath, merged)


if __name__ == '__main__':

    a = argv[1]
    b = argv[2]
    out = argv[3]

    run(a,b,out)
