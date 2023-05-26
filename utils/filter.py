import json
import threading
from utils.settings import ORIGIN_DATA_PATH, OUTPUT_DATA_PATH

FILE_NAME_PREFIX = 'state_'

class State:
    artwork_state = {}
    block = "0"
    concurrent = 0

    _instance_lock = threading.Lock()

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if not hasattr(State, "_instance"):
            with State._instance_lock:
                if not hasattr(State, "_instance"):
                    State._instance = State(*args, **kwargs)
        return State._instance

    def update_state(self, b):
        self.block = b
        self.artwork_state = {}
        self.load_state()

    def update_and_save(self, aid, ok):
        self.update_load_state(aid, ok)
        self.save_state()

    def load_state(self):
        block = self.block
        state_file_name = FILE_NAME_PREFIX + block + ".json"
        path = OUTPUT_DATA_PATH + block + '/' + state_file_name
        try:
            with open(path) as f:
                self.artwork_state = json.load(f)
        except FileNotFoundError as e:
            print(e)
        except PermissionError as e2:
            print(e2)
        else:
            print('state exits, will continue ! block ', block)

    def save_state(self):
        data = json.dumps(self.artwork_state, indent=4)
        block = self.block
        state_file_name = FILE_NAME_PREFIX + block + ".json"
        path = OUTPUT_DATA_PATH + block + '/' + state_file_name
        try:
            with open(path, 'w') as f:
                f.write(data)
        except PermissionError as e:
            print(e)
        except FileExistsError as e:
            print(e)
        else:
            print('state save successfully, block ', block)

    def filter(self, artwork_id) -> []:
        ret = []
        for aid in artwork_id:
            if not self.check_has_loaded(aid):
                ret.append(aid)
        return ret

    def check_has_loaded(self, aid) -> bool:
        return self.artwork_state.get(aid)

    def update_load_state(self, aid, ok:bool = True) -> None:
        self.artwork_state[aid] = ok

    def get_current_state_block(self):
        return self.block
