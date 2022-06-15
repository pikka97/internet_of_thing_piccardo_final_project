import board
import analogio
import busio
import supervisor as SV
import microcontroller as MC
import time
import gc

_TICKS_PERIOD = 1<<29

class ADCSensor():
    def __init__(self, pin, retry, slope, intercept):
        self.ncycles   = 2
        self.deltaTime = self.ncycles * 20                     # a loop takes 20 millisec

        self.pin       = pin
        self.retry     = retry
        self.slope     = slope
        self.intercept = intercept

               
    def read(self, ret_val=False):
        gc.collect()
        valRms = [0] * self.retry

        try:
            buff = [0] * (self.deltaTime * 9 + 20)                   # approssimo
            print('Mem adc free: {} alloc: {}'.format(gc.mem_free(), gc.mem_alloc()))
        except MemoryError as err:
            print('Errore: {}'.format(err))
            return -1

        for indRms in range(self.retry):
            try: 
                ind = 0
                pin = analogio.AnalogIn(self.pin)
                endPeriod = (SV.ticks_ms() + self.deltaTime) % _TICKS_PERIOD
                
                while SV.ticks_ms() < endPeriod:
                    # MC.delay_us(2)
                    buff[ind] = pin.value
                    ind += 1
                pin.deinit()
            except IndexError as err:
                pin.deinit()
                print('Errore: {}'.format(err))
                return -1

            if ret_val:
                print ('allocated: {} used: {}'.format(len(buff), ind))

                # valori medi
            cycle_size = ind // self.ncycles


            for i in range(cycle_size):
                mean = buff[i]
                for j in range(1, self.ncycles):
                    mean += buff[cycle_size*j + i]

                buff[i] = mean // self.ncycles

                # rms
            rms2 = 0.0
            for i in range(cycle_size):
                rms2 += (float(buff[i])*float(buff[i]))

            valRms[indRms] = (rms2/cycle_size)**0.5
            if ret_val:
                print ('rms2: {} RMS: {}'.format(rms2, valRms[indRms]))
            time.sleep(0.1)

        rms = sum(valRms) / self.retry
        del valRms
        del buff
        gc.collect()
        
        print ('RMS: {}'.format(rms))

        if ret_val:
            return rms
        else:
            return int (rms * self.slope + self.intercept)

