#!/bin/bash
#
# health-check.sh - checks for Tesla GPU nodes
#
# This script is called by Torque at job start, job end,
# and at some interval of the polling interval.
#
# If any check fails the node is offlined with a note.
#

unhealthy=0
note=""
expecteddimms=8
expectedsize=16384
if [[ $(hostname -s) =~ ^(kepler05|kepler06|kepler07)$ ]]; then
    expectedcpu="20"
    expectedgpus="8"
    expectedtype="K80"
    expectedspeed=2133
else
    expectedcpu="16"
    expectedgpu="3"
    expectedtype="K40"
    expectedspeed=1600
fi

function check_status(){
    # $1 = expected value
    # $2 = status
    # $3 = message if different

    if [[ "$1" != "$2" ]] ; then
        unhealthy=1
	    if [[ -z $note ]] ; then
            note=$3
	    else
            note="$note; $3"
	    fi
    fi
}

# Check 1 - Memory
dimmcount=$(/usr/sbin/dmidecode -t 17 | /bin/grep 'Configured Clock.*MHz' | /usr/bin/wc | /bin/awk '{print $1}')
speedcount=$(/usr/sbin/dmidecode -t 17 | /bin/grep 'Configured Clock.*MHz' | /bin/grep $expectedspeed | /usr/bin/wc | /bin/awk '{print $1}')
sizecount=$(/usr/sbin/dmidecode -t 17 | /bin/grep 'Size.*MB' | /bin/grep $expectedsize | /usr/bin/wc | /bin/awk '{print $1}')
if [ "$dimmcount" -ne "$expecteddimms" ]; then
    check_status 0 $? "Memory problems, not the expected DIMM count."
fi
if [ "$speedcount" -ne "$expecteddimms" ]; then
    check_status 0 $? "Memory problems, not the expected speed."
fi
if [ "$sizecount" -ne "$expecteddimms" ]; then
    check_status 0 $? "Memory problems, not the expected size."
fi


# Check 2 - Check CPUs
cpu_count=$(/bin/grep processor /proc/cpuinfo | /usr/bin/wc -l)
check_status $expectedcpu $cpu_count "processor count off"

# Check 3 - GPUs
gpus=$(/usr/bin/nvvs -g | /bin/grep $expectedtype | /usr/bin/wc | /bin/awk '{print $1}')
if [ "$count" -ne "$expectedgpus" ]; then
    check_status 0 $? "GPU count off"
fi

exit $exitstatus

# Check 4 - Check automount
/etc/init.d/autofs status > /dev/null 2>&1
if [[ "$?" -ne 0 ]] ; then
    /etc/init.d/autofs restart > /dev/null 2>&1
    check_status 0 $? "automount not running"
fi

# Check 5 - Check ypbind
/etc/init.d/ypbind status > /dev/null 2>&1
if [[ "$?" -ne 0 ]] ; then
    /etc/init.d/ypbind restart > /dev/null 2>&1
    ypbind_status=$?
    check_status 0 $ypbind_status "ypbind not started"
    # if ypbind is bounced and is OK, need to restart autofs
    if [[ "$ypbind_status" -eq 0 ]] ; then
        /etc/init.d/autofs restart
    fi
fi

# Check 6 - Check if apps mounted
/bin/grep '/rcc/shared nfs rw' /etc/mtab >/dev/null 2>&1
check_status 0 $? "shared apps not mounted"

# Check 7 - Check local disk usage
percent_disk_used=$( /bin/df / | /usr/bin/tail -n 1 | /bin/awk '{print $4}' | /usr/bin/tr -d '%' )
check_status 0 $(( $percent_disk_used > 90 )) "local disk full"

# Check 8 - test local scratch file system
if [ -d "/scratch/local" ] ; then
    test_file_name=$(/usr/bin/uuidgen)
    /bin/touch /scratch/local/.$test_file_name
    check_status 0 $? "/scratch/local file system problems"
    /bin/rm -f /scratch/local/.$test_file_name
fi

# Check 9 - test global scratch file system
/bin/grep '/scratch/global nfs rw' /etc/mtab >/dev/null 2>&1
check_status 0 $? "/scratch/global not mounted"
test_file_name=$(/usr/bin/uuidgen)
/bin/touch /scratch/global/.$test_file_name
check_status 0 $? "/scratch/global file system problems"
/bin/rm -f /scratch/global/.$test_file_name

# Report if any checks fail
if [[ "$unhealthy" -ne 0 ]] ; then
    echo "ERROR $note"
    exit -1
fi

exit 0
