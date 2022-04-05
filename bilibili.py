import json
import requests
import re
import subprocess
# import urllib3
# urllib3.disable_warnings()


"""
ffmpeg 很强，可以拆分音视频，合并音视频等等，但要自己下载，配置环境变量
提取音频命令： ffmpeg -i mp4 -f mp3 output_file
音视频合并命令：ffmpeg -i mp4 -i mp3 -strict -2 -f mp4 output_file  # 超级慢
            ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac output.mp4
试了下，最简单最快的：  ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac output.mp4  # 直接复制音视频塞一起
"""

url = 'https://www.bilibili.com/video/BV1fV41147Ck'
url = 'https://www.bilibili.com/video/BV1hZ4y1m7CU?spm_id_from=333.851.b_7265636f6d6d656e64.3'

headers = {
    'origin': 'https://www.bilibili.com',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Edg/91.0.864.41',
    'referer': 'https://www.bilibili.com/',
}


def get_info(html_url):
    r = requests.get(html_url, headers)
    reg = re.compile('<script>window.__playinfo__=(.*?)</script>')
    html_data = reg.findall(r.text)
    data = json.loads(html_data[0])

    title = re.findall('<meta data-vue-meta="true" itemprop="name" name="title" content="(.*?)">', r.text)[0]
    audio = data['data']['dash']['audio'][0]['baseUrl']
    video = data['data']['dash']['video'][0]['baseUrl']

    info = {
        'title': title,
        'audio': audio,
        'video': video
    }
    print(info)
    return info


info = get_info(url)

# ------------------------下载视频------------------------------------------------------

''' 花里胡哨反而不行, 或者说不能stream
with open('demo.mp4', 'wb') as f:
    f.write(requests.get(info['video'], headers, stream=True, verify=False).content)

with open('demo.mp3', 'wb') as f1:
    f.write(requests.get(info['audio'], headers, stream=True, verify=False).content)
'''

'''
Range头域
Range头域可以请求实体的一个或者多个子范围。例如，
表示头500个字节：bytes=0-499
表示第二个500字节：bytes=500-999
表示最后500个字节：bytes=-500
表示500字节以后的范围：bytes=500-
第一个和最后一个字节：bytes=0-0,-1      ------- # 为什么我0-1，-1 可以，bytes=却不行？
同时指定几个范围：bytes=500-600,601-999

作者：苍简
链接：https://www.jianshu.com/p/331aa20937ba
来源：简书
著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
'''


def download_range(fp, url):
    # 如果download不行了，一个就可以用这个了
    begin = 0
    end = 0
    with open(fp, 'ab') as f:
        # 如果不识别416状态的话，他会一直请求，但是返回不了内容，进入死循环
        # 416:请求的范围超出资源，即到了末尾，不要end了
        while True:
            begin = end +1
            end += 1024**2
            headers.update({'Range': f'bytes={begin}-{end}'})
            r = requests.get(url=url, headers=headers)
            print(r.status_code)
            if r.status_code == 416:
                headers.update({'Range': f'bytes={begin}-'})
                r = requests.get(url=url, headers=headers)
                f.write(r.content)
                print(begin, end)
                break
            print(begin, end)
            f.write(r.content)


# download_range(info['title']+'.mp4', info['video'])
# ? 怎么不用分段也可以了？？


def download(fp, url):
    r = requests.get(url=url, headers=headers)
    with open(fp, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024**2):
            f.write(chunk)


download(info['title']+'_video.mp4', info['video'])
download(info['title']+'_audio.mp3', info['audio'])

subprocess.call(f"ffmpeg -i \"{info['title']+'_video.mp4'}\" -i \"{info['title']+'_audio.mp3'}\" -c:v copy -c:a copy \"{info['title']+'.mp4'}\"")
