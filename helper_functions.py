import numpy as np
import re
import paramiko
import getpass
import time
from pathlib import Path

def write_pwl_file(pwlfilename, f, amp, dt, tstop):
    t = np.arange(0, tstop + dt / 2, dt)
    v = amp * np.sin(2 * np.pi * f * t)

    with open(pwlfilename, "w") as fp:
        for ti, vi in zip(t, v):
            fp.write(f"{ti:.9e} {vi:.9f}\n")

def update_netlist_file(netlist_file, new_pwlfile, new_td, new_tend):
    with open(netlist_file, "r") as f:
        text = f.read()

    # Replace pwlfile
    text = re.sub(
        r'pwlfile="[^"]*"',
        f'pwlfile="{new_pwlfile}"',
        text
    )

    # Replace td
    text = re.sub(
        r'\btd\s*=\s*([^\s\\]+)',
        f'td={new_td}',
        text
    )

    # Replace tend
    text = re.sub(
        r'\btend\s*=\s*([^\s\\]+)',
        f'tend={new_tend}',
        text
    )

    with open(netlist_file, "w") as f:
        f.write(text)

    print("Updated:")
    print(f"  pwlfile = {new_pwlfile}")
    print(f"  td      = {new_td}")
    print(f"  tend    = {new_tend}")


def copy_files_to_server(host, port, username, password, remote_dir, local_dir, files_to_copy):
    ### Copying files from PC to Server
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=username, password=password)

    sftp = client.open_sftp()

    # Make sure remote directory exists
    def ensure_remote_dir(sftp_client, path):
        parts = path.strip("/").split("/")
        current = ""
        for part in parts:
            current += "/" + part
            try:
                sftp_client.stat(current)
            except FileNotFoundError:
                sftp_client.mkdir(current)

    ensure_remote_dir(sftp, remote_dir)

    # Upload the two files
    for filename in files_to_copy:
        local_path = local_dir / filename
        remote_path = f"{remote_dir}/{filename}"

        if not local_path.exists():
            raise FileNotFoundError(f"Missing local file: {local_path}")

        sftp.put(str(local_path), remote_path)
        print(f"Copied {local_path.name} -> {remote_path}")

    sftp.close()

def run_remote_simulation(host, port, username, password, remote_run_dir):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=username, password=password)

    chan = client.invoke_shell()
    time.sleep(1)

    chan.send("cd\n")
    chan.send("source ~/.bash_profile\n")
    chan.send("source ~/projects/Apollo_v1/env/setup_Apollo_v1.sh\n")
    chan.send(f"cd {remote_run_dir}\n")

    time.sleep(1)
    while chan.recv_ready():
        print(chan.recv(4096).decode(errors="ignore"), end="")

    chan.send("spectre C2LR_Wv_Pdyn.scs -format psfbin -raw ./results\n")
    chan.send("ocean -nograph -restore C2LR_Wv_Pdyn.ocn\n")
    chan.send("exit\n")

    output_text = ""

    while not chan.closed:
        if chan.recv_ready():
            chunk = chan.recv(4096).decode(errors="ignore")
            print(chunk, end="")
            output_text += chunk
        else:
            time.sleep(0.2)

    m = re.search(
        r'(?m)^Pdiss_sw\s*=\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*$',
        output_text
    )

    pdiss_sw = None
    if m:
        pdiss_sw = float(m.group(1))
        print("Power Dissipatin [W]:", pdiss_sw)

    chan.close()
    client.close()

    return pdiss_sw, output_text