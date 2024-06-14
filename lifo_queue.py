from collections import deque
# Define the FixedLengthLIFOQueue class for photon counts
class FixedLengthLIFOQueue:
    def __init__(self, length):
        self.queue = deque(maxlen=length)       # Initialize the deque with a fixed length
        self.running_sum = 0                    # Initialize the running sum

    def push(self, item):
        if len(self.queue) == self.queue.maxlen:
            self.running_sum -= self.queue[-1]  # Subtract the rightmost item if the queue is full
        self.queue.appendleft(item)             # Append item to the left end of the queue
        self.running_sum += item                # Add the new item to the running sum

    def pop(self):
        if self.queue:
            item = self.queue.pop()             # Pop the last item from the right end of the queue
            self.running_sum -= item            # Subtract the popped item from the running sum
            return item
        else:
            return None                         # Return None if the queue is empty

    def get_last(self):
        if self.queue:
            return self.queue[-1]               # Return the last item in the queue without removing it
        else:
            return None                         # Return None if the queue is empty

    def get_first(self):
        if self.queue:
            return self.queue[0]                # Return the first item in the queue without removing it
        else:
            return None                         # Return None if the queue is empty

    def size(self):
        return len(self.queue)                  # Return the length of the queue

    def get_item(self, index):
        if 0 <= index < len(self.queue):
            return self.queue[index]            # Return the item at the specified index
        else:
            return None                         # Return None if the index is out of range

    def get_running_average(self):
        if self.queue:
            return self.running_sum / len(self.queue)  # Return the running average
        else:
            return 0                                   # Return 0 if the queue is empty
        