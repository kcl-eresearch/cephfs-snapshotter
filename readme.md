# CephFS Snapshotter

This is a script for creating and deleting CephFS snapshots. It is designed to be run as an hourly cron job e.g.:

```
15 * * * * /bin/bash -c "/opt/ceph_snapshotter/ceph_snapshot.py >> /var/log/ceph_snapshot.log 2>&1"
```

If you run the script on the same filesystem from multiple systems, it is advisable to vary the minute; it will only run once per hour even on multiple hosts.

## Configuration

The default configuration file location is `/etc/cephfs_snapshot.yaml` - use the `-c` option to change this. This should contain something similar to what's in `config.example.yaml` - all times are in hours.

The following example makes snapshots of `/scratch` every 8 hours and deletes them after 168 hours (one week).

```
paths:
  /scratch:
    frequency: 8
    keep: 168
```
