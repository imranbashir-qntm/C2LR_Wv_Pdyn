#########################################
######### C2LR Waveform Analysis ########
#########################################

# Notes: Follow the user account setup procedure on the EDA server upto step 13. See procedure on the link below.
# https://co41-confluence.honeywell.lab:4447/display/AP/EDA+Setup
# After creating the local database, you can use this code to run Spectre simulation remotely.

import numpy as np
import re
#import paramiko
import getpass
import time
from pathlib import Path
from helper_functions import write_pwl_file
from helper_functions import update_netlist_file
from helper_functions import copy_files_to_server
from helper_functions import run_remote_simulation

### High level parameters
WAVEGEN = 1 # Generate waveform and save into PWLF file
GEN_NETLIST = 1 # Update netlist with specified parameters
COPY_FILES = 1 # Copy netlist and pwlf file to server
RUN_SIM = 1 # Run Spectre simulation on server
userid = "h638985"
pwlfilename = "sine_1MHz_12p5V.pwl"
netlist_file = "C2LR_Wv_Pdyn.scs"
new_td = "1u" # Follow Cadence Format use u,n,p,f etc 
new_tend = "20u" # Follow Cadence Format use u,n,p,f etc
# ARB waveform gen parameters
f = 1e6          # Hz
amp = 12.5       # V peak
dt = 10e-9      # 10 ns
tstop = 50e-6    # 50 us
#########################

# Server Login Information
host = "coeng1d-vc01.honeywell.lab"
port = 22
username = f"{userid}@honeywell.lab"
if COPY_FILES or RUN_SIM:
    password = getpass.getpass("Password: ")

# Local folder where this Python script lives
local_dir = Path(__file__).resolve().parent

# Only these two files will be copied
files_to_copy = [
    pwlfilename,
    netlist_file,
]

# Remote destination folder
remote_dir = f"/home/{userid}/projects/Apollo_v1/skill/C2LR_Wv_Pdyn"

# Simulation file parameter
new_pwlfile = f"/home/{userid}/projects/Apollo_v1/skill/C2LR_Wv_Pdyn/{pwlfilename}"

### Wave generation
if WAVEGEN:
    write_pwl_file(pwlfilename, f, amp, dt, tstop)

### Updating Simulation Netlist File
if GEN_NETLIST:
    update_netlist_file(netlist_file, new_pwlfile, new_td, new_tend)

### Copy simulation files to server
if COPY_FILES:
    copy_files_to_server(
        host=host,
        port=port,
        username=username,
        password=password,
        remote_dir=remote_dir,
        local_dir=local_dir,
        files_to_copy=files_to_copy,
    )

### Run remote simulation
if RUN_SIM:
    pdiss_sw, output_text = run_remote_simulation(
        host=host,
        port=port,
        username=username,
        password=password,
        remote_run_dir="~/projects/Apollo_v1/skill/C2LR_Wv_Pdyn"
    )
