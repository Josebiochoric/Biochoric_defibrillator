#import serial
import sys
import machine
import math
from machine import ADC, Pin, UART
import time
import _thread

#hi I am an update
# Hi I am a second update
############# set pins
output_pins = [machine.Pin(27,machine.Pin.OUT), machine.Pin(28,machine.Pin.OUT), machine.Pin(17,machine.Pin.OUT), machine.Pin(18,machine.Pin.OUT)]
pair1 = [output_pins[0], output_pins[2]] #forward polarization pins
pair2 = [output_pins[1], output_pins[3]] # reverse polarization pins

IGBT1 = machine.Pin(27, machine.Pin.OUT)
IGBT2 = machine.Pin(28, machine.Pin.OUT)
IGBT3 = machine.Pin(17, machine.Pin.OUT)
IGBT4 = machine.Pin(18, machine.Pin.OUT)

IGBTS = [IGBT1,IGBT2, IGBT3, IGBT4]
for i in IGBTS:
    i.off()
    
charging_pin = machine.Pin(17, machine.Pin.OUT)
discharging_pin = machine.Pin(16, machine.Pin.OUT)
bypass_IGBT = machine.Pin(20,machine.Pin.OUT)
#amperage sensing pin and variables###########
analogInputPin = ADC(26)
pwm = machine.PWM(machine.Pin(12)) # Configure the PWM pin
pwm.freq(10000) # Set the frequency of the PWM signal (in Hz)
MILLIVOLT_PER_AMPERE = 185   # mV per Amp for 5 Amp sensor
AREF = 3.3 # volt
DEFAULT_OUTPUT_VOLTAGE = 2.51  # sensor vcc = 5 V, but a voltage divider is used to get 1.65 V from 2.5 V for the sensor out pin
ERROR = 0.3## was 0.5 on the example code
####################### Variablesfor amperage sensing and resistance calculation#######################
amperage = 0
energy = 0.001 # Jules
chest_resistance = 0
Voltage_defibrillation = 0
time_charging= 0
calibration_switch = False
charge_switch = False

pulses=8
pos_t=0.00125
neg_t=0.00125
pause_t=0

def Average(lst):
    return sum(lst) / len(lst)

def cubic_fit(x):
    return 3.58345890e-07 * math.pow(x, 3) - 1.89420208e-04 * math.pow(x, 2) + 1.05758876e-01 * x - 3.22859942e-01

def power_fit(x):
    return 0.02637989 * math.pow(x, 1.2113786)

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
        #app.amperage_sensing()
        for pin in pair1:
            pin.on()
        time.sleep(2)
        for pin in pair1:
            pin.off() 
        ### probably no need to use bypass IGBT here since its quite low voltage and I make a time.sleep
        modes.stand_by_mode()
        modes.deplet_capacitor() # jsut in case
        if amperage != 0:
            calibration_switch = True
            #print("calibration successful")
            ### send amperage to GUI
        else:
            ### send amperage to GUI to display error message
            ## set amperage back to 0
            #print("error in calibration")
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

            ##GUI should display a message of error

    def defibrillation_discharge():
        global pulses, pos_t, neg_t, pause_t, charge_switch
        modes.activate_discharge_mode()
        if charge_switch == True:
            for i in range(pulses):
                #print("bip I am defibrillating")
                for pin in pair1 and pair2:
                    pin.off()
                for pin in pair1:
                    pin.on()  # Turn on the pin
                time.sleep(pos_t)
                for pin in pair1 and pair2:
                    pin.off()
                for pin in pair2:
                    pin.on()  # Turn on the pin
                time.sleep(neg_t)
                for pin in pair2:
                    pin.off()
                time.sleep(pause_t)
            charge_switch = False   
        else:
            pass
        modes.stand_by_mode()
    
                    #message to be sure capacitor is charged before defibrillation
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
        num_samples = 10  # Number of samples to average (adjust to your needs)
        samples = [0] * num_samples  
        for i in range(510):
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
            time.sleep(0.001)
              
        lowest_number = min(samples)
        amperage = lowest_number*(-1)
        #amperage=1
        #print("amperage: " + str(amperage))
        return  amperage

    def resistance_calculation():
        global  amperage, energy, Voltage_defibrillation, time_charging, pulses
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
            pass

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
        pulses=16
        pos_t=0
        neg_t=0
        pause_t=0

        modes.deplet_capacitor()
        modes.stand_by_mode()
        #print("reseting")
        ### parallelize this function?
        pass

class modes:
###################### switchs for charging, defibibrillation, stand-by and depletion#####
    def activate_charging_mode():
        discharging_pin.off()  
        charging_pin.on()
        ## make regression to adjust how much time is needed to charge

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
        ###calculate time of discharge to make it more efficient?
        time.sleep(3)
        bypass_IGBT.off()

    def turn_off():
        for pin in output_pins:
            pin.off()
        charging_pin.off()
        discharging_pin.off()
        bypass_IGBT.off()

uart = UART(0, baudrate=9600)
#print("the time necessary to charge is: " + str(time_charging))
print("hi")


"""
while True:
    if uart.any():
        #message = uart.readline()
        message = sys.stdin.readline().strip()
        # Read a line from the PC
        values = message.split(",")
        value1, value2 = values
        #sys.stdout.flush()
        if value1 == "0":
            energy = value2
            response0 = "Energy set to: {} Jules".format(value2)
            sys.stdout.write(response0 + "\n")
            IGBT3.on()
        if value1 == "1":
            app.calibration()
            response = "I have run the calibration process and the current is: {} A".format(amperage)
            sys.stdout.write(response + "\n")
            IGBT3.off()
        if value1 == "2":
            #####calculate variables as voltage and so here
            app.charge()
            response3= "Charging time: {} seconds".format(time_charging)
            sys.stdout.write(response3 + "\n")
            IGBT2.on()
        if value1 == "3":

            app.defibrillation_discharge()
            response = "working"
            sys.stdout.write(response + "\n")
            IGBT2.off()
        if value1 == "4":
            sys.stdout.write("Reseting all settings\n")
            app.reset()
            IGBT3.off()
            #machine.reset()
        if value1 == "5":
            calibration_switch = False
            Voltage_defibrillation = float(value2)
            response5 = "Voltage set to: {} volts".format(value2)
            sys.stdout.write(response5 + "\n")
    
            IGBT3.on()
        if value1 == "6":
            shape = value2.split("/")
            pulses, pos_t, neg_t, pause_t = shape
            pulses=float(pulses)
            pos_t=float(pos_t)
            neg_t=float(neg_t)
            pause_t=float(pause_t)
            response = "shape: {} ".format(shape)
            sys.stdout.write(response + "\n")
            IGBT4.on()
        if value1 =="7":
            #set off
            
            app.reset()
            modes.turn_off
    else: pass
        
    #sys.stdout.flush()
    time.sleep(0.01)
    """

while True:
    try:
        if uart.any():
            message = sys.stdin.readline().strip()
            values = message.split(",")

            if len(values) >= 2:
                value1, value2 = values[:2]
            else:
                raise ValueError("Invalid input format, expected at least two values.")

            if value1 == "0":
                try:
                    energy = value2
                    response0 = "Energy set to: {} Jules".format(value2)
                    sys.stdout.write(response0 + "\n")
                except Exception as e:
                    sys.stdout.write("Error setting energy: {}\n".format(e))

            elif value1 == "1":
                try:
                    app.calibration()
                    response = amperage
                    sys.stdout.write( str(response) + "\n")
                except Exception as e:
                    sys.stdout.write("Error in calibration: {}\n".format(e))

            elif value1 == "2":
                try:
                    #####calculate variables as voltage and so here
                    app.charge()
                    response3 = "Charging time: {} seconds".format(time_charging)
                    sys.stdout.write(response3 + "\n")
                except Exception as e:
                    sys.stdout.write("Error during charging: {}\n".format(e))

            elif value1 == "3":
                try:
                    app.defibrillation_discharge()
                    response = "working"
                    sys.stdout.write(response + "\n")
                except Exception as e:
                    sys.stdout.write("Error in defibrillation discharge: {}\n".format(e))

            elif value1 == "4":
                try:
                    sys.stdout.write("Resetting all settings\n")
                    app.reset()
                except Exception as e:
                    sys.stdout.write("Error in resetting settings: {}\n".format(e))

            elif value1 == "5":
                try:
                    calibration_switch = False
                    Voltage_defibrillation = float(value2)
                    response5 = "Voltage set to: {} volts".format(value2)
                    sys.stdout.write(response5 + "\n")
                except ValueError:
                    sys.stdout.write("Error: Invalid voltage input. Please enter a valid number.\n")
                except Exception as e:
                    sys.stdout.write("Error setting voltage: {}\n".format(e))

            elif value1 == "6":
                try:
                    shape = value2.split("/")
                    if len(shape) != 4:
                        raise ValueError("Invalid shape format. Expected 4 values.")
                    pulses, pos_t, neg_t, pause_t = map(float, shape)
                    response = "Shape: {} ".format(shape)
                    sys.stdout.write(response + "\n")
                except ValueError:
                    sys.stdout.write("Error: Invalid shape parameters. Ensure all values are numbers.\n")
                except Exception as e:
                    sys.stdout.write("Error in setting shape: {}\n".format(e))

            elif value1 == "7":
                try:
                    app.reset()
                    modes.turn_off()
                except Exception as e:
                    sys.stdout.write("Error in turning off: {}\n".format(e))

        else:
            pass

    except Exception as e:
        sys.stdout.write("An error occurred: {}\n".format(e))