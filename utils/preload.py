import os
from utils.settings import ORIGIN_DATA_PATH
from utils.settings import OUTPUT_DATA_PATH
import openpyxl
from utils.filter import State
import asyncio
import queue

BLOCKMAXSIZE = 100


def prepare(block_num):
    path = OUTPUT_DATA_PATH + block_num + '/'
    if not os.path.exists(path):
        os.makedirs(path)
        print('mkdir ', path)

class Preloader:
    blocks_queue = queue.Queue(maxsize=2000)
    id_queue = queue.Queue(maxsize=1000*BLOCKMAXSIZE)
    next_block_id_queue = queue.Queue(maxsize=1000*BLOCKMAXSIZE)

    def get_aid_until_finish_all_block(self):
        self.flush_buffer()
        if not self.id_queue.empty():
            ret = self.id_queue.get()
            block = ret[0]
            aid = ret[1]
            return (block, aid)
        else:
            return None

    def __init__(self, path=ORIGIN_DATA_PATH):
        files = os.listdir(path)
        for f in files:
            print(f)
            block = str(f.split('.')[0])
            self.blocks_queue.put(block)


    def load_block(self):
        if not self.blocks_queue.empty():
            block_num = self.blocks_queue.get()
            print('loading block ', block_num)
            prepare(block_num)
            wb = openpyxl.load_workbook(ORIGIN_DATA_PATH + block_num + '.xlsx')
            ws = wb.active
            num = 0
            artwork_id = []
            for line in ws:
                if num == 0:
                    num += 1
                    continue
                aid = str(line[0].value)
                artwork_id.append(aid)
                num += 1

            state = State.get_instance()
            state.update_state(block_num)
            filter_artwork_id = state.filter(artwork_id=artwork_id)
            print('block ', block_num, ' remain ', len(filter_artwork_id), ' item.')
            for item in filter_artwork_id:
                self.next_block_id_queue.put((block_num, item))

    def flush_buffer(self):
        if self.id_queue.qsize() <= BLOCKMAXSIZE / 2:
            while not self.next_block_id_queue.empty():
                next = self.next_block_id_queue.get()
                self.id_queue.put(next)
            self.load_block()

    def has_unfinished_block(self) -> bool:
        return not self.blocks_queue.empty()