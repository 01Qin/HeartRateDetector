import array


class Fifo:
    """Interrupt safe fifo implementation
    Buffer used for storage is allocated when the object is instantiated.
    Methods don't allocate memory.
    Typecode specifies the type of stored values as defined in array
    When used from ISR, the ISR should call put() to add data to fifo and
    the main program must read data from fifo by calling get() often enough
    to prevent fifo from getting full.
    """
    def __init__(self, size, typecode = 'H'):
        """Parameters

        size (int): Fifo size. The maximum number of items stored is one less than the given size
        typecode (char): Type of data stored in fifo. (Default is 'H' - unsigned short)
        """        
        self.data = array.array(typecode)
        for i in range(size):
            self.data.append(0)
        self.head = 0
        self.tail = 0
        self.size = size
        self.dc = 0
        
    def put(self, value):
        """Put one item into the fifo. Raises an exception if the fifo is full."""
        nh = (self.head + 1) % self.size
        if nh != self.tail:
            self.data[self.head] = value
            self.head = nh
        else:
            self.dc = self.dc + 1
            raise RuntimeError("Fifo is full - value dropped")
            
    def get(self):
        """Get one item from the fifo. If the fifo is empty raises an exception and returns the last value."""
        val = self.data[self.tail]
        if self.empty():
            raise RuntimeError("Fifo is empty")
        else:
            self.tail = (self.tail + 1) % self.size
        return val
    
    def dropped(self):
        """Return number of dropped items. A return value that is greater than zero means that fifo is emptied too slowly.""" 
        return self.dc

    def has_data(self):
        """Returns True if there is data in the fifo"""
        return self.head != self.tail
                
    def empty(self):
        """Returns True if the fifo is empty"""
        return self.head == self.tail
