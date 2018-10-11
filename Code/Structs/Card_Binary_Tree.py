from Binary_Tree import Binary_Tree
from Binary_Tree import Node
from Binary_Tree import Traversals

# Child class for Card Binary tree
class Card_Binary_Tree(Binary_Tree):
    def __init__(self, rootNode=None):
        super().__init__(rootNode)

    # reduces the card count value of a particular card, if it reaches 0 then that node is deleted
    def decrement(self, nodeValue):
        if nodeValue == None:
            return False
        elif isinstance(nodeValue, Node): # defensive programming?
            nodeValue = nodeValue.value

        # if node does not exist in the tree
        node_to_dec = self.getNode(nodeValue)
        if node_to_dec == None:
            return False

        elif node_to_dec.value == nodeValue:
            node_to_dec.countValue -= 1
            if node_to_dec.countValue == 0:
                self.delete(node_to_dec)
                self.maintainTree()
            return True

    # traverse the entire tree and only add to the node processing if bigger than or greater than the node passed
    # pass in node, returns the sum of the count values of the nodes which have a value
    # greater than or equal to the passed node
    def cardCountGTET(self, baseNode=False):
        if baseNode == False:
            baseNode = self._root
        minNode = self.get_min_node()
        if minNode == baseNode:
            return self.totalCardCount()
        def base_case(node):
            if node is None:
                return 0
            return -1
        def node_processing(node, left, right):
            toAdd = 0
            if node >= baseNode:
                toAdd = node.countValue
            return toAdd + left + right
        return Traversals.post_order(self._root, base_case=base_case, node_processing=node_processing)

    # COUNT NUM NODES IN TREe -> OTHER METHOD
    # Post order traversal to count number of CARDS in a tree
    # sum of each node's count values
    def totalCardCount(self, parent=False):
        if parent == False:
            parent = self._root
        def base_case(node):
            if node == None:
                return 0
            return -1
        def node_processing(node, left, right):
            return node.countValue + left + right
        tree_count = Traversals.post_order(parent, base_case=base_case, node_processing=node_processing)
        ace_node = self.getNode(11) # could put this higher up to simplify this logical block, but less efficient as unecessary counting
        if ace_node is not None:
            tree_count = tree_count - self.getNode(11).countValue # prevents counting the ace twice
        return tree_count

    # prints count values as well as node value
    def output_tree_console(self, parent):
        if parent == None:
            return False
        self.output_tree_console(parent.left)
        print(parent.value, parent.countValue)
        self.output_tree_console(parent.right)

# child class of node.
# implements additional attribute of countValue
# in this context the corressponding number of cards associated with a card value
# left in the tree
class Card_Node(Node):
    def __init__(self, value, countValue):
        super().__init__(value)
        self.countValue = countValue
