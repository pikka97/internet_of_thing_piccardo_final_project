import sys
import os
import board
import digitalio
import pwmio
import busio
import time
import gc
from microcontroller import watchdog as wdt
from watchdog import WatchDogMode
from lib.utility import util
from lib.sim800 import sim800
from lib.sensor_adc import ADCSensor
#------------------
# costanti
#------------------
#    3.3/65535*ad.read()*130)
#------------------
_DEBUG      =  1
_APN_SIM   = ''                                                 #TODO Insert here the APN of the sim to connect the network
_NTP_ip1    = '193.204.114.232'
_NTP_ip2    = '193.204.114.233'
_URL        = ''                                                #TODO: Insert here the middleware server here
_FILE_sav   = '/tmp/msg.txt'
_MAX_line   = 10                                                # max number for the file saving
_PIN_       = ''                                                # TODO: Insert here the pin of the SIM
_PWM_MAX    = 65535
_PWM_50perc = 32767
_PWM_10perc = 6553
_LIMITperc  = 10                                                # % threshold to save new data
_TAB_minuti = [0,15,30,45]                                      # minutes on when post data
_MIN_wait   = 1*600                                             # waiting minutes for the loop
_Thres_Vma  = 230*500                                           # minimal power (V*mA) to turn off the charger
_NrThreshold   = 3

_API_KEY    = ''                                                # Api key to communicate with the middleware server

rst = digitalio.DigitalInOut(board.D1)                          # reset sim800 board
rst.direction = digitalio.Direction.OUTPUT

pw = digitalio.DigitalInOut(board.D2)                           # GPIO for the charger
pw.direction = digitalio.Direction.OUTPUT

led = pwmio.PWMOut(board.D5, frequency=1, variable_frequency=True)
led.duty_cycle = _PWM_10perc                                    # duty cicle 10% 

button = digitalio.DigitalInOut(board.D0)                       # charger button
button.direction = digitalio.Direction.INPUT
button.pull=digitalio.Pull.UP                                   # pull up
                                                                # UART for SIM800
uart = busio.UART(board.TX, board.RX, baudrate=19200, timeout=.4)

ad_V = ADCSensor(board.A3, 5, 0.1877125101019382, 16951.361707775177)   # sensor 230 V
#The calibration of this sensor is not work correctly, should be fix before the use
ad_A = ADCSensor(board.A4, 8, 0.10, 10)                                 # sensor current

#=========================== local functions =========================#
def setDebug(val):
    global _DEBUG
    _DEBUG = val
    return

#============================ Initialization of the IOT device =========================================#
#------------------
# watchdog timer init
#------------------
if _DEBUG > 0:
    wdt = None
else:
    wdt.timeout = 15                                    # 16 seconds max value possible
    wdt.mode = WatchDogMode.RESET

util = util(button, led, pw, wdt)
sim = sim800(util.waitDecimal, uart, _APN_SIM, _DEBUG)

try:
    ret = sim.pinSim(_PIN_)
    if ret[0] == False:
        raise NameError('pinSim')

    ret = sim.registerSim()
    if ret[0] == False:
        raise NameError('registerSim')

    ret = sim.getTime()
    if int(ret[1][0:2]) < 20:
        ret = sim.ntpService(_NTP_ip1)
        if ret[0] == False:
            time.sleep(20)
            ret = sim.ntpService(_NTP_ip2)
            if ret[0] == False:
                raise NameError('ntpService')
except NameError as err:
    led.frequency = 5
    led.duty_cycle = _PWM_50perc                        # Found errors, showing them with led
    if _DEBUG > 0:
        print ('Errore in: {}'.format(err))
    else:
        sys.exit()

gc.collect()

#=========================== main loop =========================#
def mainLoop():
    errori    = False
    saveVolt  = 0
    saveAmper = 0
    nrSl      = 0
    nrLines   = _MAX_line if util.checkFile(_FILE_sav) else 0

    while True:
        if errori == True:          ### Problem here !!!!!
            pass

        ret = sim.getTime()
        minuti = -1 if ret[0]==False else int(ret[1][12:14])
        can_I_post_data = minuti in _TAB_minuti                 # if true we can post the data

        if nrLines >= _MAX_line or (nrLines != 0 and can_I_post_data):
            msg = util.toSend(_FILE_sav)
            api_key = _API_KEY if _DEBUG == 0 else None
            ret = sim.httpPost(_URL, msg, api_key)
            if ret[0] == False:
                errori = True
                continue
            nrLines = 0
            util.clearFile(_FILE_sav)

        currenVolt  = ad_V.read()
        currenAmper = ad_A.read()
        gc.collect()
        if currenVolt == -1 or currenAmper == -1:
            errori = True
            continue

        if pw.value == True and (currenVolt * currenAmper) < _Thres_Vma:
            nrSl +=1
            if nrSl > _NrThreshold:                                           # turning off the charger
                pw.value = False
                nrSl = 0

        if (currenVolt * currenAmper) > (saveVolt * saveAmper)*(1 + _LIMITperc/100) or \
                (currenVolt * currenAmper) < (saveVolt * saveAmper)*(1 - _LIMITperc/100):
            ret = sim.getTime()
            if ret[0] == False:
                errori = True
                continue
            util.saveValue(_FILE_sav, currenVolt, currenAmper, ret[1])
            nrLines += 1

        errori = False
        util.waitDecimal(_MIN_wait)
#----------------------- EOF -------------------#


mainLoop()