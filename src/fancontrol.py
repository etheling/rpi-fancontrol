#!/usr/bin/env python3

# https://github.com/etheling/rpi-fancontrol/blob/master/LICENSE (BSD 2-clause)

import os
import subprocess
import time
import syslog
import configparser

from gpiozero import OutputDevice

## Temperatures (C) to turn fan on/off
GPU_ON_THRESHOLD = 70 
GPU_OFF_THRESHOLD = 55 
CPU_ON_THRESHOLD = 70  
CPU_OFF_THRESHOLD = 55 
SLEEP_INTERVAL = 5  # check frequency 
GPIO_PIN = 27  # Which GPIO pin is used to control the fan. Try '$ pinout'

## Info on CPU & GPU temperatures
## https://www.raspberrypi.org/documentation/hardware/raspberrypi/frequency-management.md
## https://www.raspberrypi.org/forums/viewtopic.php?t=141082
## it is possible that 'just' monitoring GPU would be enough...

def log_alert (str):
    print (str)
    syslog.syslog(syslog.LOG_ERR, str)

def log_info (str):
    print (str)
    syslog.syslog(syslog.LOG_INFO, str)

# read /etc/fancontrol.conf and set CPU_* thresholds and GPIO pin
def read_config(str):
    global GPU_ON_THRESHOLD, GPU_OFF_THRESHOLD, CPU_ON_THRESHOLD, CPU_OFF_THRESHOLD, GPIO_PIN
        
    if not os.path.isfile(str):
        return
    
    try:
        config = configparser.ConfigParser()
        config.read(str)
        CPU_ON_THRESHOLD = config['fancontrol'].getint('CPU_ON_THRESHOLD', CPU_ON_THRESHOLD)
        CPU_OFF_THRESHOLD = config['fancontrol'].getint('CPU_OFF_THRESHOLD', CPU_OFF_THRESHOLD)
        GPU_ON_THRESHOLD = config['fancontrol'].getint('GPU_ON_THRESHOLD', GPU_ON_THRESHOLD)
        GPU_OFF_THRESHOLD = config['fancontrol'].getint('GPU_OFF_THRESHOLD', GPU_OFF_THRESHOLD)
        GPIO_PIN = config['fancontrol'].getint('GPIO_PIN', GPIO_PIN)
    except:
        log_info ("Error reading config file:" + str )

#
def get_cpu_temp():
    # $ cat /sys/class/thermal/thermal_zone0/temp
    output = subprocess.run(['cat', '/sys/class/thermal/thermal_zone0/temp'], capture_output=True)
    temp_t = float(output.stdout.decode())/1000
    try:
        return float(temp_t)
    except (IndexError, ValueError):
        log_alert ("ALERT: cannot parse CPU temp. Returning 255C."); # -> fan on
        return 255

def get_gpu_temp():
    # $ vcgencmd measure_temp
    output = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True)
    temp_str = output.stdout.decode()
    try:
        return float(temp_str.split('=')[1].split('\'')[0])
    except (IndexError, ValueError):
        log_alert ("ALERT: cannot parse GPU temp. Returning 255C."); # -> fan on
        return 255


if __name__ == '__main__':
    read_config ("/etc/fancontrol.conf")

    # Validate on and off thresholds
    if CPU_OFF_THRESHOLD >= CPU_ON_THRESHOLD:
        log_alert ("ERROR: CPU off temp is < CPU on temp. Aborting")
        exit (1)
    if GPU_OFF_THRESHOLD >= GPU_ON_THRESHOLD:
        log_alert ("ERROR: GPU off temp is < GPU on temp. Aborting")
        exit (1)

    #
    log_info ("Raspberry Pi Fan Control daemon. GPIO: " + str (GPIO_PIN) +
              ", CPU on/off: " + str(CPU_ON_THRESHOLD) + "/" + str(CPU_OFF_THRESHOLD) +
              ", GPU on/off: " + str(GPU_ON_THRESHOLD) + "/" + str(GPU_OFF_THRESHOLD) )

    fan = OutputDevice(GPIO_PIN)

    while True:
        fanon = -1
        fstatus = fan.value; # `fan.value` returns 1 for "on" and 0 for "off
        cpu_temp = get_cpu_temp()
        gpu_temp = get_gpu_temp()       

        if cpu_temp > CPU_ON_THRESHOLD or gpu_temp > GPU_ON_THRESHOLD:
            fanon=1
        if cpu_temp < CPU_OFF_THRESHOLD and gpu_temp < GPU_OFF_THRESHOLD:
            fanon=0

        ## print ("cpu: " + str(cpu_temp) + ", gpu: " + str(gpu_temp))

        ## if fan is off, and we've reached either of the 'on' tresholds -> ON
        if fstatus == 0 and fanon == 1:
            log_info ("Fan ON: CPU: " +str(cpu_temp) + ", GPU: " +str(gpu_temp))
            fan.on()

        ## if fan is on, and we're below both 'off' thresholds -> OFF
        if fstatus == 1 and fanon == 0:
            log_info ("Fan OFF: CPU: " +str(cpu_temp) + ", GPU: " +str(gpu_temp))
            fan.off()
            
        time.sleep(SLEEP_INTERVAL)

#
# TODO:
# - maybe implement PID file to 'prevent' multiple instances

