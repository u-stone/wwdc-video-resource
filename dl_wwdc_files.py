# -*- coding: utf-8 -*-

import os, time
import urllib3
import lxml, json

base_path = "/Users/ustone/WWDC/"
desc_stat = {}
title_stat = {}
count = 0

def read_json_file(path):
    ret = (False, "", "", "", "")
    if not os.path.isfile(path):
        return ret
    print "read file: ", path
    return ret
    data = {"":""}
    with open(path, "r") as pf:
        json_string = pf.read()
        data = json.loads(json_string)

    if len(data) == 0 :
        return ret
    
    dl_finish = 0
    video_url = ""
    pdf_url = ""

    if not (data.has_key("dl_pdf") and data["dl_pdf"] == "1"):
        pdf_url = data["pdf"]
    if not (data.has_key("dl_video") and data["dl_video"] == "1"):
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
            print "open file exception:", path

    if len(data) == 0 :
        return ret

    for tag in tags:
        if data.has_key(tag):
            ret.append(data[tag])
        else:
            ret.append("")

    return ret

def mark_as_finished(path, file_type):
    json_string = ""
    with open(path, "r") as pf:
        json_string = pf.read()

    with open(path, "w+") as pf:
        if len(json_string) == 0:
            return

        data = json.loads(json_string)
        if file_type == 1:
            data["dl_video"] = "1"
        elif file_type == 2:
            data["dl_pdf"] = "1"
        else:
            return

        pf.write(json.dumps(data))

def dl_file_frome_web(url, path, file_type, mark_file_path):
    print "download file from: ", url, "and save to:", path
    if len(url) == 0:
        return

    if os.path.exists(path):
        print "file ", path, "is existed, won't download again."
        return

    time_start = time.time()
    pool = urllib3.PoolManager()
    r = pool.request('GET', url, preload_content = False)

    with open(path, 'wb') as pf:
        while True:
            data = r.read(10240)
            if not data:
                break
            pf.write(data)
    r.release_conn()
    mark_as_finished(mark_file_path, file_type)

    print "download file form:", url, "finished, spend time for ", time.time() - time_start, "seconds"
    return


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
                # download video
                dl_file_frome_web(ret[1], ret[2], 1, path)
                # download pdf
                dl_file_frome_web(ret[3], ret[4], 2, path)
        else:
            print "this is not a directory nor a json file: ", path

    return

def stat_category(base_path):
    global count
    for item in os.listdir(base_path):
        path = os.path.join(base_path, item)
        if os.path.isdir(path):
            stat_category(path)
        elif os.path.isfile(path) and os.path.splitext(path)[1] == ".json":
            print "processing file ", path
            count += 1
            ret = read_json_info(path, ["title","describe"])
            if len(ret) == 2:
                add_title(ret[0])
                add_desc(ret[1])
        else:
            print "this is not a directory nor a json file: ", path   

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
    print "title statistics：", title_stat
    print "description statistics: ", desc_stat
    """

    save_json(base_path, "stat", json.dumps(title_stat) + "\n" + json.dumps(desc_stat))
    return


def add_title(title_string):
    title_parse = title_string.split()
    for string in title_parse:
        if not title_stat.has_key(string):
            title_stat[string] = 1
        else:
            title_stat[string] = title_stat[string] + 1

    return

def add_desc(desc_string):
    desc_parse = desc_string.split()
    for string in desc_parse:
        if not desc_stat.has_key(desc_string):
            desc_stat[string] = 1
        else:
            desc_stat[string] = desc_stat[string] + 1
    return


if __name__ == '__main__':
    global count
    print "start to download videos and pdfs: "
    time_start = time.time()
    stat_category(base_path)
    dl_start(base_path)
    print "total file number is: ", count

    output_stat()
    print "done, time spend:", time.time() - time_start, " seconds"

