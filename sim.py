# Simulation of squishing an RTM into a frugal RTM.
import random
from collections import namedtuple

R = random.Random()
R.seed(0)

def randomlyMove(machine):
    machine.trace()
    machine.readMainTape()
    headDelta = R.randint(0, 2) - 1
    newMainValue = R.random()
    newAddressBit = R.randint(0, 1)
    machine.writeMainTape(newMainValue)
    machine.writeAddressTape(newAddressBit)
    if headDelta:
        machine.moveAddressHead(headDelta)

class PlainMachine:
    def __init__(self):
        self.mainTape = {}
        self.addressTape = 0
        self.addressHead = 0
        self.ensureMainCellExists()

    def ensureMainCellExists(self):
        if self.addressTape not in self.mainTape:
            self.mainTape[self.addressTape] = 0

    def readMainTape(self):
        return self.mainTape[self.addressTape]

    def writeMainTape(self, v):
        self.mainTape[self.addressTape] = v

    def writeAddressTape(self, b):
        if b:
            self.addressTape |= (2 ** self.addressHead)
        else:
            self.addressTape &= ~(2 ** self.addressHead)
        self.ensureMainCellExists()

    def moveAddressHead(self, d):
        self.addressHead += d
        if self.addressHead < 0:
            self.addressHead = 0

    def trace(self):
        a = bin(self.addressTape)[2:]
        paddingWidth = self.addressHead - len(a) + 1
        a = ('0' * paddingWidth) + a
        left = a[:-self.addressHead-1]
        mid = a[-self.addressHead-1]
        right = a[-self.addressHead:] if self.addressHead else ''
        print self.addressHead, ('%s(%s)%s' % (left, mid, right)), sorted(self.mainTape.keys())

###########################################################################

class ALL_ZEROS:
    def __repr__(self):
        return '0...'
ALL_ZEROS = ALL_ZEROS()
ALL_ZEROS_POINTER = 0

class Cons(namedtuple('Cons', ['headBit', 'tailPointer'])): pass

class LeafNode(namedtuple('LeafNode', ['parentPointer',
                                       'tailPointer',
                                       'cellValue'])):
    pass

class InternalNode(namedtuple('InternalNode', ['parentPointer',
                                               'leftPointer',
                                               'rightPointer'])):
    pass

class FrugalMachine:
    def __init__(self):
        self.mainTape = [ALL_ZEROS, LeafNode(0, ALL_ZEROS_POINTER, 0)]
        self.tailPointer = 0
        self.addressHeadPointer = 1
        self.mainHeadPointer = 1
        self.allocPointer = 2

    def __getitem__(self, index):
        return self.mainTape[index]

    def __setitem__(self, index, value):
        if index == len(self.mainTape):
            self.mainTape.append(value)
        else:
            self.mainTape[index] = value

    def here(self):
        return self[self.addressHeadPointer]

    def readMainTape(self):
        return self[self.mainHeadPointer].cellValue

    def writeMainTape(self, v):
        self[self.mainHeadPointer] = self[self.mainHeadPointer]._replace(cellValue = v)

    def writeAddressTape(self, b):
        # At this point I realised that I don't think this problem has
        # a solution. The problem here is: what if our simulated
        # address tape contains 000000, and we flip bit zero to a 1,
        # yielding 100000? Let's assume we've visited every address
        # between 000000 and 111111 before. Then in order to update
        # mainHeadPointer we would have to walk down the tree to the
        # leaves to find the cell at simulated address 100000. Say,
        # then, we flip bit one, yielding 110000. Then we have to walk
        # down the tree again to find the cell for 110000. Imagine now
        # that the string of zeros on the address tape is larger, and
        # you can see that we're doing work proportional to the square
        # of the length of the string on the address tape, which in
        # this setting is O(T(n)), and so we are doing O(T(n)^2) work,
        # which is too much for an efficient simulation.
        #
        # Another way of looking at it is to see that the addresses
        # reachable from a given bit string are those bit strings with
        # Hamming distance of 1 from the current address. This makes
        # the graph of reachable addresses an n-dimensional hypercube,
        # where n is the length of the address string. There is no
        # hope of storing that much information in nearly linear
        # space.
        #
        pass #%%%

    def analyzeTail(self, p):
        if self[p] == ALL_ZEROS:
            return (0, p)
        else:
            return (self[p].headBit, self[p].tailPointer)

    def moveAddressHead(self, d):
        if d == -1:
            # Up the tree.
            oldAddressHeadPointer = self.addressHeadPointer
            newAddressHeadPointer = self.here().parentPointer
            if newAddressHeadPointer == 0:
                # Attempt to move off the left of the tape.
                return
            self.addressHeadPointer = newAddressHeadPointer
            oldBit = 1 if self.here().rightPointer == oldAddressHeadPointer else 0
            self[self.allocPointer] = Cons(oldBit, self.tailPointer)
            self.tailPointer = self.allocPointer
            self.allocPointer += 1
        elif d == 1:
            # Down the tree.

            if isinstance(self.here(), LeafNode):
                # Need to split the node before we can do anything.
                oldLeaf = self.here()

                # Allocate new leaf nodes and a new internal node.
                newLeftPointer = self.allocPointer
                self.allocPointer += 1
                newRightPointer = self.allocPointer
                self.allocPointer += 1
                newInternalPointer = self.allocPointer
                self.allocPointer += 1

                (leafDirection, leafTail) = self.analyzeTail(oldLeaf.tailPointer)
                if leafDirection:
                    # Push the old leaf down to the right.
                    newLeft = LeafNode(newInternalPointer, ALL_ZEROS_POINTER, 0)
                    newRight = LeafNode(newInternalPointer, leafTail, oldLeaf.cellValue)
                    replacementForCurrentLeaf = newRightPointer
                else:
                    # Push the old leaf down to the left.
                    newLeft = LeafNode(newInternalPointer, leafTail, oldLeaf.cellValue)
                    newRight = LeafNode(newInternalPointer, ALL_ZEROS_POINTER, 0)
                    replacementForCurrentLeaf = newLeftPointer

                newInternal = InternalNode(oldLeaf.parentPointer, newLeftPointer, newRightPointer)

                self[newLeftPointer] = newLeft
                self[newRightPointer] = newRight
                self[newInternalPointer] = newInternal

                # Adjust main head, if necessary.
                if self.mainHeadPointer == self.addressHeadPointer:
                    self.mainHeadPointer = replacementForCurrentLeaf

                # Move to the new internal node.
                self.addressHeadPointer = newInternalPointer

            elif isinstance(self.here(), InternalNode):
                # We can just move.
                pass

            else:
                raise Exception('Invalid tree node: ' + repr(self.here()))

            (directionBit, self.tailPointer) = self.analyzeTail(self.tailPointer)
            self.addressHeadPointer = \
                self.here().rightPointer if directionBit else self.here().leftPointer
        elif d == 0:
            # No movement.
            pass
        else:
            raise Exception('Invalid address-head delta ' + str(d))

    def trace(self):
        assert isinstance(self[self.mainHeadPointer], LeafNode)
        assert isinstance(self.here(), LeafNode) or isinstance(self.here(), InternalNode)
        assert isinstance(self[self.tailPointer], Cons) or self[self.tailPointer] == ALL_ZEROS
        print self.tailPointer, self.allocPointer, self.addressHeadPointer, self.mainHeadPointer, self.mainTape

###########################################################################

## m = FrugalMachine()
m = PlainMachine()
for x in range(100):
    randomlyMove(m)
