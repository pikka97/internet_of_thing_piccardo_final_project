import gc


class sim800():

    def __init__(self, wait, uart=None, apn=None, debug=0, api_key=None):

        # UART
        self.uart = uart
        self.apn = apn
        self.wait = wait
        self.debug = debug

        self.api_key = api_key

            #--------------
            # AT SIM800 Commands
            #--------------
        self.cmdTab = {
            'preset':   {'cmd': 'AT', 'end': 'OK', 'time': 6 },
            'echoff':   {'cmd': 'ATE0', 'end': 'OK', 'time': 2 },
            'funset':   {'cmd': 'AT+CFUN=1', 'end': 'OK', 'time': 2 },
            'signal':   {'cmd': 'AT+CSQ', 'end': 'OK', 'time': 5 },
            'debug2':   {'cmd': 'AT+CMEE=2', 'end': 'OK', 'time': 2 },
            'pintest':  {'cmd': 'AT+CPIN?', 'end': 'OK', 'time': 2 },
            'pinset':   {'cmd': 'AT+CPIN=', 'end': 'OK', 'time': 2 },
            'regset':   {'cmd': 'AT+COPS=0,0', 'end': 'OK', 'time': 5 },                    # seleziona operatore 0=automatico
            'regtest':  {'cmd': 'AT+COPS?', 'end': 'OK', 'time': 5 },
            'nettest':  {'cmd': 'AT+CREG?', 'end': 'OK', 'time': 3 },                       # test se registrato alla rete
            'netset':   {'cmd': 'AT+CREG=1', 'end': 'OK', 'time': 3 },                      # set rete 1=abilita registrazione
            'smsfmt':   {'cmd': 'AT+CMGF=1', 'end': 'OK', 'time': 2 },                      # sms in formato testo
            'smsset':   {'cmd': 'AT+CSCS="GSM"', 'end': 'OK', 'time': 2 },                  # char set per sms
            'smssend':  {'cmd': 'AT+CMGS=', 'end': '>', 'time': 5 },
            'endchr':   {'cmd': '\x1A', 'end': 'OK', 'time': 2 },
            'gprsset':  {'cmd': 'AT+SAPBR=3,1,"Contype","GPRS"', 'end': 'OK', 'time': 3 },  # set modalità ip in GPRS
            'apnset':   {'cmd': 'AT+SAPBR=3,1,"APN",', 'end': 'OK', 'time': 3 },            # imposta APN rete
            'cnopen':   {'cmd': 'AT+SAPBR=1,1', 'end': 'OK', 'time': 10 },                  # apre conessione internet
            'cnclose':  {'cmd': 'AT+SAPBR=0,1', 'end': 'OK', 'time': 5 },                   # chiude conessione internet
            'cntest':   {'cmd': 'AT+SAPBR=2,1', 'end': 'OK', 'time': 3 },                   # legge parametr rete tra i quali IP-address
            'httpinit': {'cmd': 'AT+HTTPINIT', 'end': 'OK', 'time': 10 },
            'urlset':   {'cmd': 'AT+HTTPPARA="URL",', 'end': 'OK', 'time': 3 },
            'jsonset':  {'cmd': 'AT+HTTPPARA="CONTENT","application/json"', 'end': 'OK', 'time': 3 },
            'apikeyset':  {'cmd': 'AT+HTTPPARA="api_key","' + self.api_key + '"', 'end': 'OK', 'time': 3 },
            'httpdata': {'cmd': 'AT+HTTPDATA={},10000', 'end': 'DOWNLOAD', 'time': 15 },
            'httppost': {'cmd': 'AT+HTTPACTION=1', 'end': 'OK', 'time': 12 },
            'httpend':  {'cmd': 'AT+HTTPTERM', 'end': 'OK', 'time': 12 },
            'httptest': {'cmd': 'AT+HTTPSTATUS?', 'end': 'OK', 'time': 3 },
            'ntpset':   {'cmd': 'AT+CNTPCID=1', 'end': 'OK', 'time': 2 },
            'ntpurl':   {'cmd': 'AT+CNTP=', 'end': 'OK', 'time': 5, 'plus': ',4' },
            'ntpget':   {'cmd': 'AT+CNTP', 'end': 'OK', 'time': 12 },
            'timeget':  {'cmd': 'AT+CCLK?', 'end': 'OK', 'time': 3 },
        }

    def debugPrt(self, level, msg):
        if (self.debug >= level):
            print (msg)

    def comando_AT(self, comando, data=None):
        if comando not in self.cmdTab:
            self.debugPrt (1,'comando non trovato: {}'.format(comando))
            return

        cmdAT = self.cmdTab[comando]['cmd']
        endAT = self.cmdTab[comando]['end']
        timeAT = self.cmdTab[comando]['time']
        plusAT = self.cmdTab[comando]['plus'] if 'plus' in self.cmdTab[comando] else ''
        output = ''
        letture = 0

        if 'HTTPDATA' in cmdAT:                         # caso speciale
            cmdAT = cmdAT.format(data)
            data = None

        #esegue comado
        self.uart.write(b'{}{}{}\r'.format(cmdAT,'' if data==None else '"{}"'.format(data), plusAT))
        while True:
            letto = self.uart.readline()
            if not letto:
                self.wait(6)
                if letture > timeAT:
                    self.debugPrt (1,'\tTimeout su: {}'.format(cmdAT))
                    return None
                letture += 1
                continue                    # continuo a leggere

            try: 
                output += str(letto, 'uft-8')        # converto in string
            except:
                pass
            if 'ERROR' in output:
                self.debugPrt (1,'\tErrore:  {}'.format(output))
                return None

            if endAT in output:
                break
            if letture > timeAT:
                self.debugPrt (1,'\tNon trovato end su: {}'.format(cmdAT))
                return None
            letture += 1
        # end while
        self.debugPrt (2, 'Ret {}: [{}]'.format(cmdAT, output))
        return output

    def nosollecit_AT(self, expect, timeout):
        output = ''
        letture = 0

        while True:
            letto = self.uart.readline()
            if not letto:
                self.wait(6)
                if letture > timeout:
                    self.debugPrt (1,'\tTimeout exp. su: {}'.format(expect))
                    return None
                letture += 1
                continue                    # continuo a leggere

            try: 
                output += str(letto, 'uft-8')        # converto in string
            except:
                pass
            if expect in output:
                break
            if letture > timeout:
                self.debugPrt (1,'\tTimeout exp. su: {}'.format(expect))
                return None
            letture += 1
        # end while

        self.debugPrt (2, 'Uns AT: {}'.format(output))
        return output

    def __preSet__(self):
        if self.comando_AT('gprsset') == None:
            return False
        if self.comando_AT('apnset', self.apn) == None:
            return False
        if self.comando_AT('cnopen') == None:
            return False
        gc.collect()
        return True

#--------------------------------------------------------------------#
    def pinSim(self, pin=None):
        if self.comando_AT('preset') == None:
            return False, None
        if self.comando_AT('echoff') == None:
            return False, None
        if self.comando_AT('funset') == None:
            return False, None

        ret = self.comando_AT('pintest')
        if ret == None:
            return False, None
        if 'READY' in ret:
            return True, ''
        if pin != None:
            ret = self.comando_AT('pinset', pin)
            if ret == None:
                return False, None
            return True
        return False, None

    def registerSim(self):
        if self.comando_AT('regset') == None:
            return False, None

        if self.comando_AT('gprsset') == None:
            return False, None
        if self.comando_AT('apnset', self.apn) == None:
            return False, None

        setReg = True
        for _ in range (3):
            ret = self.comando_AT('nettest')
            if ret == None:
                return False, None
            if ': 1,' in ret:
                return True, ''

            if setReg and self.comando_AT('netset') == None:
                return False, None
            setReg = False
        return False, None

    def sendSms(self, nrtel, msg):
        if self.comando_AT('smsfmt') == None:
            return False, None
        if self.comando_AT('smsset') == None:
            return False, None
        ret = self.comando_AT('smssend', nrtel)
        if ret == None:
            return False, None

        lines = msg.split('\r')
        for m in lines:
            self.uart.write(b'{}\r'.format(m))
            self.wait(4)

        msg = self.comando_AT('endchr')
        if msg == None:
            return False, None
        return True, msg
        
    def httpPost(self, url, data):
        if self.__preSet__() == False:
            return False, None

        self.wait(50)
        if self.comando_AT('httpinit') == None:
            return False, None
        if self.comando_AT('urlset', url) == None:
            return False, None
        if self.api_key != None:
            if self.comando_AT('apikeyset') == None:
                return False, None
        if self.comando_AT('jsonset') == None:
            return False, None
        if self.comando_AT('httpdata', len(data)) == None:
            return False, None

        lines = data.split('\r')
        for m in lines:
            self.uart.write(b'{}\r'.format(m))
            self.debugPrt (2, 'invio:  {}'.format(m))
            self.wait(1)

        for _ in range (10):
            if 'OK' in self.uart.readline():
                break
            self.wait(1)

        err = False
        if self.comando_AT('httppost') == None:
            err = True
        self.wait(100)

        if self.nosollecit_AT('ACTION', 10) == None:
            err = True
        if self.comando_AT('httpend') == None:
            err = True
        self.wait(50)
        if self.comando_AT('cnclose') == None:
            err = True

        if err:
            return False, None
        return True
        
    def ntpService(self, url):
        if self.__preSet__() == False:
            return False, None

        err = False
        if self.comando_AT('ntpset') == None:
            err = True
        if not err and self.comando_AT('ntpurl', url) == None:
            err = True
        if not err and self.comando_AT('ntpget') == None:
            err = True
        self.wait(100)
        if self.comando_AT('cnclose') == None:
            err = True

        if err:
            return False, None
        return True, ''

    def getTime(self):
        ret = self.comando_AT('timeget')
        if ret == None:
            return False, None
        tm = ret.split('"')
        if len(tm) < 1:
            return False, None
        return True, tm[1][:17]
