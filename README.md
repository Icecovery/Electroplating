This repository contains the code for an electroplating device built from a modified 3D Printer

## Contents

### Electroplating_Serial

This folder contains the code for the Arduino that controls the electroplating device. The Arduino receives commands from the serial interface and controls the voltage and the current of the electroplating device.

### SendCommand.py

This file contains the code for the Python script that sends commands to the Arduino. The script controls the 3D printer via OctoPrint REST API and sends commands to the Arduino via serial.

Change `api_key`, `base_url`, `serial_port` and the variables under the `machine limits` section to match your setup.