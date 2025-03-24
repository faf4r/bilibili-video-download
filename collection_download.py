import os
import time
import re
import asyncio

import aiohttp
import aiofiles


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Origin": "https://www.bilibili.com",
    "Referer": "https://www.bilibili.com/",
    "Cookie": "哔哩哔哩的COOKIE",
}


# view_url = "https://api.bilibili.com/x/web-interface/view?bvid=BV1Qx411P7kW"
view_url = "https://api.bilibili.com/x/web-interface/view?bvid={bvid}"

# play_url = "https://api.bilibili.com/x/player/wbi/playurl?avid=1756738&bvid=BV1Qx411P7kW&cid=2789981"
play_url = "https://api.bilibili.com/x/player/wbi/playurl?avid={avid}&bvid={bvid}&cid={cid}&qn=80&fnver=0&fnval=4048&fourk=1&gaia_source=&from_client=BROWSER&is_main_page=true&need_fragment=false&isGaiaAvoided=false"

def merge(video_in, audio_in, out):
    os.system(f'ffmpeg -i "{video_in}" -i "{audio_in}" -c copy -y "{out}"')


def legal_name(title):
    mode = re.compile(r'[\\/:*?"<>|]')
    new_name = re.sub(mode, "_", title)
    return new_name


async def get_view_info(client, bvid):
    url = view_url.format(bvid=bvid)
    async with client.get(url) as resp:
        data = await resp.json()
        return data["data"]
    

async def get_play_info(client, avid, bvid, cid):
    url = play_url.format(avid=avid, bvid=bvid, cid=cid)
    async with client.get(url) as resp:
        data = await resp.json()
        return data["data"]
    

async def download_one(client, avid, bvid, name, page):
    cid = page["cid"]
    title = legal_name(page["part"])
    no = page["page"]
    print(f"Downloading {no} - {title}...")
    play_info = await get_play_info(client, avid, bvid, cid)
    video_format = play_info["format"][:3]  # 存在flv480这种
    try:    # 有时是dash，有时只有durl
        video_url = play_info["dash"]["video"][0]["baseUrl"]
        audio_url = play_info["dash"]["audio"][0]["baseUrl"]
        video_path = f"video/{name}/{title}.{video_format}"
        audio_path = f"audio/{name}/{title}.mp3"
        if not os.path.exists(video_path):
            async with client.get(video_url) as resp:
                async with aiofiles.open(video_path, "wb") as f:
                    while True:
                        chunk = await resp.content.read(1024)
                        if not chunk:
                            break
                        await f.write(chunk)
        if not os.path.exists(audio_path):
            async with client.get(audio_url) as resp:
                async with aiofiles.open(audio_path, "wb") as f:
                    while True:
                        chunk = await resp.content.read(1024)
                        if not chunk:
                            break
                        await f.write(chunk)
    except KeyError:    # durl直接输出到out
        video_url = play_info["durl"][0]["url"].split("?")[0]
        video_path = f"out/{name}/错误请手动下载__{title}.xml"
        if not os.path.exists(video_path):
            async with client.get(video_url) as resp:
                async with aiofiles.open(video_path, "wb") as f:
                    while True:
                        chunk = await resp.content.read(1024)
                        if not chunk:
                            break
                        await f.write(chunk)
    except Exception as e:
        # 未知错误
        raise e


async def download_collection(bvid):
    async with aiohttp.ClientSession(headers=headers) as client:
        view_info = await get_view_info(client, bvid)
        avid = view_info["aid"]
        num = view_info["videos"]
        name = legal_name(view_info["title"])
        os.makedirs(f"video/{name}/", exist_ok=True)
        os.makedirs(f"audio/{name}/", exist_ok=True)
        os.makedirs(f"out/{name}/", exist_ok=True)
        print(f"Downloading {name} ({num} videos)...")

        task_list = []
        cnt = -1
        pages = view_info["pages"]
        for i, page in enumerate(pages):
            if i % 8 == 0:
                cnt += 1
                task_list.append([])
            task_list[cnt].append(download_one(client, avid, bvid, name, page))
        for task in task_list:
            await asyncio.gather(*task)
            time.sleep(5)   # 限一下速不然会挂
        print("done.")
        print(f"Merging {name}...", end="")
        for filename in os.listdir(f"./video/{name}"):
            # 请手动删除错误文件
            title = filename.split(".")[0]
            if os.path.exists( f"./out/{name}/{title}.mkv"):
                continue
            merge(
                f"./video/{name}/{filename}",
                f"./audio/{name}/{title}.mp3",
                f"./out/{name}/{title}.mkv",    # 使用mkv格式避免B站给的format实际不正确导致合成失败
            )


if __name__ == '__main__':
    # asyncio.run(download_collection("BV1Qx411P7kW"))
    # asyncio.run(download_collection("BV1Xs411o7nq"))
    asyncio.run(download_collection("BV1Nx411N7aN"))