import time
import os
_PWM_MAX    = 65535
_PWM_50perc = 32767
_PWM_10perc = 6553

class util():
    def __init__(self, button, led, pw, wdt=None):
        self.button = button
        self.led    = led
        self.pw     = pw
        self.wdt    = wdt

    #------------- turn on or off the charger -------------#
    def doButton(self):
        if self.pw.value == False:
            self.pw.value = True
            self.led.duty_cycle = _PWM_MAX                  # turning one the led
        else:
            self.pw.value = False
            self.led.duty_cycle = _PWM_10perc

        while self.button.value == True:                    # waiting release of the button
            if self.wdt != None:
                self.wdt.feed()
            time.sleep(5)
        return

    #------------- sleeping function (in tens of second) with feed for the WDT -------------#
    def waitDecimal(self, val):
        i = 0

        for j in range(val//100):                           # loop ever 10 seconds
            if self.wdt != None:
                self.wdt.feed()                             # reset watchdog
            for k in range(100):                            
                if self.button.value == False and i == 0:
                    i = 1
                time.sleep(.1)
                if self.button.value == False and i == 1:
                    i = 2
                    self.doButton()

        if self.wdt != None:
            self.wdt.feed()                                 # reset watchdog
        for j in range(val%100):                            
            if self.button.value == False and i == 0:
                i = 1
            time.sleep(.1)
            if self.button.value == False and i == 1:
                i = 2
                self.doButton()
        return

    #------------- check if any data is present on the file -------------#
    def checkFile(self, fileN):
        try: 
            ret = os.stat(fileN)
            if ret[6] > 0:                              # check if there are more line on the file
                return True
            else:
                return False
        except OSError:
            return False

    #------------- write data on the file -------------#
    def saveValue(self, fileN, volt, amper, data, signal=10):
        msg = {'volt':volt,'amper':amper,'data':data,'signal':signal}
        with  open(fileN, "a") as file:
            content = str(msg).replace("'",'"') + ','
            file.write(content)
        return

    #------------- return the data saved on the file -------------#
    def toSend(self, fileN):
        msg = '{"msg":['
        with  open(fileN, "r") as file:
            msg += file.read()[:-1]                         # remove last ','
        msg += ']}'                                         # converts the message in json
        return msg

    #------------- resets the file -------------#
    def clearFile(self, fileN):
        with  open(fileN, "w"):
            pass
        return
