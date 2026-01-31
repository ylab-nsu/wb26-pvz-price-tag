# utils.py

import random
import time

import config_common as config

from lora_mesh import log

class RingBuffer:
    def __init__(self, max_size):
        self.max_size = max_size
        self._cur_ind = 0
        self._list = [None] * max_size

    def add(self, elem):
        self._list[self._cur_ind] = elem
        self._cur_ind = (self._cur_ind + 1) % self.max_size
    
    def __contains__(self, elem):
        return elem in self._list
    
    def clear(self):
        self._list = [None] * self.max_size
        self._cur_ind = 0


def get_random_id(mini=None, maxi=None):
    mini = mini if mini is not None else config.RANDOM_MIN_INT
    maxi = maxi if maxi is not None else config.RANDOM_MAX_INT
    return random.randint(mini, maxi)