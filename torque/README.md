# Tesla GPU Cluster Torque Config

Tesla configuration scripts and items.

# Enable security
add following to /etc/pam.d/{login,sshd}:
account required pam_access.so

# Test filter script
$ cat test.pbs | ./test.py
