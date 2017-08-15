# -*- coding: utf-8 -*-
import os
import sys
import urllib2
import requests
import re
import json
import threading
import time
from lxml import etree

tlock = threading.Lock()
dlock = threading.Lock()
basePath = "/Users/ustone/WWDC2/"

def save_json(path, filename, content):
    if not os.path.exists(path):
        os.makedirs(path)
    # 需要注意filename中带有/字符串
    path = path + "/" + filename + ".json"

    tlock.acquire()
    with open(path, "w+") as pf:
        pf.write(content)
    tlock.release()
    return

def page_wwdc_single(year, url):
    # 遍历得到每一个视频的页面
    page_content = page_dl(url)
    if len(page_content) == 0:
        return ""

    nodes = page_main_nodes(page_content)
    #save_json("/Users/ustone/wwdc", year, json.dumps(nodes))

    print_obj("准备开始下载WWDC-", year)

    for (category_name, video_info) in nodes.items():
        for video_tuple in video_info:
            page_detail(year, category_name, video_tuple[0], video_tuple[1], video_tuple[2])
    
    print_obj("WWDC"+year, "的数据下载完成")
    return ""

def page_wwdc_multithead(year, url):
    # 遍历得到每一个视频的页面
    page_content = page_dl(url)
    if len(page_content) == 0:
        return

    nodes = page_main_nodes(page_content)
    #save_json("/Users/ustone/wwdc", year, json.dumps(nodes))

    category_threads = []
    for (category_name, video_info) in nodes.items():
        t = threading.Thread(None, page_category, "category-page-download", (category_name, video_info))
        category_threads.append(t)
        t.start()
        print_obj("开启线程"+year, category_name)
        

    for thread in category_threads:
        thread.join()

    print_obj("WWDC"+year, "的数据下载完成")

    return url_main

def page_category(category_name, video_info):
    for video_tuple in video_info:
        page_detail(year, category_name, video_tuple[0], video_tuple[1], video_tuple[2])

def page_main_nodes(pageContent):
    # 得到全部大的节点
    dom = etree.HTML(pageContent)
    collections = dom.xpath('/html/body/section[4]/ul')
    base_url = "https://developer.apple.com"
    category_url = {}

    # 实际上collections只有一个元素
    for item in collections:
        # 得到所有大类，比如说core-os， frameworks...
        item_groups = item.xpath('li')
        for group in item_groups:
            # 得到每一个细分类中的元素名称和对应详细页面的URL，准备保存下来后续打开
            #print group.text, group.tag
            names = group.xpath('section/section/section/section/span/span')
            if len(names) == 0:
                continue

            category_name = names[0].text
            addNameString(category_name)

            video_items = group.xpath('ul/li')
            video_urls = []
            for video_item in video_items:
                # //*[@id="core-os"]/ul/li[1]/section/section/section/a/h4
                video_name = video_item.xpath('./section/section/section/a/h4')
                video_url  = video_item.xpath('./section/section/section/a/@href')
                video_tag_focus = video_item.xpath('.//li[@class="video-tag focus"]/span')

                if len(video_name) == 1 and len(video_url) == 1:
                    # 保证一个视频名称对应一个URL
                    url = base_url + video_url[0]
                    url_dic = (video_tag_focus[0].text, video_name[0].text, url)
                    video_urls.append(url_dic)
                    addNameString(video_name[0].text)
                else:
                    # 2015开始有变化
                    # //*[@id="app-frameworks"]/ul/li[1]/section/section/section[2]/a/h4
                    video_name = video_item.xpath('./section/section/section[2]/a/h4')
                    video_url  = video_item.xpath('./section/section/section[2]/a/@href')
                    # # //*[@id="app-frameworks"]/ul/li[1]/section/section/section[2]/ul/li[2]/span
                    if len(video_name) == 1 and len(video_url) == 1:
                        # 保证一个视频名称对应一个URL
                        url = base_url + video_url[0]
                        url_dic = (video_tag_focus[0].text, video_name[0].text, url)
                        video_urls.append(url_dic)

                if len(video_name) > 0:
                    addNameString(video_name[0].text)

            category_url[category_name] = video_urls
            #print category_url

    return category_url

def page_detail(year, category_name, video_tag_focus, video_name, url):
    # 在wwdc的主页上得到全部节目的列表，然后分层次下载
    print_obj("正在下载网页:", url)

    page_content = page_dl(url)
    if len(page_content) == 0:
        return ""

    dom = etree.HTML(page_content)
    title = dom.xpath('//*[@id="main"]/section[2]/section[2]/section/ul/li[1]/h1')
    describe = dom.xpath('//*[@id="main"]/section[2]/section[2]/section/ul/li[1]/p[1]/text()')

    hd_video_url = dom.xpath('//*[@id="main"]/section[2]/section[2]/section/ul/li[1]/ul/li[@class="download"]/ul/li[1]/a/@href')
    sd_video_url = dom.xpath('//*[@id="main"]/section[2]/section[2]/section/ul/li[1]/ul/li[@class="download"]/ul/li[2]/a/@href')
    pdf_url = dom.xpath('//*[@id="main"]/section[2]/section[2]/section/ul/li[1]/ul/li[@class="document"]/a/@href')

    if len(title) == 0 or len(describe) == 0 or len(sd_video_url) == 0 or len(hd_video_url) == 0 or len(pdf_url) == 0:
        return ""

    '''
    print title[0].text
    print describe[0]
    print sd_video_url[0]
    print hd_video_url[0]
    print pdf_url[0]
    '''

    name = title[0].text

    if video_name.lower() != name.lower():
        print "得到的标题是：", name, "但是要取的标题是：", video_name 
        print "打开页面失败URL: ", url
        return ""

    content = {"title": name, "describe": describe[0], "video_tag": video_tag_focus, "sd_video": sd_video_url[0], "hd_video": hd_video_url, "pdf": pdf_url}

    category_name = getValidPathStr(category_name)
    video_name = getValidPathStr(video_name)
    path = basePath + year + "/" + category_name + "/" + video_name
    save_json(path, video_name, json.dumps(content))

    return url

def page_dl(url):
    page_content = ""
    try:
        page_content = requests.get(url, timeout=60).content.decode("utf8")
    except requests.exceptions.ConnectTimeout:
        print "网络连接不通"
    except requests.exceptions.Timeout:
        print "打开:", url, " 超时了"
    
    return page_content

def getValidPathStr(str):
    if str.find("/") != -1:
        str = str.replace("/", "-")
    return str

all_video_names = []
def addNameString(name):
    dlock.acquire()
    all_video_names.append(name)
    dlock.release()
    return

def print_obj(msg, obj):
    tlock.acquire()
    print msg, obj
    tlock.release()
    return

def analyzeNames():
    char_dic = {}
    for name in all_video_names:
        for c in name:
            if char_dic.has_key(c):
                char_dic[c] = char_dic[c] + 1
            else:
                char_dic[c] = 1
    #print("所有字符的特征: ", json.dumps(char_dic))
    save_json("/Users/ustone/tmp", "char", json.dumps(char_dic))

if __name__ == '__main__':
    print "start"
    time_start = time.clock()
    urls = {"2013": "https://developer.apple.com/videos/wwdc2013/", 
            "2014": "https://developer.apple.com/videos/wwdc2014/", 
            "2015": "https://developer.apple.com/videos/wwdc2015/",
            "2016": "https://developer.apple.com/videos/wwdc2016/",
            "2017": "https://developer.apple.com/videos/wwdc2017/"}
    
    threads = []
    for year, url in urls.items():
        t = threading.Thread(None, page_wwdc_single, "page_wwdc_", (year, url))
        threads.append(t)
        t.start()

    for thread in threads:
        thread.join()

    analyzeNames()

    print "done, 用时：", time.clock() - time_start


