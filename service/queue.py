from queue import Queue
from typing import TypeVar, Generic

T = TypeVar('T')


class QueueService(Generic[T]):
    def __init__(self):
        self.queue: Queue[T] = Queue()

    def put(self, item: T):
        self.queue.put(item)

    def get_list(self):
        return self.queue.queue
    
    def get_self(self) -> Queue:
        return self.queue
