#-*- coding:utf-8 -*-
import os, io, sys, re


basePath = "G:/WWDC2"
statPath = "G:/WWDC2"

def isValideFile(path):
    return True

def addPath(name, depth):
    if not os.path.exists(statPath):
        ps.path.mkdir(statPath)

    filePath = statPath + "/" + "downloaded_video.txt"
    with open(filePath, "a+") as pf:
        pf.write(name)
        pf.write("\n")

    return


def stat(rootPath, depth):
    depth = depth + 1
    for item in os.listdir(rootPath):
        path = os.path.join(rootPath, item)
        if os.path.isdir(path):
            stat(path, depth)
        elif os.path.isfile(path) and os.path.splitext(path)[1] == ".mp4":
            if isValideFile(path):
                addPath(item, depth)
        else:
            pass



if __name__ == '__main__':
    print("start")
    stat(basePath, 1)
    print("finished")


