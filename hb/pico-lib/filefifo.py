
class Filefifo:
    """Mock version of Interrupt safe fifo implementation
    This mock version implements an interface that is identical to
    the real fifo except for the constructor which takes up to two additional
    parameters. The mock version is for testing data processing
    without actually using interrupts. Instead of creating a buffer for data
    the mock fifo reads data from a file. Method put is a dummy function that
    exists for sake of compatibility.
    """
    def __init__(self, size, typecode = 'H', name = 'data.txt', repeat = True):
        """Parameters
        size (integer): Not used - fifo size in the real implementation
        typecode(string): Not used - type of stored values in real implementation
        name (string): Name of the file to read data from. 
        repeat (boolean): End of file behaviour. True means start over from beginning.
        """        
        self._file  = open(name)
        self._repeat = repeat
        
    def put(self, value):
        """Put one item into the fifo. In the mock this function does nothing since data comes from a file."""
        pass

    def get(self):
        """Get one item from the fifo. If repeat is set to False and file ends raises an exception and returns the last value."""
        value = -1
        fail = False
        str = self._file.readline()
        if len(str) > 0:
            value = int(str)
        else:
            if self._repeat:
                self._file.seek(0)
                str = self._file.readline()
                if len(str) > 0:
                    value = int(str)
                else:
                    fail = True
            else:
                fail = True
        if fail:
            raise RuntimeError("Out of data")

        return value
    
    def dropped(self):
        """Return number of dropped items. Mock always returns zero."""
        return 0
       
    def has_data(self):
        """Returns True if there is data in the fifo. Mock always returns True."""
        return True
                
    def empty(self):
        """Returns True if the fifo is empty. Mock always returns False."""
        return False
