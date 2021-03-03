import numpy as np


class RingBuffer(object):
    """A 1D ring buffer using numpy arrays"""
    def __init__(self, length):
        self.data = np.zeros(length, dtype='d')
        self.cnt = 0

    def extend(self, x):
        """adds array x to ring buffer"""
        index = self.cnt % self.data.size
        x_index = (index + np.arange(x.size)) % self.data.size
        self.data[x_index] = x
        self.cnt += x.size

    def add(self, item):
        self.data[self.cnt % self.data.size] = item
        self.cnt += 1

    def get(self, num_items=0, relative=True):
        if not relative:
            return self.data[0:num_items]
        index = self.cnt % self.data.size
        if num_items == 0:
            return np.hstack((self.data[index+1:], self.data[0:index]))
        elif index - num_items < 0:
            if self.cnt < self.data.size:
                return self.data[0:index]
            else:
                return np.hstack((self.data[-(num_items - index):], self.data[0:index]))
        else:
            return self.data[index-num_items:index]

    def clear(self):
        self.cnt = 0
