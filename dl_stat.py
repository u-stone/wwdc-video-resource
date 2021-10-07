#-*- coding:utf-8 -*-
import os, io, sys, re
sys.path.append(".")
import dl_config


def isValideFile(path):
    return True

def addPath(name, depth):
    if not os.path.exists(dl_config.statPath):
        ps.path.mkdir(dl_config.statPath)

    filePath = dl_config.statPath + "/" + "downloaded_video.txt"
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
        elif os.path.isfile(path) and (os.path.splitext(path)[1] == ".mp4" or os.path.splitext(path)[1] == ".pdf"):
            if isValideFile(path):
                addPath(item, depth)
        else:
            pass



if __name__ == '__main__':
    print("start")
    stat(dl_config.basePath, 1)
    print("finished")


