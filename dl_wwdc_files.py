# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import os, time, threading
from datetime import datetime
import json
import shutil
import certifi, urllib3
import sys
sys.path.append(".")
import dl_config
from urllib.request import urlopen

desc_stat = {}
title_stat = {}
count = 0
count_dl = 0
video_tag = "hd_video"
kws = ["WKWebView", "HTTP", "Safari", "Swift", "Energy", "Text", "VR", "Runtime", "Network", 
        "OpenCL", "OpenGL", "Xcode", "Optimization", "ML", "HEVC", "Multitasking", "Tools", 
        "Performance", "Fixing", "Optimize", "Techniques", "Affiliate", "LLVM", "Understanding", 
        "Introducing", "Cocoa", "Language", "Core Data", "SiriKit", "Touch Bar", "Drag and Drop",
        "Efficient", "Localization", "Deep Linking", "HEVC", "HEIF", "Efficiency", "HLS", "Privacy", 
        "HomeKit", "Grand Central Dispatch", "Networking", "Notifications", "Location", "File System",
        "Core NFC", "Neural Networks", "GCD", "CarPlay", "Internationalization", "Resources", "Auto Layout", 
        "Measurements", "Debugging", "System Trace", "Sanitizer", "Time Profiler", "Optimizing", "Metal", 
        "Rendering", "Core Image", "Speech Recognition", "Marvel", "Seamless", "in Depth", "Search", "Keychain",
        "Sandbox", ""]
# i made a mistake, i added a "" into kws, so i downloaded all videos and pdfs.

download_tasks = []
task_failed = {}
thread_count = 16

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

    if not "dl_pdf" in data: 
        if "pdf" in data:
            pdf_url = data["pdf"]
    if not "dl_video" in data:
        if video_tag in data:
            video_url = data[video_tag]

    path = path[:-5]

    if video_url == "" and pdf_url == "":
        return ret

    # if not video_url == "":
    #     print("re-download :", video_url, " to ", path+".mp4", " current size", file_size_string(path+".mp4"))
    # if not pdf_url == "":
    #     print("re-download :", pdf_url, " to ", path+".pdf", " current size", file_size_string(path+".pdf"))
    
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

def set_video_file_size(path, size):
    json_string = ""
    with open(path, "r") as pf:
        json_string = pf.read()

    with open(path, "w+") as pf:
        if not json_string:
            return

        data = json.loads(json_string)
        if video_tag == "hd_video":
            data["hd_video_size"] = size
        elif video_tag == "sd_video":
            data["sd_video_size"] = size
        else:
            return

        pf.write(json.dumps(data))

def get_video_file_size(path):
    size = 0
    with open(path, "r") as pf:
        data = json.loads(pf.read())
        
        if video_tag == "hd_video" and "hd_video_size" in data.keys():
            size = int(data["hd_video_size"])
        elif video_tag == "sd_video" and "sd_video_size" in data.keys():
            size = int(data["sd_video_size"])
        else:
            pass
    
    return size

def kws_lower():
    tmp = []
    global kws
    for item in kws:
        tmp.append(item.lower())
    kws = tmp

def check_kw(string):
    lowString = string.lower()
    for key in kws:
        if key in lowString:
            return True
    
    return False

def startTasks():
    print("total task is ", len(download_tasks))
    threads = []
    for index in range(thread_count):
        t = threading.Thread(None, workThread, "download_from_web", (index,))
        print("thread ", index + 1, " startting")
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    print("all thread done")

def addTask(url, path, file_type, mark_file_path):
    if len(url) == 0:
        return
    task = (url, path, file_type, mark_file_path)
    download_tasks.append(task)
    return

def workThread(thread_index):
    num = len(download_tasks)
    if thread_index >= num:
        return

    single_task_count = num // thread_count
    last_task_added = num % thread_count
    start_index = thread_index * single_task_count
    end_index = start_index + single_task_count

    if single_task_count == 0:
        start_index = thread_index
        end_index = start_index + 1

    msg = "======> thread " + str(thread_index) + " started : start index " + str(start_index) + " end: " + str(end_index) + "====="
    print(msg)

    if thread_index == thread_count - 1:
        end_index += last_task_added
    
    for index in range(start_index, end_index):
        task_data = download_tasks[index]
        print(datetime.today().strftime('[%Y-%m-%d-%H:%M:%S]'), " thread ", thread_index, " working")
        while True:
            if dl_file_frome_web(task_data[0], task_data[1], task_data[2], task_data[3]):
                break
            
    

def dl_file_frome_web(url, path, file_type, mark_file_path):
    global count_dl

    if not url:
        return True
    if url[:4].lower() != "http":
        print(url, " is not a standard url")
        return True

    file_size = get_video_file_size(mark_file_path)
    # if file size is unkown(0), so we get it with urlopen
    if (file_size == 0): 
        file_size = int(urlopen(url).info().get('Content-Length', -1))
        set_video_file_size(mark_file_path, file_size)

    if os.path.exists(path): 
        first_byte = os.path.getsize(path)
    else:
        first_byte = 0
    header = {"Range": "bytes=%s-%s" % (first_byte, file_size)}

    print('== start  == ', os.path.basename(path), ' start pos: ', format_size(first_byte), ' whole size: ', format_size(file_size))

    time_start = time.time()
    pool = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    chunk_size = 65536
    resource = pool.request('GET', url, preload_content=False, headers=header)
    with open(path, 'ab') as outfile:
        while True:
            data = resource.read(chunk_size)
            if not data:
                break
            outfile.write(data)
    resource.release_conn()
    content_bytes = resource.headers.get('Content-Length')

    size = os.path.getsize(path)
    if content_bytes and size < int(content_bytes):
        task_failed[path] = url
        print('== failed == ', os.path.basename(path), ' not full downloaded', ' original size = ', format_size(content_bytes), ' downloaded size = ', format_size(size))
        return False

    mark_as_finished(mark_file_path, file_type)
    count_dl += 1
    
    timeInterval = time.time() - time_start
    print("== suc    == ", os.path.basename(path), " ", timeInterval, "seconds, file size: ", file_size_string(path), ", average speed: ", getSpeedString(path, timeInterval))
    return True

def format_size(size):
    size_string = ""
    size_value = int(size)
    if size_value > 1000000:
        size_value /= 1000000
        size_string = str(size_value) + " MB"
    elif size_value > 1000:
        size_value /= 1000
        size_string = str(size_value) + " KB"
    else:
        size_string = str(size_value) + "B"
    return size_string

def file_size_string(path):
    if not os.path.exists(path):
        return "none"
    return format_size(os.path.getsize(path))

def getSpeedString(path, timeInterval):
    if (not os.path.exists(path)) or (not os.path.isfile(path)):
        return "0 B/s (path error)"

    speedString = ""

    fileSize = os.path.getsize(path)
    fileSize /= timeInterval
    
    if fileSize > 1000000000:
        fileSize /= 1000000000
        speedString = str(fileSize) + " GB/s"
    elif fileSize > 1000000:
        fileSize /= 1000000
        speedString = str(fileSize) + " MB/s"
    elif fileSize > 1000:
        fileSize /= 1000
        speedString = str(fileSize) + " KB/s"
    else:
        speedString = str(fileSize) + " B/s"

    return speedString

def get_all_tasks(base_path):
    global count
    for item in os.listdir(base_path):
        path = os.path.join(base_path, item)
        if os.path.isdir(path):
            get_all_tasks(path)
        elif os.path.isfile(path) and os.path.splitext(path)[1] == ".json":
            count += 1
            ret = read_json_file(path)
            if len(ret) == 5 and ret[0]:
                if not check_kw(item):
                    continue
                # download video
                addTask(ret[1], ret[2], 1, path)
                # download pdf
                addTask(ret[3], ret[4], 2, path)
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
    global title_stat
    global desc_stat
    global task_failed
    save_json(dl_config.basePath, "title_stat", json.dumps(title_stat))
    save_json(dl_config.basePath, "desc_stat", json.dumps(desc_stat))
    save_json(dl_config.basePath, "failed_task", json.dumps(task_failed))

    title_stat = {}
    desc_stat = {}
    task_failed = {}
    
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
    stat_category(dl_config.basePath)

    get_all_tasks(dl_config.basePath)

    while (len(download_tasks) > 0) :
        startTasks()
        print("total file number is: ", count)

        output_stat()
        print("download files: ", count_dl)
        print("done, time spend:", time.time() - time_start, " seconds")

        get_all_tasks(dl_config.basePath)


    

