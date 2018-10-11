"""
    - circular queue structure
    - FIFO logic
    - additional property tracking size of queue
"""

class Circular_Queue:
    def __init__(self, size):
        self.__size = size
        self.__circQ = [None for _ in range(self.__size)]
        self.__front = -1
        self.__rear = -1
        self.__num_elements = 0

    @property
    def size(self):
        return self.__size

    @property
    def num_elements(self):
        return self.__num_elements

    def push(self, toPush):
        if self.isFull():
            return False
        if self.isEmpty():
            self.__front += 1

        # if rear has reached end of queue, circle it to front of array
        if self.__rear == (self.__size - 1):
            self.__rear = 0
        else:
            self.__rear += 1

        self.__circQ[self.__rear] = toPush
        self.__num_elements += 1
        return True

    def pop(self):
        if self.isEmpty():
            return False
        toReturn = self.__circQ[self.__front]
        self.__circQ[self.__front] = None

        # if last ele popped
        if self.__front == self.__rear:
            self.__front, self.__rear = -1, -1
        # if front pointer has reached front of queue, circle it
        elif self.__front == (self.__size - 1):
            self.__front = 0
        else:
            self.__front += 1
        self.__num_elements -= 1
        return toReturn

    def peek(self):
        return self.__circQ[self.__front]

    def isFull(self):
        noPopCond = self.__front == 0 and self.__rear == (self.__size -1)
        generalCond = self.__front == (self.__rear + 1)
        return noPopCond or generalCond

    def isEmpty(self):
        return self.__front == -1 and self.__rear == -1

if __name__ == "__main__":
    q = Circular_Queue(2)

    for x in range(5):
        print()
        for i in range(2):
            q.push(i)
        while not q.isEmpty():
            print("peek", q.peek())
            print("pop", q.pop())
