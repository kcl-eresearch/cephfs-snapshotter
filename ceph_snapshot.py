#!/usr/bin/env python3

import argparse
import datetime
import os
import pathlib
import re
import socket
import subprocess
import sys
import yaml

# Print with pid prefix
def pid_print(message):
    print("[%d] %s" % (os.getpid(), message))

# Get filesystem type at path
# Because Python doesn't have a statfs function
def fs_type(path):
    if not os.path.isdir(path):
        return False
    try:
        return subprocess.check_output(["/usr/bin/stat", "-f", "-t", "-c", "%T", path]).decode().rstrip()
    except Exception as e:
        return False

parser = argparse.ArgumentParser()
parser.add_argument("-c", default="/etc/cephfs_snapshot.yaml")
args = parser.parse_args()

timestamp_format = "%Y-%m-%d-%H%M%S%z"
now = datetime.datetime.now(datetime.timezone.utc)
now_str = now.strftime(timestamp_format)

pid_print("Starting at %s" % (now_str,))

try:
    with open(args.c) as fh:
        config = yaml.safe_load(fh)
except Exception as e:
    pid_print("Cannot load configuration from %s: %s" % (args.c, e))
    sys.exit(1)

if not "paths" in config:
    pid_print("Configuration does not contain any paths")
    sys.exit(1)

if os.path.exists(config["last_file"]):
    try:
        with open(config["last_file"]) as fh:
            last_data = yaml.safe_load(fh)
            if (now - datetime.datetime.strptime(last_data["time"], timestamp_format)).total_seconds() < 3600:
                pid_print("Nothing to do yet - exiting.")
                sys.exit(0)

    except Exception as e:
        sys.exit(0)

with open(config["last_file"], "w") as fh:
    try:
        yaml.dump({"host": socket.gethostname(), "time": now_str, "pid": os.getpid()}, fh, default_flow_style=False)
    except Exception as e:
        pid_print("Couldn't create last_file %s: %s" % (config["last_file"], e))
        sys.exit(1)

regex_tstr = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}[0-9]{2}[0-9]{2}[+-][0-9]{4}$')

for path in config["paths"].keys():
    path_fs = fs_type(path)
    if not path_fs:
        pid_print("Path '%s' does not exist or cannot determine type - skipping" % (path,))
        continue

    if path_fs != "ceph":
        pid_print("Path '%s' is of type '%s' not 'ceph' - skipping" % (path, path_fs))
        continue

    snap_path = "%s/.snap" % (path,)
    p = pathlib.Path(snap_path)

    need_snap = True
    for x in p.iterdir():

        if regex_tstr.match(x.name):
            snap_age = (now - datetime.datetime.strptime(x.name, timestamp_format).replace(minute=0, second=0, microsecond=0)).total_seconds() / 3600
            if snap_age > config["paths"][path]["keep"]:
                pid_print("Delete %s" % (x,))
                os.rmdir(x)
            elif snap_age < config["paths"][path]["frequency"]:
                need_snap = False

    if need_snap:
        snap_path = "%s/.snap/%s" % (path, now_str)
        pid_print("Create %s" % snap_path)
        os.mkdir(snap_path)

pid_print("Complete - exiting.")
