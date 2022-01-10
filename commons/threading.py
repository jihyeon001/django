import threading
from collections import deque

MAXIMUM_THREAD_COUNT : int
thread_queue : deque

class ThreadManager:
    thread_class = threading.Thread

    def __init__(self, target, args):
        self.target = target
        self.args = args

    def get_thread(self):
        return self.thread_class(
            target=self.target, 
            args=self.args
        )

    def check_thread_count(self):
        return threading.active_count() > MAXIMUM_THREAD_COUNT

    def get_next_thread(self):
        if thread_queue:
            return thread_queue.popleft()
        return None

    def append_thread(self):
        thread = self.get_thread()
        thread_queue.append(thread)

    def start(self):
        pass