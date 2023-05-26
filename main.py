import asyncio
import playwright.async_api
from playwright.async_api import async_playwright
import os
import time
from utils.pivixitem import PivixItem
from utils.utils import save_data, get_start_url, make_start_url, make_extract_content_extent
from utils.settings import DOMAIN_PREFIX, CONCURRENT_LEVEL, DEBUG
import sys
from utils.filter import State
from utils.preload import Preloader

print(os.getcwd())

preloader = Preloader()

def pipeline(item, block):
    save_data(item, block=block)

async def fast_extract_followers(content: playwright.async_api.Page):
    extract_start_time = time.time()
    loc = await content.locator('.bookmark-item span.date').all_text_contents()
    floc = await content.locator('.bookmark-item span.user-name').all_text_contents()
    dates = []
    followers = []

    for i in range(len(loc)):
        dates.append(loc[i])
        followers.append(floc[i])

    extract_end_time = time.time()
    print('page extract time ', extract_end_time - extract_start_time, ' item = ', len(loc))
    extract_contents = [dates, followers]
    return extract_contents

async def fetch(context, aid, block):
    url = make_start_url(aid)
    print("begin fetch : ", url)
    page = await context.new_page()

    # load detail page
    content = []
    try:
        # following: `document`, `stylesheet`, `image`, `media`, `font`, `script`, `texttrack`, `xhr`, `fetch`,
        # `eventsource`, `websocket`, `manifest`, `other`.
        await page.route("**/*", lambda route: route.abort()
        if route.request.resource_type == "image" or route.request.resource_type == 'script'
        else route.continue_())
        first_page_fetch_start_time = time.time()
        await page.goto(url, wait_until="domcontentloaded") # domcontentloaded networkidle
        first_page_fetch_end_time = time.time()
        print("first page fetch time : ", first_page_fetch_end_time - first_page_fetch_start_time)
        while True:
            await page.wait_for_selector('css=.bookmark-items', state='attached', timeout=8000)
            next_content = await fast_extract_followers(page)
            content = make_extract_content_extent(content, next_content)
            await page.wait_for_selector('css=.next', state="attached", timeout=8000)  # 2 secs
            await page.click('.next', timeout=8000) # 0.5 secs

    except playwright.async_api.TimeoutError as e:
        print(e)
        if len(content) > 0:
            item = PivixItem(p_aid=aid, p_followers=content[1], p_dates=content[0])
            pipeline_start_time = time.time()
            pipeline(item, block=block)
            pipeline_end_time = time.time()
            msg = 'block ' + block + ' aid ' + aid
            print(msg, ' page finish, pipeline time = ', pipeline_end_time - pipeline_start_time)
        else:
            print('no content')
        State.get_instance().update_state(b=block)
        State.get_instance().update_and_save(aid=aid, ok=True)
        await page.close()
    else:
        print(aid, ' over')
        await page.close()

async def producer(queue:asyncio.Queue):
    loop = 0
    preloader.flush_buffer()
    preloader.load_block()
    while True:
        kk = preloader.get_aid_until_finish_all_block()
        if kk:
            block = kk[0]
            aid = kk[1]
            msg = 'produce block ' + block + ' : ' + aid
            print(msg)
            await queue.put((block, aid))
        loop = loop + 1


async def consumer(queue:asyncio.Queue):
    loop = 0
    while True:
        print("waiting for job ...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state="auth.json")
            # (block_num, artwork_id)
            kk = await queue.get()
            block = kk[0]
            aid = kk[1]
            await fetch(context=context, aid=aid, block=block)
            print(aid, " task done.")
            queue.task_done()
            await context.close()
            await browser.close()
            loop += 1


async def pixiv_main_task(concurrent_level:int) -> None:
    queue = asyncio.Queue(maxsize=100)
    loop = asyncio.get_event_loop()
    block_consumers = []
    for i in range(concurrent_level):
        single_consumer = loop.create_task(consumer(queue))
        block_consumers.append(single_consumer)
    block_producer = loop.create_task(producer(queue))
    await asyncio.wait(block_consumers + [block_producer])

def main(argv):
    concurrent_level: int
    if argv[1]:
        concurrent_level = int(argv[1])
    else:
        concurrent_level = 1
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pixiv_main_task(concurrent_level))

if __name__ == "__main__":
    main(sys.argv)

