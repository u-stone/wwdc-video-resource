# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import os, time
import json
import shutil
import certifi, urllib3

base_path = "G:/WWDC2/"
desc_stat = {}
title_stat = {}
count = 0
count_dl = 0
kws = ["WKWebView", "HTTP", "Safari", "Swift", "Energy", "Text", "VR", "Runtime", "Network", 
        "OpenCL", "OpenGL", "Xcode", "Optimization", "ML", "HEVC", "Multitasking", "Tools", 
        "Performance", "Fixing", "Optimize", "Techniques", "Affiliate"]

def read_json_file(path):
    ret = (False, "", "", "", "")
    if not os.path.isfile(path):
        return ret

    data = {"":""}
    with open(path, "r") as pf:
        json_string = pf.read()
        try:
            data = json.loads(json_string)
        except BaseException:
            print("open file exception:", path)

    if not data:
        return ret
    
    dl_finish = 0
    video_url = ""
    pdf_url = ""

    if not (("dl_pdf" in data) and (data["dl_pdf"] == "1")):
        if "pdf" in data:
            pdf_url = data["pdf"]
    if not (("dl_video" in data) and (data["dl_video"] == "1")):
        if "sd_video" in data:
            video_url = data["sd_video"]    
    if video_url == "" and pdf_url == "":
        return ret

    path = path[:-5]
    return (True, video_url, path+".mp4", pdf_url, path+".pdf")

def read_json_info(path, tags):
    ret = []
    if not os.path.exists(path):
        return ret

    data = {}
    with open(path, "r") as pf:
        try:
            json_string = pf.read()
            data = json.loads(json_string)
        except BaseException:
            print("open file exception:", path)

    if not data:
        return ret

    for tag in tags:
        if tag in data:
            ret.append(data[tag])
        else:
            ret.append("")

    return ret

def mark_as_finished(path, file_type):
    json_string = ""
    with open(path, "r") as pf:
        json_string = pf.read()

    with open(path, "w+") as pf:
        if not json_string:
            return

        data = json.loads(json_string)
        if file_type == 1:
            data["dl_video"] = "1"
        elif file_type == 2:
            data["dl_pdf"] = "1"
        else:
            return

        pf.write(json.dumps(data))

def kws_lower():
    tmp = []
    global kws
    for item in kws:
        tmp.append(item.lower())
    kws = tmp

def check_kw(string):
    words = string.split()
    for word in words:
        if kws.count(word.lower()) > 0:
            return True
    
    return False

def dl_file_frome_web(url, path, file_type, mark_file_path):
    global count_dl
    count_dl += 1

    if not url:
        return
    
    print("download file from: ", url, "and save to:", path)

    time_start = time.time()
    pool = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    http = pool.request('GET', url, preload_content = False)

    with pool.request('GET', url, preload_content=False) as resource, open(path, 'wb') as outfile:
        shutil.copyfileobj(resource, outfile)
    #http.release_conn()

    mark_as_finished(mark_file_path, file_type)

    print("spend time for ", time.time() - time_start, "seconds, file size: ", file_size_string(path))
    return

def file_size_string(path):
    if not os.path.exists(path):
        return "none"
    size_string = ""
    size = os.path.getsize(path)
    if size > 1000000:
        size /= 1000000
        size_string = str(size) + " MB"
    elif size > 1000:
        size /= 1000
        size_string = str(size) + " KB"
    else:
        size_string = str(size) + "B"

    return size_string

def dl_start(base_path):
    global count
    for item in os.listdir(base_path):
        path = os.path.join(base_path, item)
        if os.path.isdir(path):
            dl_start(path)
        elif os.path.isfile(path) and os.path.splitext(path)[1] == ".json":
            count += 1
            ret = read_json_file(path)
            if len(ret) == 5 and ret[0]:
                if not check_kw(item):
                    continue
                # download pdf
                dl_file_frome_web(ret[3], ret[4], 2, path)
                # download video
                dl_file_frome_web(ret[1], ret[2], 1, path)
        else:
            pass
            #print("this is not a directory nor a json file: ", path)

    return

def stat_category(base_path):
    global count
    for item in os.listdir(base_path):
        path = os.path.join(base_path, item)
        if os.path.isdir(path):
            stat_category(path)
        elif os.path.isfile(path) and os.path.splitext(path)[1] == ".json":
            #print("processing file ", path)
            count += 1
            ret = read_json_info(path, ["title","describe"])
            if len(ret) == 2:
                add_title(ret[0])
                add_desc(ret[1])
        else:
            pass
            #print("this is not a directory nor a json file: ", path)

    return

def save_json(path, filename, content):
    if not os.path.exists(path):
        os.makedirs(path)
    path = path + "/" + filename + ".json"

    with open(path, "w+") as pf:
        pf.write(content)

    return

def output_stat():
    """
    print("title statistics：", title_stat)
    print("description statistics: ", desc_stat)
    """

    save_json(base_path, "title_stat", json.dumps(title_stat))
    save_json(base_path, "desc_stat", json.dumps(desc_stat))
    
    return


def add_title(title_string):
    t = type(title_string)
    if not isinstance(title_string, str):
        return
    title_parse = title_string.split()
    for string in title_parse:
        if not string in title_stat:
            title_stat[string] = 1
        else:
            title_stat[string] = title_stat[string] + 1

    return

def add_desc(desc_string):
    t = type(desc_string)
    if not isinstance(desc_string, str):
        return
    desc_parse = desc_string.split()
    for string in desc_parse:
        if not desc_string in desc_stat:
            desc_stat[string] = 1
        else:
            desc_stat[string] = desc_stat[string] + 1
    return


if __name__ == '__main__':
    #global count
    kws_lower()

    print("start to download videos and pdfs: ")
    time_start = time.time()
    stat_category(base_path)
    dl_start(base_path)
    print("total file number is: ", count)

    output_stat()
    print("download files: ", count_dl)
    print("done, time spend:", time.time() - time_start, " seconds")
    

