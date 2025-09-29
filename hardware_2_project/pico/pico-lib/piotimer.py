import rp2

# Timer class with hard interrupts. 
class Piotimer:
    """Piotimer is RP2 PIO based timer that uses hard interrupts.
    Hard interrupts will be handled immediately by the processor which
    makes them suitable for applications where accurate timing is essential.
    Piotimer implements an interface that is identical with MicroPython Timer
    class.
    See Timer class documentation for more information.
    """
    PERIODIC = 1
    ONE_SHOT = 0
    
    _available = [0, 1, 2, 3]

    def __init__(self, *args, mode=PERIODIC, freq=- 1, period=- 1, callback=None):
        # validate parameters
        if freq > 0:
            interval = int(1000000 / freq)
        elif period > 0:
            interval = int(period * 1000)
        else:
            raise RuntimeError('Must specify \'freq\' or \'period\'')

        if interval < 100:
            raise RuntimeError('Too high timer frequency')

        if mode != self.PERIODIC:
            raise RuntimeError('Piotimer supports only PERIODIC operation')
 
        tid = -1
        if len(args) > 0:
            tid = int(args[0])
        if tid < 0: # negative means dynamic allocation
            if len(self._available) == 0:
                raise RuntimeError('Out of timer instances')
            tid = self._available[0]
        
        try:
            self._available.remove(tid) # Raises ValueError if not in the list
        except:
            raise ValueError('Timer ' + str(tid) + ' is not available')
            
        self.id = tid
            
        self.sm = rp2.StateMachine(self.id, self.pio_timer, freq = 1000000)
        # set interrupt handler
        self.sm.irq(handler = callback, hard = True)
        # Start the StateMachine's running.
        self.sm.put(interval - 5)
        self.sm.active(1)

    def __del__(self):
        self.sm.active(0)
        self._available.append(self.id)
    
    def deinit(self):
        self.sm.active(0)
        self._available.append(self.id)
    
    @rp2.asm_pio()
    def pio_timer():
        wrap_target()
        pull(noblock)
        mov(x, osr)
        mov(y,x)
        label("loop")
        jmp(y_dec, "loop")
        irq(rel(0))
        wrap()

