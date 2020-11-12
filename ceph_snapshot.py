#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import yaml

# Get filesystem type at path
# Because Python doesn"t have a statfs function
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

try:
    with open(args.c) as fh:
        config = yaml.safe_load(fh)
except Exception as e:
    sys.stderr.write("Cannot load configuration from %s: %s\n" % (args.c, e))
    sys.exit(1)

if not "paths" in config:
    sys.stderr.write("Configuration does not contain any paths\n")
    sys.exit(1)

for path in config["paths"].keys():
    path_fs = fs_type(path)
    if not path_fs:
        sys.stderr.write("Path '%s' does not exist or cannot determine type - skipping\n" % (path,))
        continue

    if path_fs != "ceph":
        sys.stderr.write("Path '%s' is of type '%s' not 'ceph' - skipping\n" % (path, path_fs))
        continue
