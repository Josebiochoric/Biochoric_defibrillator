# importing everything from tkinter
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import time
import sys
import _thread
import multiprocessing
import numpy as np
from datetime import datetime
import logging
import serial
import math
import subprocess
import sys
# Open the serial port
#serial_port = '/dev/ttyACM0'
serial_port = 'COM6'
ser = serial.Serial(serial_port, 9600, timeout=0.1)  # Replace '/dev/ttyUSB0' with the appropriate serial port

#variable_id
# 0 for energy selection
# 1 for calibration
# 2 for capacitor charge
# 3 for defibrilation
# 4 for reset
# 5 for voltage selection
# 6 for pulse shape
# 7 for turn off pico

calibration_switch = False
charge_switch = False
time_charging=0
energy = 0
voltage = 0
current= 0.2

#Hi I am updating
class app:
    # creating the tkinter window
    window = tk.Tk()
    window.title("Biochoric defibrillator interface")  
    window.geometry("1024x600")  # Adjusted size for the Raspberry Pi screen
    #window.attributes('-fullscreen', True)
    my_font = ("Neue Haas Grotesk Text Pro", 18)
    my_font_2 = ('Arial', 24)
    ### Create a Notebook widget and add tabs
    notebook = ttk.Notebook(window)
    style = ttk.Style()
    style.configure("TNotebook.Tab", font=my_font, tabposition='n')

    tab1 = ttk.Frame(notebook, width=1024, height=600)  # Adjusted size for the Raspberry Pi screen
    tab2 = ttk.Frame(notebook, width=1024, height=600)  # Adjusted size for the Raspberry Pi screen
    tab3 = ttk.Frame(notebook, width=1024, height=600)  # Adjusted size for the Raspberry Pi screen
    notebook.add(tab1, text="Main")
    notebook.add(tab2, text="Advanced settings")
    notebook.add(tab3, text="Log")
    notebook.pack(expand = False, fill ="both")
    background_image = tk.PhotoImage(file="defibrillator_background.png")
    #background_image = tk.PhotoImage(file="/home/biochoric/defibrillator_background.png")

    def pi_communication(variable_id, comp_message):
        variable_id=str(variable_id)
        comp_message = str(comp_message)
        message = "{},{}\n".format(variable_id, comp_message)
        ser.write(message.encode())
        response = ser.readline().decode('utf-8').strip()
        if response != "":
            print("Received from Pico:", response)
        else:pass
        return response
    
    def energy_selection(var):
        global energy
        main_tab.text_label.config(text = "1st step: Energy is set to " + str(var) + " J")
        advanced_tab.text_frame_advanced_1_3.config(text="Energy is set to " + str(var) + " J")
        logging.info("Energy is set to " + str(var) + "J")
        advanced_tab.text_frame_advanced_2_3.config(text="Voltage not set")
        advanced_tab.my_button_advanced_calibrate["state"] = tk.NORMAL
        main_tab.my_button["state"] = tk.NORMAL
        main_tab.text_label_2.config(text = "2nd step: Please put the pads on the animal and proceed to calibrate")
        energy = var
        response= app.pi_communication(0,energy)

    def calibration_pretext():
        main_tab.text_label_2.config(text = "2nd step: Please wait")
        app.window.after(1, app.calibration)
        
    def calibration():
        global time_charging, calibration_switch
        app.pi_communication(1,0)
        if current == 0:
            main_tab.text_label_2.config(text = "2nd step: Error in calibration, please repeat")
            logging.info("Error in calibration, please repeat")
            calibration_switch = False
            ## error calibrate again
        elif current != 0:
            main_tab.text_label_2.config(text = "2nd step: Your device is now calibrated")
            logging.info("Your device is now calibrated")
            calibration_switch = True
            main_tab.my_button_2["state"] = tk.NORMAL
            advanced_tab.my_button_advanced_charge["state"] = tk.NORMAL
            app.var_calculation()
            ## your device is now calibrated
        else: pass

    def charge_pretext():
        if calibration_switch == True:
            main_tab.text_label_3.config(text = "3rd step: Charging please wait")
            advanced_tab.my_button_advanced_charge["bg"] = "#FDDA0D"
            main_tab.my_button_2["bg"] = "#FDDA0D"
            advanced_tab.my_button_advanced_charge["text"] = "Charging"
            main_tab.my_button_2["text"] = "Charging"
            app.window.after(1, app.charge)
            
        elif calibration_switch == False: main_tab.text_label_3.config(text = "3rd step: Please calibrate before charging")
    def charge():
        global charge_switch, time_charging
        #time_charging=app.pi_communication(2,0)
        charge_switch = True
        time.sleep((time_charging))

        advanced_tab.my_button_advanced_charge["text"] = "Charge"
        advanced_tab.my_button_advanced_charge["bg"] = "#0095D9"
        advanced_tab.my_button_advanced_charge["state"] = tk.DISABLED
        main_tab.my_button_2["text"] = "Charge"
        main_tab.my_button_2["bg"] = "#0095D9"
        main_tab.my_button_2["state"] = tk.DISABLED

        main_tab.my_button_3["state"] = tk.NORMAL
        main_tab.my_button_3["bg"] = "#d90007"
        advanced_tab.my_button_advanced_defibrillate["state"] = tk.NORMAL
        advanced_tab.my_button_advanced_defibrillate["bg"] = "#d90007"
        # I sleep the program for the amount of time taken by the charge
        main_tab.text_label_3.config(text = "3rd step: Charge complete")
        logging.info("the defibrillator has been charged in " + str(time_charging) + " seconds")
        

    def defibrillate_pretext():
        if charge_switch == True:
            main_tab.text_label_3.config(text = "3rd step: Defribrillation running")
            app.window.after(1, app.defibrillate)
        elif charge_switch == False:
            main_tab.text_label_3.config(text = "3rd step: Please charge before proceeding with defibrillation")

    def defibrillate():
        #amp_read_check= app.pi_communication(3,0)
        ## A new read of the sensor is carried to ensure the voltage is passing through the paddles
        time.sleep(2) # check value at the end
        main_tab.my_button_3["state"] = tk.DISABLED
        main_tab.my_button_3["bg"] = "#0095D9"
        advanced_tab.my_button_advanced_defibrillate["state"] = tk.DISABLED
        advanced_tab.my_button_advanced_defibrillate["bg"] = "#0095D9"
        main_tab.text_label_3.config(text = "3rd step: Defibrilation successful")

        main_tab.my_button_2["state"] = tk.NORMAL
        advanced_tab.my_button_advanced_charge["state"] = tk.NORMAL

        logging.info("Defibrillation had been carried successfully")

    def reset():
        app.pi_communication(4,0)
        #logging.info(line)
        main_tab.my_button_2["state"] = tk.DISABLED
        main_tab.my_button_3["state"] = tk.DISABLED
        main_tab.my_button_3["bg"] = "#0095D9"
        advanced_tab.my_button_advanced_charge["state"] = tk.DISABLED
        advanced_tab.my_button_advanced_defibrillate["state"] = tk.DISABLED
        advanced_tab.my_button_advanced_defibrillate["bg"] = "#0095D9"
        advanced_tab.my_button_advanced_calibrate["state"] = tk.NORMAL
        main_tab.my_button["state"]=tk.NORMAL
        ## give it a sec just in case
        main_tab.text_label.config(text = "1st step: Select energy settings")
        main_tab.text_label_2.config(text = "2nd step: Please put the pads on the animal and proceed to calibrate")
        main_tab.text_label_3.config(text = "3rd step: Please charge before proceeding with defibrillation")
        advanced_tab.text_frame_advanced_1_3.config(text="Energy not set")
        advanced_tab.text_frame_advanced_2_3.config(text="Voltage not set")
        logging.info("All the settings have been reseted")

    def voltage_selection(var):
        global voltage, calibration_switch, time_charging
        voltage = var
        advanced_tab.my_button_advanced_calibrate["state"] = tk.DISABLED
        main_tab.my_button["state"]=tk.DISABLED

        main_tab.my_button_2["state"] = tk.NORMAL
        advanced_tab.my_button_advanced_charge["state"] = tk.NORMAL

        advanced_tab.text_frame_advanced_2_3.config(text="Voltage  set to " + str(voltage) + " V")
        advanced_tab.text_frame_advanced_1_3.config(text="Energy overrided by voltage")
        main_tab.text_label.config(text = "1st step: Energy overrided by voltage")
        main_tab.text_label_2.config(text = "2nd step: No need of calibration")
        response= app.pi_communication(5,voltage)
        time_charging = round(app.cubic_fit(voltage),2)
        logging.info("voltage has been set to " + str(voltage) + " volts")
        logging.info("The necessary time for charging is " + str(time_charging) + " seconds")
        calibration_switch = True
    
    def shape_selection(shape, positive, negative, pause):
        pulse= str(shape) + "/" + str(positive) + "/" + str(negative) + "/" + str(pause)
        #positive=float(advanced_tab.spinbox1.get())
        app.pi_communication(6, pulse)
    
    def cubic_fit(x):
        return 3.58345890e-07 * math.pow(x, 3) - 1.89420208e-04 * math.pow(x, 2) + 1.05758876e-01 * x - 3.22859942e-01

    def var_calculation():
        global energy, voltage, current, time_charging
        chest_resistance = 20/float(current)
        tms = (2*8)/1000
        voltage = math.sqrt((float(energy)*float(chest_resistance)/float(tms)))
        total_resistance = chest_resistance + 19
        voltage = (voltage / chest_resistance) * total_resistance
        voltage = round(voltage,2)
        advanced_tab.text_frame_advanced_2_3.config(text="Voltage set to " + str(voltage) + "V")
        logging.info("chest resistance through the subject is :" + str(chest_resistance) + " ohms")
        logging.info("The voltage for defibrillation has been set to: " + str(voltage) + " V")
        time_charging = round(app.cubic_fit(voltage),2)
        logging.info("The necessary time for charging is " + str(time_charging) + " seconds")

    def on_close_window():
    # This function will be executed when the user tries to close the window
        if messagebox.askokcancel("Quit", "Do you want to close the application?"):
            app.window.destroy()
            app.pi_communication(1,0) ## this discharges the capacitor through Bypath-IGBT

    window.protocol("WM_DELETE_WINDOW", on_close_window)
#####################################################################################
############################## First Tab "main"######################################
#####################################################################################
class main_tab:
    # Create a Label widget to display the background image
    background_label = tk.Label(app.tab1, image=app.background_image)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)
    ###texts###
    text_label = tk.Label(app.tab1, font=app.my_font, text="1st step: Select energy settings", bg="white", fg="#0095D9")
    text_label.grid(row=0, column=0, pady=0,columnspan= 6, sticky="w")
    text_label_2 = tk.Label(app.tab1, font=app.my_font, text="2nd step: Please put the pads on the animal and proceed to calibrate", bg="white", fg="#0095D9")
    text_label_2.grid(row=2, column=0, pady=(15,0),columnspan= 6, sticky="w")
    text_label_3 = tk.Label(app.tab1, font=app.my_font, text="3rd step: Please charge before proceeding with defibrillation", bg="white", fg="#0095D9")
    text_label_3.grid(row=5, column=0, pady=(15,0),columnspan= 6, sticky="w")
    ####buttons and tabs####
    spin = tk.Spinbox(app.tab1, from_=0.1, to=2, increment=0.1, wrap=True, buttonbackground="#0095D9", font=('Helvetica', 36), width=10)
    spin.grid(row=1, column=0,pady=20, padx=20,ipady=20,ipadx=20)
    energy_button_set = tk.Button(app.tab1, font=app.my_font,text = ("Set"),command = lambda: app.energy_selection(float(main_tab.spin.get())), bg="#0095D9", fg="white", width=10)
    energy_button_set.grid(row=1, column=2, pady=10, ipady=20)
    energy_button_1 = tk.Button(app.tab1, font=app.my_font,text = "0.5 Jules",command = lambda: app.energy_selection(0.5), bg="#0095D9", fg="white", width=10)
    energy_button_1.grid(row=1, column=3, pady=10, ipady=20, sticky= "e")
    energy_button_2 = tk.Button(app.tab1, font=app.my_font,text = "2 Jules",command = lambda: app.energy_selection(2), bg="#0095D9", fg="white", width=10)
    energy_button_2.grid(row=1, column=4, padx=0, pady=10, ipady=20, sticky= "w")
    my_button = tk.Button(app.tab1, font=app.my_font,text = "Calibrate",command = app.calibration_pretext, bg="#0095D9", fg="white", width=20)
    my_button.grid(row=4, column=0, padx=0, pady=10, ipady=20, columnspan=2)
    my_button_2 = tk.Button(app.tab1, font=app.my_font,text = "Charge",command = app.charge_pretext, bg="#0095D9", fg="white", width=20, state=tk.DISABLED)
    my_button_2.grid(row=6, column=0, pady= 10, ipady=20, columnspan= 2)
    my_button_3 = tk.Button(app.tab1, font=app.my_font,text = "Defibrillate",command = app.defibrillate_pretext,  bg="#0095D9", fg="white", width=20, state=tk.DISABLED)
    my_button_3.grid(row=6, column=2, pady= 10, ipady=20, columnspan= 2)
    my_button_4 = tk.Button(app.tab1, font=app.my_font,text = "Reset settings",command = app.reset,  bg="#0095D9", fg="white", width=10)
    my_button_4.grid(row=6, column=4, pady=(90,0), padx=75,ipadx= 10, ipady= 15, columnspan= 2)

#######################################################################################
################### Second tab "advanced settings"#####################################
#######################################################################################
class advanced_tab:
    def get_current_value(slider_var):
        return '{: .2f}'.format(slider_var.get())

    def slider_changed(slider_label, slider_var):
        slider_label.configure(text=(advanced_tab.get_current_value(slider_var)))

    background_label_advanced = tk.Label(app.tab2, image=app.background_image)
    background_label_advanced.place(x=0, y=0, relwidth=1, relheight=1)
    ######### Set energy manually settings ############################
    current_value_1 = tk.DoubleVar()
    label_frame_advanced = tk.LabelFrame(app.tab2, text='Set energy manually (J)  ',font=app.my_font)
    label_frame_advanced.grid(column=0, row=0, padx=0, pady=0, ipadx=40, ipady=25, sticky="NW")
    radio = tk.Button(label_frame_advanced, font=app.my_font,  command = lambda: app.energy_selection(advanced_tab.get_current_value(advanced_tab.current_value_1)), text="Set", bg="#0095D9", fg="white", width=7)
    radio.grid(column=3, row=0, padx=20, ipadx= 30, ipady= 10)
    text_frame_advanced_1 = tk.Label(label_frame_advanced, font=app.my_font, text="J", fg="#0095D9")
    text_frame_advanced_1.grid(row=1, column=0)
    text_frame_advanced_1_2 = tk.Label(label_frame_advanced, font=app.my_font, text=(get_current_value(current_value_1)), fg="#0095D9")
    text_frame_advanced_1_2.grid(row=1, column=0, padx=40, sticky='w')
    slider = ttk.Scale(label_frame_advanced, from_=0, to=2, orient='horizontal', variable=current_value_1, command=lambda event: advanced_tab.slider_changed(advanced_tab.text_frame_advanced_1_2, advanced_tab.current_value_1))
    slider.grid(column=0, row=0, padx=(30,10), ipadx=60, ipady=25, sticky='w')
    text_frame_advanced_1_3 = tk.Label(label_frame_advanced, font=app.my_font, text="Energy not set", fg="#0095D9")
    text_frame_advanced_1_3.grid(row=2, column=0, padx=0, pady=(10,0),columnspan=4)
    ######### Set voltage manually settings ###########################
    current_value_2 = tk.DoubleVar()
    label_frame_advanced_2 = tk.LabelFrame(app.tab2, text='Set voltage manually (V) ',font=app.my_font)
    label_frame_advanced_2.grid(column=1, row=0, padx=0, pady=0, ipadx=25, ipady=25, columnspan=2, sticky="W")
    radio_2 = tk.Button(label_frame_advanced_2, font=app.my_font, command = lambda: app.voltage_selection(float(advanced_tab.get_current_value(advanced_tab.current_value_2))), text="Set", bg="#0095D9", fg="white", width=7)
    radio_2.grid(column=3, row=0,  padx=20,  ipadx=30, ipady=10)
    text_frame_advanced_2 = tk.Label(label_frame_advanced_2, font=app.my_font, text=" V", fg="#0095D9")
    text_frame_advanced_2.grid(row=1, column=0, padx=0,columnspan=3)
    text_frame_advanced_2_2 = tk.Label(label_frame_advanced_2, font=app.my_font, text=(get_current_value(current_value_2)), fg="#0095D9")
    text_frame_advanced_2_2.grid(row=1, column=0, padx=40, sticky='w',columnspan=3)
    slider_2 = ttk.Scale(label_frame_advanced_2, from_=0, to=500, orient='horizontal', variable=current_value_2, command=lambda event: advanced_tab.slider_changed(advanced_tab.text_frame_advanced_2_2, advanced_tab.current_value_2))
    slider_2.grid(column=0, row=0, padx=(30,10), ipadx=60, ipady=25, sticky='we')
    text_frame_advanced_2_3 = tk.Label(label_frame_advanced_2, font=app.my_font, text="Voltage not set", fg="#0095D9")
    text_frame_advanced_2_3.grid(row=2, column=0, padx=0, pady=(10,0),columnspan=4, rowspan=2)
    ######### Manual pulse settings ####################################
    ####################################################################
    label_frame_advanced_3 = tk.LabelFrame(app.tab2, text='Pulse shape settings  ',font=app.my_font) # Create main label
    label_frame_advanced_3.grid(column=0, row=1,  padx=0, ipadx=0,ipady=25, sticky="N")
    radio_3 = tk.Button(label_frame_advanced_3, font=app.my_font, command=  lambda: app.shape_selection(float(advanced_tab.spinbox1.get()),float(advanced_tab.spinbox2.get()), float(advanced_tab.spinbox3.get()), float(advanced_tab.spinbox4.get())), text="Set", bg="#0095D9", fg="white", width=10) #Create button to set manual settings
    radio_3.grid(column=2, row=3, padx=20,ipadx= 10, ipady= 10)
    my_var_pulse = tk.StringVar(label_frame_advanced_3, value='16') # Create the second spinbox for pulse count
    spinbox1 = tk.Spinbox(label_frame_advanced_3, from_=0, to=16, increment=1, width=6, font=('Helvetica', 30), format='%5.0f', textvariable=my_var_pulse)
    spinbox1.grid(row=2, column=0, pady=5)
    text_frame_advanced_3 = tk.Label(label_frame_advanced_3, font=app.my_font, text="Pulse count", fg="#0095D9")
    text_frame_advanced_3.grid(row=2, column=1, padx=0, sticky='w')
    my_var_positive = tk.StringVar(label_frame_advanced_3, value='100') # Create the second spinbox for t positive
    spinbox2 = tk.Spinbox(label_frame_advanced_3, from_=0, to=10000, increment=100, width=6, font=('Helvetica', 30), format='%5.0f', textvariable=my_var_positive)
    spinbox2.grid(row=3, column=0, pady=5)
    text_frame_advanced_3_2 = tk.Label(label_frame_advanced_3, font=app.my_font, text="T. positive (ms)", fg="#0095D9")
    text_frame_advanced_3_2.grid(row=3, column=1, padx=0, sticky='w')
    my_var_negative = tk.StringVar(label_frame_advanced_3, value='100') # Create the third spinbox for t.negative
    spinbox3 = tk.Spinbox(label_frame_advanced_3, from_=0, to=10000, increment=100, width=6, font=('Helvetica', 30), format='%5.0f', textvariable=my_var_negative)
    spinbox3.grid(row=4, column=0, pady=5)
    text_frame_advanced_3_3 = tk.Label(label_frame_advanced_3, font=app.my_font, text="T. negative (ms)", fg="#0095D9")
    text_frame_advanced_3_3.grid(row=4, column=1, padx=0, sticky='w')
    my_var_pause = tk.StringVar(label_frame_advanced_3, value='0') # Create the fourth spinbox for t.pause
    spinbox4 = tk.Spinbox(label_frame_advanced_3, from_=0, to=10000, increment=100, width=6, font=('Helvetica', 30), format='%5.0f',  textvariable=my_var_pause)
    spinbox4.grid(row=5, column=0, pady=5)
    text_frame_advanced_3_4 = tk.Label(label_frame_advanced_3, font=app.my_font, text="T. pause (ms)", fg="#0095D9")
    text_frame_advanced_3_4.grid(row=5, column=1, padx=0, sticky='w')
    ###### external Buttons############################################
    ###################################################################
    my_button_advanced_calibrate = tk.Button(app.tab2, font=app.my_font, text = "Calibrate",command = app.calibration_pretext,  bg="#0095D9", fg="white", width=12)
    my_button_advanced_calibrate.grid(row=1, column=1, pady=0, ipadx= 10, ipady= 20, sticky="NW")
    my_button_advanced_charge = tk.Button(app.tab2, font=app.my_font, text = "Charge", command = app.charge_pretext,  bg="#0095D9", fg="white", width=12, state=tk.DISABLED)
    my_button_advanced_charge.grid(row=1, column=1, pady=0, padx=270, ipadx= 10, ipady= 20, sticky="NW")
    my_button_advanced_defibrillate = tk.Button(app.tab2, font=app.my_font, text = "Defibrillate", command = app.defibrillate_pretext,  bg="#0095D9", fg="white", width=12, state=tk.DISABLED)
    my_button_advanced_defibrillate.grid(row=1, column=1, pady=(0,0), ipadx= 10, ipady= 20, sticky="W")
    my_button_advanced_reset = tk.Button(app.tab2, font=app.my_font, text = "Reset settings", command = app.reset,  bg="#0095D9", fg="white", width=12)
    my_button_advanced_reset.grid(row=1, column=1, pady=(240,0), padx=270, ipadx= 10, ipady= 20, sticky="SW")

class log:
    def redirect_output_to_log(text_widget):
        class StdRedirector:
            def write(self, message):
                text_widget.configure(state='normal')
                text_widget.insert('end', message)
                text_widget.configure(state='disabled')
                text_widget.see('end')  # Auto-scroll to the end

            def flush(self):
                pass

        sys.stdout = StdRedirector()
        sys.stderr = StdRedirector()

    @staticmethod
    def open_folder(path):
        if sys.platform == 'win32':
            subprocess.Popen(['explorer', path], shell=True)
        elif sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', path])
        else:  # Assume Linux compatibility
            subprocess.Popen(['xdg-open', path])

# Assume 'app' and 'app.tab3' are already defined in your code

# Set up the logging text widget
log_text = tk.Text(app.tab3, wrap='word', state='disabled')
log_text.pack(fill='both', expand=True)

# Redirect stdout and stderr to the log text widget
log.redirect_output_to_log(log_text)

# Get current date and time for the filename
current_time = datetime.now().strftime("%Y%m%d_%H_%M")
#log_file_path = f'your_log_{current_time}.txt'
log_file_path = f'/home/biochoric/Documents/your_log_{current_time}.txt'

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.FileHandler(log_file_path, 'a', 'utf-8'), logging.StreamHandler()])

# Test messages
logging.info("Welcome to Biochoric defibrillator")
logging.info("The program has started")

# Add a button to the tab that opens the specified folder
folder_path = '/home/biochoric/Documents'  # Change this to your folder path
open_folder_button = tk.Button(app.tab3, text="Open log Folder", command=lambda: log.open_folder(folder_path))
open_folder_button.config(width=20, height=3, bg="#0095D9", activebackground='light blue', fg="white", font=("Arial", 15))  # You can adjust the width and height as needed
open_folder_button.pack(side=tk.RIGHT)
# Add the red button to close the application
close_button = tk.Button(app.tab3, text="Close Program", command=app.on_close_window)
close_button.config(width=20, height=3, bg="red", activebackground='dark red', fg="white", font=("Arial", 15))  # Adjust the width and height as needed
close_button.pack(side=tk.LEFT)

# To run the app:
if __name__ == "__main__":
    app.window.mainloop()

 #main_tab()