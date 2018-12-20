# SUPReMM Setup

Follow https://supremm.xdmod.org/8.0/supremm-overview.html

# Changes
yum install pcp pcp-libs-devel perl-PCP-PMDA pcp-pmda-nvidia-gpu pcp-system-tools

edit cron job - pcp-pmlogger
```
#
# Performance Co-Pilot crontab entries for a monitored site
# with one or more pmlogger instances running
#
# daily processing of archive logs (with compression enabled)
10     0  *  *  *  root  /usr/libexec/pcp/bin/pmlogger_daily -M -k forever
# every 30 minutes, check pmlogger instances are running
0,30  *  *  *  *  root  /usr/libexec/pcp/bin/pmlogger_check -C
```


