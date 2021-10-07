# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
"""
this script collection urls
"""
import re
import os
import json
import threading
import time
import requests
from lxml import etree
from pathlib import Path
import dl_config

tlock = threading.Lock()
dlock = threading.Lock()
all_video_names = []
urls_failed = []

def save_json(ori_path, ori_filename, content):
    path=""
    invalid_char="\".?"
    for c in ori_path:
        if invalid_char.find(c) != -1:
            continue
        path += c
    if not os.path.exists(path):
        os.makedirs(path)
    # 需要注意filename中带有/字符串
    filename=""
    for c in ori_filename:
        if invalid_char.find(c) != -1:
            continue
        filename += c
    path = path + "/" + filename + ".json"

    tlock.acquire()
    with open(path, "w+") as pf:
        pf.write(content)
    tlock.release()
    return

def page_wwdc_single(year, url):
    # 遍历得到每一个视频的页面
    page_content = page_dl(url)
    if not page_content:
        return ""

    nodes = page_main_nodes(page_content)
    save_json(dl_config.basePath, year, json.dumps(nodes))

    print_obj("start to download WWDC-", year)

    for (category_name, video_info) in nodes.items():
        # if "Developer Tools" != category_name:
        #     continue
        page_category(year, category_name, video_info)

    print_obj("WWDC"+year, " download finished...")
    return ""

def page_wwdc_multithead(year, url):
    # 遍历得到每一个视频的页面
    page_content = page_dl(url)
    if not page_content:
        return

    nodes = page_main_nodes(page_content)
    save_json(dl_config.basePath, year, json.dumps(nodes))

    category_threads = []
    for (category_name, video_info) in nodes.items():
        t = threading.Thread(None, page_category, "category-page-download", (year, category_name, video_info))
        category_threads.append(t)
        t.start()
        print_obj("start thread: "+year, category_name)


    for thread in category_threads:
        thread.join()

    print_obj("WWDC"+year, " download finished...")

    return

def page_category(year, category_name, video_info):
    for video_tuple in video_info:
        if len(video_tuple) == 4:
            page_detail(year, category_name,
                        video_tuple[0], video_tuple[1], video_tuple[2], video_tuple[3])
    return

def page_main_nodes(pageContent):
    # 得到全部大的节点
    dom = etree.HTML(pageContent)
    collection_focus_groups = dom.xpath('/html/body/main/section[3]/ul')
    base_url = "https://developer.apple.com"
    category_url = {}

    # 实际上collection_focus_groups只有一个元素
    for collection_group in collection_focus_groups:
        # 得到所有大类，比如说core-os， frameworks...
        collection_items = collection_group.xpath('li')
        for group in collection_items:
            # 得到每一个细分类中的元素名称和对应详细页面的URL，准备保存下来后续打开
            #print(group.text, group.tag)
            # /html/body/main/section[3]/ul/li[1]/section/section/section/section/span/span
            # /html/body/main/section[3]/ul/li[1]/ul/li[1]/section/section/section[2]
            names = group.xpath('section/section/section/section/span/span')
            if not names:
                continue

            category_name = names[0].text
            addNameString(category_name)

            video_items = group.xpath('ul/li')
            video_urls = []
            for video_item in video_items:
                video_name = video_item.xpath('./section/section/section/a/h4')
                video_url  = video_item.xpath('./section/section/section/a/@href')
                pos = video_url[0][1:-1].rindex('/') + 2
                video_tag_event = video_url[0][pos:len(video_url[0])-1]
                video_tag_focus = video_item.xpath('.//li[@class="video-tag focus"]/span')

                if len(video_name) == 1 and len(video_url) >= 1 and len(video_tag_event) >= 1:
                    # 保证一个视频名称对应一个URL
                    url = base_url + video_url[0]
                    url_dic = (video_tag_focus[0].text, video_tag_event, video_name[0].text, url)
                    video_urls.append(url_dic)
                    addNameString(video_name[0].text)
                # else:
                #     # 2015开始有变化
                #     video_name = video_item.xpath('./section/section/section[2]/a/h4')
                #     video_url = video_item.xpath('./section/section/section[2]/a/@href')
                #     video_tag_event = video_item.xpath('./section/section/section/ul/li[@class="video-tag event"]/span')
                #     if len(video_name) == 1 and len(video_url) == 1 and len(video_tag_event) == 1:
                #         # 保证一个视频名称对应一个URL
                #         url = base_url + video_url[0]
                #         url_dic = (video_tag_focus[0].text, video_tag_event[0].text, video_name[0].text, url)
                #         video_urls.append(url_dic)

                if not video_name:
                    addNameString(video_name[0].text)

            category_url[category_name] = video_urls
            #print(category_url)

    return category_url

def page_detail(year, category_name, video_tag_focus, video_tag_event, video_name, url):
    # 在wwdc的主页上得到全部节目的列表，然后分层次下载
    print_obj("downloading page: ", url)

    # if video_tag_event != '10017':
    #     return

    page_content = page_dl(url)
    if not page_content:
        return ""

    dom = etree.HTML(page_content)
    title = dom.xpath('//*[@id="main"]/section[2]/section[2]/section/ul/li[1]/h1')
    describe = dom.xpath('//*[@id="main"]/section[2]/section[2]/section/ul/li[1]/p[1]/text()')

    hd_video_url = dom.xpath('//*[@id="main"]/section[2]/section[2]/section/ul/li[1]/ul/li[@class="download"]/ul/li[1]/a/@href')
    sd_video_url = dom.xpath('//*[@id="main"]/section[2]/section[2]/section/ul/li[1]/ul/li[@class="download"]/ul/li[2]/a/@href')
    

    if not title or not describe or not sd_video_url or not hd_video_url:
        return ""

    pdf_url = ""
    resources_urls = dom.xpath('//*[@id="main"]/section[2]/section[2]/section/ul/li[1]/ul[1]')
    if len(resources_urls) == 0:
        print('resources link not found')
    for url_inner in resources_urls:
        resource_list = url_inner.xpath('./li/a')
        for resource in resource_list:
            text = resource.text
            if text.lower() == "Presentation Slides (PDF)".lower():
                pdf_url = resource.xpath('./@href')[0]
                break

    name = title[0].text

    if video_name.lower() != name.lower():
        print("we get title：", name, "but we want：", video_name)
        print("open page failed, URL: ", url)
        addFailedURL(url)
        return ""

    content = { "title": name,
                "describe": describe[0],
                "video_tag_focus": video_tag_focus,
                "video_tag_event": video_tag_event,
                "sd_video": sd_video_url[0],
                "hd_video": hd_video_url[0],
                "pdf": pdf_url }

    category_name = getValidPathStr(category_name)
    # prefix_len = len("Session ")
    # video_tag_event = video_tag_event[prefix_len:]
    video_name = "[" + year + " - " + video_tag_event + "] " + video_name
    video_name = getValidPathStr(video_name)
    path = dl_config.basePath + year + "/" + category_name + "/" + video_name
    save_json(path, video_name, json.dumps(content))

    return url

def page_dl(url):
    page_content = ""
    try:
        page_content = requests.get(url, timeout=60).content.decode("utf8")
    except requests.exceptions.ConnectTimeout:
        print("network connect failed")
    except requests.exceptions.Timeout:
        print("open: ", url, " time-out")

    return page_content

def getValidPathStr(string):
    if string.find("/") != -1:
        string = string.replace("/", "-")
    if string.find(":") != -1:
        string = string.replace(":", "-")
    if string[-1] == ' ':
        string = string[0:-1]
    return string

def addNameString(name):
    dlock.acquire()
    all_video_names.append(name)
    dlock.release()
    return

def addFailedURL(url):
    dlock.acquire()
    urls_failed.append(url)
    dlock.release()
    return

def printFailedURL():
    if not urls_failed:
        print("no failed url")
    else:
        print("failed url number is ", len(urls_failed))

def print_obj(msg, obj):
    tlock.acquire()
    print(msg, obj)
    tlock.release()
    return

def analyzeNames():
    char_dic = {}
    for name in all_video_names:
        for c in name:
            if c in char_dic:
                char_dic[c] = char_dic[c] + 1
            else:
                char_dic[c] = 1
    #print("所有字符的特征: ", json.dumps(char_dic))
    save_json(dl_config.basePath, "char", json.dumps(char_dic))


if __name__ == '__main__':
    print("start")
    time_start = time.time()
    urls = {
            "2013": "https://developer.apple.com/videos/wwdc2013/",
            "2014": "https://developer.apple.com/videos/wwdc2014/",
            "2015": "https://developer.apple.com/videos/wwdc2015/",
            "2016": "https://developer.apple.com/videos/wwdc2016/",
            "2017": "https://developer.apple.com/videos/wwdc2017/",
            "2018": "https://developer.apple.com/videos/wwdc2018/",
            "2019": "https://developer.apple.com/videos/wwdc2019/",
            "2020": "https://developer.apple.com/videos/wwdc2020/",
            "2021": "https://developer.apple.com/videos/wwdc2021/"
            }


    threads = []
    for year, url in urls.items():
        t = threading.Thread(None, page_wwdc_single, "page_wwdc_single", (year, url))
        threads.append(t)
        t.start()

    for thread in threads:
        thread.join()

    analyzeNames()
    printFailedURL()

    print("done, use time(second)：", time.time() - time_start)