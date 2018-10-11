"""
    - class for binary tree
    - functions utilising pointers within nodes to point to left and right nodes
    - structure of the binary tree is automatically maintained so that always remains balanced
    - binary seach tree has property of every node in left subtree is less than the root
    - and every node in the right subtree is larger than the root
    - balanced means that there are the same number of nodes in every subtree in the tree +- 1 node
"""

class Binary_Tree:
    def __init__(self, rootNode=None):
        self._root = rootNode

    @property
    def root(self):
        return self._root

    # CHange to DFS?
    # pass in the value of the node you are looking for, or a equivalent to the one you are looking for
    # returns the node, found via pre order traversals
    def getNode(self, nodeValue):
        toPass = nodeValue
        if isinstance(nodeValue, Node):
            toPass = nodeValue.value

        def base_case(node):
            if node is None:
                return None
            return -1

        def node_processing(node):
            if node.value == toPass:
                return node
            return -1

        returnNode = Traversals.pre_order(self._root, base_case=base_case, node_processing=node_processing)
        return returnNode

    # inserts node using ifs and loops
    def insert(self, node):
        if isinstance(node, int):
            node = Node(node)
        if self.getNode(node) is not None:
            return False
        if self._root is None:
            self._root = node
            return True

        nextNode = self._root
        nextParent = None
        lastParentLeft = True # used to choose which side to insert
        while nextNode is not None:
            if node.value < nextNode.value:
                nextParent = nextNode
                nextNode = nextNode.left
                lastParentLeft = True
            elif node.value > nextNode.value:
                nextParent = nextNode
                nextNode = nextNode.right
                lastParentLeft = False
        if lastParentLeft:
            nextParent.left = node
        else:
            nextParent.right = node
        self.maintainTree()

    # pass in a node or a node value, and this will return
    # that node's parent node via pre order traversal
    def getParent(self, nodeToFind):
        def base_case(node):
            if node is None:
                return None
            return -1
        def node_processing(node):
            if node.left == nodeToFind or node.right == nodeToFind:
                return node
            return -1

        return Traversals.pre_order(self._root, base_case=base_case, node_processing=node_processing)

    # counts the number of nodes in a tree via post order traversal
    def get_tree_size(self):
        def base_case(node):
            if node is None:
                return 0
            return -1
        def node_processing(node, left, right):
            return (left + right + 1)
        return Traversals.post_order(self._root, base_case=base_case, node_processing=node_processing)

    # method which maintains balance within the binary tree
    # for information on how this works check the documented design section
    def maintainTree(self):
        def base_case(node):
            if node is None:
                return 0
            return -1

        def node_processing(node, left, right):
            if left == -1 or right == -1:
                return -1
            elif abs(left - right) >= 2:
                if left > right:
                    self.swap_max_LST(node)
                else:
                    self.swap_min_RST(node)
                return -1
            return left + right + 1

        # unknown number of maintainance actions becuase every time a maintainance occurs
        # the maintainance must start again from the bast of the tree, because one adjustment
        # to one subtree may affect other trees
        completed_comparing = -1
        while completed_comparing == -1:
            completed_comparing = Traversals.post_order(self._root, base_case=base_case, node_processing=node_processing)

    # pass in the root to a subtree, places the maximum node in the left subtree
    # as the new root, and then puts the old root as the first node in new right subtree
    def swap_max_LST(self, swapRoot):
        """
        replace the parent with the max in LST
        - newRoot.right = oldRoot (oldRoot keeps left subtree)
        - if newRoot is direct parent
        return False to start again
        """
        max_LST = self.get_max_LST(swapRoot)
        parent = self.getParent(swapRoot)

        if swapRoot.left != max_LST:
            self.delete(max_LST) # one child guarenteed -> one call
            max_LST.left = swapRoot.left
        swapRoot.left = None # Will this break the subtree?
        max_LST.right = swapRoot

        if parent == None:
            self._root = max_LST
        elif parent.left == swapRoot:
            parent.left = max_LST
        elif parent.right == swapRoot:
            parent.right = max_LST

    # pass in the root to a subtree, places the minimum node in the right subtree
    # as the new root, and then puts the old root as the first node in the new left subtree
    def swap_min_RST(self, swapRoot):
        """
        swap nodes:
        replace parent with minRST
                - newRoot.left <- oldRoot
                - if directChild then keep RST
                - else then newRoot.right <- OldRoot.Right
            return False to start again
        """
        # get -> delete -> swap
        min_RST = self.get_min_RST(swapRoot)
        parent = self.getParent(swapRoot)

        # if direct child, it keeps its old RST, and is not deleted before swapping
        if swapRoot.right != min_RST:
            self.delete(min_RST)
            min_RST.right = swapRoot.right
        swapRoot.right = None # Will this break the subtree?
        min_RST.left = swapRoot

        if parent == None:
            self._root = min_RST
        elif parent.right == swapRoot:
            parent.right = min_RST
        elif parent.left == swapRoot:
            parent.left = min_RST

    # gets the maximum node in the left subtree of the passed node
    def get_max_LST(self, root):
        current_node = root.left
        while current_node.right is not None:
            current_node = current_node.right
        # current_node.left, current_node.right = None, None
        return current_node

    # gets the minimum node in the right subtree of the passed node
    def get_min_RST(self, root):
        current_node = root.right
        while current_node.left is not None:
            current_node = current_node.left
        return current_node

    # deletes a passed node
    # DO NOT MAINTAIN WITHIN THIS METHOD
    # 3 cases - no children, 1 child, 2 children or deleting root
    def delete(self, node):
        numChildren = node.numOfChildren()
        if node == self._root:
            self.delete_root()
        else:
            nodeParent = self.getParent(node)
            nodeIsLeft = nodeParent.left == node
            if numChildren == 0:
                self.delete_noChildren(node, nodeParent, nodeIsLeft)
            elif numChildren == 1:
                self.delete_oneChild(node, nodeParent, nodeIsLeft)
            elif numChildren == 2:
                self.delete_twoChildren(node, nodeParent, nodeIsLeft)

    # lower level fuction for deleting with no children
    def delete_noChildren(self, node, nodeParent, nodeIsLeft=None):
        if nodeIsLeft is None:
            nodeIsLeft = nodeParent.left == node
        if nodeIsLeft:
            nodeParent.left = None
        else:
            nodeParent.right = None

    # lower level fuction for deleting with one child
    def delete_oneChild(self, node, nodeParent, nodeIsLeft=None):
        if nodeIsLeft is None:
            nodeIsLeft = nodeParent.left == node
        childIsLeft = node.hasLeft()

        if nodeIsLeft:
            if childIsLeft:
                nodeParent.left = node.left
            else:
                nodeParent.left = node.right
        else:
            if childIsLeft:
                nodeParent.right = node.left
            else:
                nodeParent.right = node.right

    # lower level fuction for deleting with two children
    def delete_twoChildren(self, node, nodeParent, nodeIsLeft=None):
        if nodeIsLeft is None:
            nodeIsLeft = nodeParent.left == node
        # Find max node in left subtree and replace the node to delete with it
        max_LST = self.get_max_LST(node)

        # Recursively delete the old node from its old position, since it is the max node in left tree, it cannot
        # have a right child, therefore this will be called recursively once at max (one child MAX).
        self.delete(max_LST)
        max_LST.right = node.right
        max_LST.left = node.left
        if nodeIsLeft:
            nodeParent.left = max_LST
        else:
            nodeParent.right = max_LST

    # special case when deleting a root, because the principle of everything in lst must be smaller
    # than root and everything in rst must be bigger than root must be maintained.
    def delete_root(self):
        if self._root.left is None and self._root.right is None:
            self.clearTree()
        else:
            if self._root.left is not None:
                swapNode = self.get_max_LST(self._root)
            else:
                swapNode = self.get_min_RST(self._root)
            self.delete(swapNode)
            swapNode.left = self._root.left
            swapNode.right = self._root.right
            self._root = swapNode

    # For a binary search tree, this should be in ascending order.
    def output_tree_console(self, parent): # Always pass in the root node with initial call.
        if parent == None:
            return False
        self.in_order_traversal(parent.left)
        print(parent.value)
        self.in_order_traversal(parent.right)

    def clearTree(self):
        self._root = None

    # gets the smallest node in the tree
    def get_min_node(self, start_node=False):
        if start_node == False:
            start_node = self._root
        node = start_node
        while node.left is not None:
            node = node.left
        return node

# utility static class for abstracting away the traversals
# pass in lexically scoped function for the base case (reaching a None node)
# and another function for the node processing
class Traversals:
    # Static higher level function for pre order traversals
    @staticmethod
    def pre_order(root, base_case, node_processing):
        base_result = base_case(root)
        if base_result != -1:  # need another base value (None, and False cannot be used) (maybe a false base object?)
            return base_result
        processing_result = node_processing(root)
        if processing_result != -1:
            return processing_result

        left = Traversals.pre_order(root.left, base_case, node_processing)
        right = Traversals.pre_order(root.right, base_case, node_processing)

        if left is not None:
            return left
        elif right is not None:
            return right

    @staticmethod
    # never used so not implemented
    def in_order(self):
        pass

    @staticmethod
    def post_order(root, base_case, node_processing):
        base_result = base_case(root)
        if base_result != -1:
            return base_result

        left = Traversals.post_order(root.left, base_case, node_processing)
        right = Traversals.post_order(root.right, base_case, node_processing)

        processing_result = node_processing(root, left, right)
        return processing_result


# Class for the node
# main properties - pointers to left and right nodes
# defines utility behaviours, such as counting children and comparison methods
class Node: # Association via composition
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

    def hasLeft(self):
        return (not self.left == None)

    def hasRight(self):
        return (not self.right == None)

    def hasChildren(self):
        return (not self.left == None) or (not self.right == None)

    def numOfChildren(self):
        return self.hasLeft() + self.hasRight()

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        return False

    def __str__(self):
        return str(self.value)

    def __gt__(self, other):
        if isinstance(other, Node):
            return self.value > other.value
        elif isinstance(other, int):
            return self.value > other
        return None

    def __lt__(self, other):
        if isinstance(other, Node):
            return self.value < other.value
        elif isinstance(other, int):
            return self.value > other
        return None

    def __ge__(self, other):
        if isinstance(other, Node):
            return self.value >= other.value
        elif isinstance(other, int):
            return self.value >= other
        return None

    def __le__(self, other):
        if isinstance(other, Node):
            return self.value <= other.value
        elif isinstance(other, int):
            return self.value >= other
        return None


# Testing the functionality
if __name__ == "__main__":
    node_value = 1
    insertion_arr = [2,3,4,5,6,7,8,9,10,11]
    b = Binary_Tree( Node(node_value) )
    for num in insertion_arr:
        print(num)
        b.insert( Node(num) )
        b.in_order_traversal(b.root)

    #print(b.getNode(3))

    print("6:", b.root)
    print("3:", b.root.left)
    print("9:", b.root.right)

    #print(b.root.right.left)
    #b.maintainTree()
    #print(b.root.left.right)


    #print(b.get_max_LST(b.root))
    #print(b.get_min_RST(b.root))
    #print(b.get_max_LST(b.root))

    ## print(b.getParent(8))


    #b.testfunc()
    #b.display_tree_structure()

 #   b.in_order_traversal(b.root)

    #b.decrement(Card_Node(3, 0))
    #print()
    #b.in_order_traversal(b.root)
    #print(b.root.left.countValue)
