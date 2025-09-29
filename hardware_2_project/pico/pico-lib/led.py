from machine import Pin, PWM


class Led: 
    """Dimmable LED class that implements same interface as Pin (GPIO pin class).
    Adds method brightness() that is used to set brightness of the LED on state.
    Brightness is specified as percentage in range 0.5 - 100%. Values exceeding the
    range are capped to range limits. 
    """
    def __init__(self, pin, mode = Pin.OUT, brightness = 1, value = None):
        # mode can only be Pin.OUT
        # It is defined only to keep interface compatible with Pin class
        if mode != Pin.OUT:
            raise RuntimeError('Pin.OUT is the only allowed value for Led mode')
        self._pin = Pin(pin, Pin.OUT)
        self._pwm = PWM(self._pin)
        self._pwm.freq(1000)
        self.brightness(brightness)
        if value != None:
            self.value(value)
        
    def on(self):
        self._pwm.duty_u16(self._on_val)

    def off(self):
        self._pwm.duty_u16(0)
        
    def low(self):
        self.off()

    def high(self):
        self.on()

    def toggle(self):
        if self._pwm.duty_u16():
            self.off()
        else:
            self.on()
            
    def __call__(self, *args):
        return self.value(*args)

    def value(self, *args):
            if len(args) > 1:
                raise TypeError("Too many arguments. Only one argument allowed")
            elif len(args):
                if args[0]: self.on()
                else: self.off()
            else:
                if self._pwm.duty_u16():
                    return 1
                else:
                    return 0
            
    def brightness(self, brightness):
        brightness = min(100, max(0.5, brightness)) # limit val to range [0.5-100]
        self._on_val = int(65535 * brightness/100)
        if self._pwm.duty_u16():
            self.on()

