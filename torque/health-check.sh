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
if [[ $(hostname -s) =~ ^(kepler05|kepler06|kepler07)$ ]]; then
    expectedcpu="20"
else
    expectedcpu="16"
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

# Check 2 - Memory
/rcc/shared/apps/torque/current/sbin/memcheck >& /dev/null
check_status 0 $? "memory problems"

# Check 3 - Check CPUs
cpu_count=$(/bin/grep processor /proc/cpuinfo | /usr/bin/wc -l)
check_status $expectedcpu $cpu_count "processor count off"

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
