import sys
import machine
import math
from machine import ADC, Pin, UART
import time
import _thread

############# set pins ##################################################
output_pins = [machine.Pin(27,machine.Pin.OUT), machine.Pin(28,machine.Pin.OUT), machine.Pin(17,machine.Pin.OUT), machine.Pin(18,machine.Pin.OUT)]
pair1 = [output_pins[0], output_pins[2]] #forward polarization pins
pair2 = [output_pins[1], output_pins[3]] # reverse polarization pins
for i in output_pins:
    i.off()

charging_pin = machine.Pin(19, machine.Pin.OUT)
discharging_pin = machine.Pin(21, machine.Pin.OUT)
bypass_IGBT = machine.Pin(20,machine.Pin.OUT)

#amperage sensing pin and high woltage power supply variables###########
analogInputPin = ADC(26) #current sensor reading
pwm = machine.PWM(machine.Pin(16)) #pin for setting voltage
pwm.freq(1000) # Set the frequency of the PWM signal (in Hz)
MILLIVOLT_PER_AMPERE = 185
AREF = 3.3
DEFAULT_OUTPUT_VOLTAGE = 2.45
ERROR = 0.3
####################### Variables for amperage sensing and resistance calculation#######################
amperage = 0
energy = 0.001 # Jules
chest_resistance = 50
Voltage_defibrillation = 0
time_charging= 0
calibration_switch = False
charge_switch = False

pulses=8
pos_t=0.001
neg_t=0.001
pause_t=0

def Average(lst):
    return sum(lst) / len(lst)

def cubic_fit(x):
    return 3.58345890e-07 * math.pow(x, 3) - 1.89420208e-04 * math.pow(x, 2) + 1.05758876e-01 * x - 3.22859942e-01

class app: 
    #################################################################################################################
    def calibration():
        global amperage, calibration_switch, Voltage_defibrillation
        for pin in pair1 and pair2:
            pin.off()
        amperage = 0
        app.pre_sensing()
        modes.activate_charging_mode()
        cycle = int((0.06/ 3.3) * 65535)
        pwm.duty_u16(cycle)
        time.sleep(2)
        pwm.deinit()
        modes.activate_discharge_mode()
        _thread.start_new_thread(app.amperage_sensing, ())
        time.sleep(0.0003)
        for pin in pair1:
            pin.on()
        time.sleep(2)
        for pin in pair1:
            pin.off() 
        modes.stand_by_mode()
        modes.deplet_capacitor()
        if amperage != 0:
            calibration_switch = True
        else:
            amperage = 0

    def charge():
        global charge_switch, amperage, Voltage_defibrillation
        modes.deplet_capacitor()
        modes.stand_by_mode()
        app.resistance_calculation()
        v_var= 0.003*Voltage_defibrillation
        cycle = int((v_var/ 3.3) * 65535)
        pwm.duty_u16(cycle)
        modes.activate_charging_mode()
        time.sleep(time_charging)
        charge_switch = True
        pwm.deinit()
        modes.stand_by_mode()

    def defibrillation_discharge():
        global pulses, pos_t, neg_t, pause_t, charge_switch
        modes.activate_discharge_mode()
        if charge_switch == True:
            for i in range(pulses):
                for pin in pair1 and pair2:
                    pin.off()
                for pin in pair2:
                    pin.on()  # Turn on the pin
                time.sleep(pos_t)
                for pin in pair1 and pair2:
                    pin.off()
                for pin in pair1:
                    pin.on()  # Turn on the pin
                time.sleep(neg_t)
                for pin in pair1:
                    pin.off()
                time.sleep(pause_t)
            charge_switch = False   
        else:
            pass
        modes.stand_by_mode()
    
    def pre_sensing():
        global ERROR
        ERROR = []
        for i in range(100):
            analogValue = ADC.read_u16(analogInputPin)
            pre_sensor_voltage = (analogValue / 65535) * AREF
            pre_sensor_voltage = (pre_sensor_voltage - DEFAULT_OUTPUT_VOLTAGE ) * 1000 #mvolt
            pre_sensor_voltage = (pre_sensor_voltage/ MILLIVOLT_PER_AMPERE)
            #print(pre_sensor_voltage)
            ERROR.append(pre_sensor_voltage)
        ERROR=Average(ERROR)
        #print("the error is " + str(ERROR))

    def amperage_sensing():
        global AREF, DEFAULT_OUTPUT_VOLTAGE, MILLIVOLT_PER_AMPERE, ERROR, amperage
        num_samples = 1000                           
        samples = [0] * num_samples  
        for i in range(1000):
            analogValue = ADC.read_u16(analogInputPin)
            sensor_voltage = (analogValue / 65535) * AREF #Volt
            #print("sensor voltage " + str(sensor_voltage))
            sensor_voltage = (sensor_voltage - DEFAULT_OUTPUT_VOLTAGE ) * 1000 #mvolt    
            sensor_voltage = (sensor_voltage/ MILLIVOLT_PER_AMPERE) - ERROR
            #print(sensor_voltage)
            if sensor_voltage >= 0:
                sensor_voltage = 0
                #else:
                 #   pass
            samples.pop(0)
            samples.append(sensor_voltage)
            #new_samples.append(sensor_voltage)
            time.sleep(0.0001)
              
        lowest_number = min(samples)
        amperage = lowest_number*(-1)
        #amperage=1
        #print("amperage: " + str(amperage))
        return  amperage

    def resistance_calculation():
        global  amperage, energy, Voltage_defibrillation, time_charging, pulses, chest_resistance
        if calibration_switch ==True:
            chest_resistance = 20/amperage
            #print("calculating chest_resistance")
            tms = 2*float(pulses)/1000
            desired_voltage = math.sqrt((float(energy)*float(chest_resistance))/tms)
            total_resistance = chest_resistance + 19 #internal circuit resistance
            # Calculate the total voltage using the voltage divider formula
            Voltage_defibrillation = (desired_voltage / chest_resistance) * total_resistance
            #print("the voltage is: " + str(Voltage_defibrillation))
            
        elif calibration_switch == False:
            tms = (2*pulses)/1000
            desired_voltage = math.sqrt((float(energy)*float(chest_resistance)/float(tms)))
            total_resistance = chest_resistance + 19
            Voltage_defibrillation = (desired_voltage / chest_resistance) * total_resistance

        else: pass

        time_charging = cubic_fit(Voltage_defibrillation)

        #### reset settings####
    def reset():
        global amperage, calibration_switch, energy, Voltage_defibrillation, charge_switch, pulses, pos_t, neg_t, pause_t, time_charging
        amperage = 0
        energy = 0.01 # Jules
        Voltage_defibrillation = 0
        calibration_switch = False
        charge_switch = False
        time_charging = 0
        pulses=8
        pos_t=0.001
        neg_t=0.001
        pause_t=0
        modes.deplet_capacitor()
        modes.stand_by_mode()
        pass

class modes:
###################### switchs for charging, defibibrillation, stand-by and depletion#####
    def activate_charging_mode():
        discharging_pin.off()  
        charging_pin.on()

    def activate_discharge_mode():
        charging_pin.off()
        discharging_pin.on()

    def stand_by_mode():
        for pin in output_pins:
            pin.off()
        charging_pin.off()
        discharging_pin.off()
        bypass_IGBT.off()

    def deplet_capacitor():
        bypass_IGBT.on()
        time.sleep(3)
        bypass_IGBT.off()

#uart = UART(0, baudrate=115200)
print("hi")
#modes.deplet_capacitor()
#Voltage_defibrillation = 50
#pulses=2
#pos_t=10
#calibration_switch = "a"
#app.charge()
#app.defibrillation_discharge()
#print("end")

while True:
    message = sys.stdin.readline().strip()
    values = message.split(",")
    value1, value2 = values[:2]
    #modes.deplet_capacitor()
    if value1 == "0":
        modes.deplet_capacitor()
        energy = value2
    elif value1 == "1":
        app.calibration()
        response = amperage
        sys.stdout.write( str(response) + "\n")
    elif value1 == "2":
        app.charge()
    elif value1 == "3":
        app.defibrillation_discharge()
    elif value1 == "4":
        app.reset()
    elif value1 == "5":
        calibration_switch = None
        Voltage_defibrillation = float(value2)
    elif value1 == "6":
        shape = value2.split("/")
        pulses, pos_t, neg_t, pause_t = map(float, shape)
    elif value1 == "7":
        chest_resistance = float(value2)
    elif value1 == "8":
        sys.stdout.write( "I am ready to work" + "\n")
    else: pass
    time.sleep(0.1)
