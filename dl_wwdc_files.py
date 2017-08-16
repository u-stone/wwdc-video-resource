import os, time
import urllib3
import lxml, json

base_path = "/Users/ustone/WWDC/"

def read_json_file(path):
    ret = (False, "", "", "", "")
    if not os.path.isfile(path):
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
    for item in os.listdir(base_path):
        path = os.path.join(base_path, item)
        if os.path.isdir(path):
            dl_start(path)
        elif os.path.isfile(path) and os.path.splitext(path)[1] == ".json":
            ret = read_json_file(path)
            if len(ret) == 5 and ret[0]:
                # 视频的下载
                dl_file_frome_web(ret[1], ret[2], 1, path)
                # pdf的下载
                dl_file_frome_web(ret[3], ret[4], 2, path)
        else:
            print "this is not a directory or a file: ", path


if __name__ == '__main__':
    print "start to download videos and pdfs: "
    dl_start(base_path)
    print "done"

