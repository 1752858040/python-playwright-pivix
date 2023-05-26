import asyncio
import playwright.async_api
from playwright.async_api import async_playwright
import queue
import asyncio

MAX_USED_TIME = 100

class BrowserObj:
    id:int
    browsers = []
    used_time = 0
    def __init__(self, id):
        self.id = id
        self.used_time = 0

    async def prepare(self):

    async def inc_used_time(self):
        self.used_time += 1
        if self.used_time > MAX_USED_TIME:
            await self.renew_browser()

    async def renew_browser(self):
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=True)
            self.used_time = 0
            return self.browser


class BrowserManager:
    working_browser = queue.Queue
    def __int__(self):
        return self

    def get_context(self):
        context = {}
        #self.working_browser.
        return context

   # def browsers_close(self):
