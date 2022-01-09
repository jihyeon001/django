import threading
from collections import deque

MAXIMUM_THREAD_COUNT : int
THREAD_QUEUE : list

class Thread:
    thread_class = threading.Thread

    def set_tartet(self, target):
        self.target = target
        return self

    def set_args(self, *args):
        self.args = args
        return self

    def get_thread(self):
        return self.thread_class(
            target=self.target, 
            args=self.args
        )

    def start(target, *args):
        thread = self.get_thread()
        
        if threading.active_count() > MAXIMUM_THREAD_COUNT:
            THREAD_QUEUE.append()
        thread.start()
