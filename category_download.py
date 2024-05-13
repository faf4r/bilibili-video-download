import requests
import re
import json
import os
import time
from loguru import logger
import sys

logger.add(
    sys.stdout,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
    # format="{message}",
)

reg = re.compile('<script>window.__playinfo__=(.*?)</script>')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
    'Origin': 'https://www.bilibili.com',
    'Referer': 'https://space.bilibili.com/',
    'Cookie': "=============填写你自己的cookie===========",
}

mid = '1803865534'  # up的uid


def merge(video_in, audio_in, out):
    os.system(f'ffmpeg -i "{video_in}" -i "{audio_in}" -c copy -y "{out}"')

def check(title):
    mode = re.compile(r'[\\/:*?"<>|]')
    new_name = re.sub(mode, '_', title)
    return new_name

def download_season(season_id, name, total, start_index=1):
    page_size = 100                         # 这里page_size不能太大，100是可以的
    page_max_num = total // page_size + (total%page_size!=0)   # 向上取整

    os.makedirs(f'video/{name}/', exist_ok=True)
    os.makedirs(f'audio/{name}/', exist_ok=True)
    os.makedirs(f'out/{name}/', exist_ok=True)

    archive_list = []
    for page_num in range(1, page_max_num+1):
        archive_list_url = f'https://api.bilibili.com/x/polymer/web-space/seasons_archives_list?mid={mid}&season_id={season_id}&sort_reverse=false&page_num={page_num}&page_size={page_size}'
        # logger.debug(archive_list_url)

        archive_res = requests.get(url=archive_list_url, headers=headers).json()
        archive_list.extend(archive_res['data']['archives'])
    archive_list = [(index+1, item) for index, item in enumerate(archive_list)]
    archive_list = archive_list[start_index-1:]
    # logger.debug(len(archive_list))

    for no, archive in archive_list:
        # logger.debug(no)
        aid = archive['aid']    # archive id
        bvid = archive['bvid']  # 视频号
        title = archive['title']# 视频标题
        title = check(title)
        # logger.debug(str(no), title)
        video_page_url = f'https://www.bilibili.com/video/{bvid}/'  # 结尾必须有/，不然cookie没用，出不了1080p
        print(f'\r进度: {no}/{total} {title} {video_page_url}', end='')
        # logger.debug(video_page_url)
        
        html = requests.get(url=video_page_url, headers=headers)
        data = reg.findall(html.text)[0]
        data = json.loads(data)
        # logger.debug(data)

        # with open('data.json', 'w', encoding='utf-8') as f:
        #     json.dump(data, f)

        video_url = data['data']['dash']['video'][0]['baseUrl']
        res = requests.get(video_url, headers=headers)
        with open(f'video/{name}/{no}_{title}.flv', 'wb') as f:
            f.write(res.content)

        audio_url = data['data']['dash']['audio'][0]['baseUrl']
        res = requests.get(audio_url, headers=headers)
        with open(f'audio/{name}/{no}_{title}.mp3', 'wb') as f:
            f.write(res.content)
        
        # merge(f'video/{name}/{no}_{title}.flv', f'audio/{name}/{no}_{title}.mp3', f'out/{name}/{no}_{title}.flv')
        time.sleep(1)
    print()


if __name__ == '__main__':
    series_page_num = 1
    series_list_url = f'https://api.bilibili.com/x/polymer/web-space/seasons_series_list?mid={mid}&page_num={series_page_num}&page_size=20' # 这里的page_size最大好像就这个

    seasons_list_json = requests.get(url=series_list_url, headers=headers).json()
    seasons_list = seasons_list_json['data']['items_lists']['seasons_list']

    # # 下载全部合集
    # for season in seasons_list:
    #     name = season['meta']['name']           # 合集名
    #     total = season['meta']['total']         # 合集总视频数
    #     season_id = season['meta']['season_id'] # 合集id
    #     print(name)

    #     download_season(season_id, name, total, 1)
    #     for file in os.listdir(f'./video/{name}'):
    #         file = file[:-4]
    #         merge(f'./video/{name}/{file}.flv', f'./audio/{name}/{file}.mp3', f'./out/{name}/{file}.flv')

    # 下载指定合集
    for season in seasons_list:
        name = season['meta']['name']           # 合集名
        total = season['meta']['total']         # 合集总视频数
        season_id = season['meta']['season_id'] # 合集id
        if season_id not in [2130269]:  # 注意是int型
            continue
        print(name)

        download_season(season_id, name, total, 1)
        for file in os.listdir(f'./video/{name}'):
            file = file[:-4]
            merge(f'./video/{name}/{file}.flv', f'./audio/{name}/{file}.mp3', f'./out/{name}/{file}.flv')
