"""
    Stack structure
    - LIFO logic
"""

class Stack():
    # Stack stored using an array, of predefined size
    def __init__(self, size = 15):
        self.__size = size
        self.__pointer = -1
        self.__stack = [None for x in range(size)]

    # Getter for stack size
    @property
    def size(self):
        return self.__size

    # Pushes new data to stack
    def push(self, toPush):
        if self.__pointer < self.__size-1:
            self.__pointer += 1
            self.__stack[self.__pointer] = toPush
        else:
            return None

    # Removes top object from stack
    def pop(self):
        if self.__pointer >= 0:
            popped = self.__stack[self.__pointer]
            self.__stack[self.__pointer] = None
            self.__pointer -= 1
            return popped
        else:
            return None

    # Reveals object at top of stack
    def peek(self):
        if not self.isEmpty():
            return self.__stack[self.__pointer]
        else:
            return None

    def isEmpty(self):
        return (self.__pointer == -1)

if __name__ == "__main__":
    size = 10
    a = Stack(size)

    # Testing
    a.pop()

    #for x in range(10):
    #    a.push(x)
        #print("peek: ", end="")
        #a.peek()
        #print("pop: " + str(a.pop()))

    for x in range(size):
        a.push(x)

    a.peek()
    a.push(1)

    try:
        print(a.stack)
    except AttributeError as e:
        print("your stuff works")
