#!/usr/bin/python

#---------------------------------------------------------------#
# File: $TORQUE_HOMEDIR/sbin/qsub_filter_gpu.py
# Auth: Matthew Flister <maflister@mcw.edu>
# Desc: This is a GPU specific filter for Torque's qsub command.
#---------------------------------------------------------------#


#TODO
# logging?


import sys, re, os, pwd

# max nodes for queues
gpunodes = 1

# cores per node type
k40cores = 16
k80cores = 20

# gpus per node type
k40gpus = 3
k80gpus = 8

# max memory for queues in gb
gpumem = 120

# max walltimes for queues
gpuwtime = 336

# username
username = pwd.getpwuid(os.geteuid())[0]
exemptusers = ["akrruser"]

sendmailCommand = "/usr/sbin/sendmail -t"

### DO NOT CHANGE ANYTHING BELOW THIS ###
# get default account or list of accounts
def getaccounts():
    accounts = []
    command = "mam-list-accounts"
    recs = os.popen(command, "r").readlines()[2:]
    for line in recs:
        m = re.search('\s*(\w+)\s*(\w+)\s*(\w+)\s*', line)
        account = m.group(1)
        isactive = m.group(2)
        if isactive == 'True':
            accounts.append(account)
    return accounts

# enter if qsub script
errors = []
warnings = []

# grab lines from stdin
line1 = sys.stdin.readline()
lines = sys.stdin.readlines()

if len(sys.argv) == 2:
    if "#!" not in line1:
        msg = 'First line should include shabang (#!). Example: #!/bin/sh or #!/bin/bash, etc.'
        errors.append(msg)
    pbs = "no"
    for line in lines:
        if pbs == "no":
            if not line.strip(): # skip blank lines between shabang and first #PBS line
                continue
            if "#PBS" in line: # enter if #PBS appears directly after shabang
                pbs = "yes"
            else:
                msg = 'PBS options are either missing or not directly after the shabang (#!).\nExample: #PBS -l nodes=1:ppn=1.'
                errors.append(msg)
        m = re.search('(?<=#PBS -N )(\w+)', line)
        if (m):
            jobname = m.group(0)
        m = re.search('(?<=#PBS -A )(\w+)', line)
        if (m):
            account = m.group(0)
        m = re.search('#PBS\s*\-l\s*\S*nodes\=(\w+)', line)
        if (m):
            nodes = m.group(1)
        m = re.search('#PBS\s*\-l\s*\S*ppn\=(\d+)', line)
        if (m):
            ppn = float(m.group(1))
        m = re.search('#PBS\s*\-l\s*\S*mem\=(\w+)', line)
        if (m):
            mem = m.group(1)
        m = re.search('#PBS\s*\-l\s*\S*walltime\=(\d+(:\d+)*)', line)
        if (m):
            walltime = m.group(1)
        # gpus
        m = re.search('#PBS\s*\-l\s*\S*gpus\=(\d+)', line)
        if (m):
            gpus = m.group(1)
        # features
        m = re.search('#PBS\s*\-l\s*\S*feature\=(\w+)', line)
        if (m):
            features = m.group(1)
        m = re.search('(?<=#PBS -q )(\w+)', line)
        if (m):
            queue = m.group(0)

elif len(sys.argv) > 2 and os.path.isfile(sys.argv[-1]):
    # get qsub command line
    line = ' '.join(sys.argv[1:-1])
    m = re.search('(?<= -N )(\w+)', line)
    if (m):
        jobname = m.group(0)
    m = re.search('(?<=#PBS -A )(\w+)', line)
    if (m):
        account = m.group(0)
    m = re.search('\-l\s*\S*nodes\=(\w+)', line)
    if (m):
        nodes = m.group(1)
    m = re.search('\-l\s*\S*ppn\=(\d+)', line)
    if (m):
        ppn = float(m.group(1))
    m = re.search('\-l\s*\S*mem\=(\w+)', line)
    if (m):
        mem = m.group(1)
    m = re.search('\-l\s*\S*walltime\=(\d+(:\d+)*)', line)
    if (m):
        walltime = m.group(1)
    # gpus
    m = re.search('\-l\s*\S*gpus\=(\d+)', line)
    if (m):
        gpus = m.group(1)
    # features
    m = re.search('\-l\s*\S*feature\=(\w+)', line)
    if (m):
        features = m.group(1)
    m = re.search('(?<= -q )(\w+)', line)
    if (m):
        queue = m.group(0)

    # deal with script
    if "#!" not in line1:
        msg = 'First line should include shabang (#!). Example: #!/bin/sh or #!/bin/bash, etc.'
        errors.append(msg)
    pbs = "no"
    #for line in sys.stdin.readlines():
    for line in lines:
        if not line.strip(): # skip blank lines between shabang and first #PBS line
            continue
        if pbs == "no":
            if "#PBS" in line: # enter if #PBS appears directly after shabang
                pbs = "yes"
            else:
                msg = 'PBS options are either missing or not directly after the shabang (#!).\nExample: #PBS -l nodes=1:ppn=1.'
                errors.append(msg)
        try:
            jobname
        except:
            m = re.search('(?<=#PBS -N )(\w+)', line)
            if (m):
                jobname = m.group(0)
        try:
            account
        except:
            m = re.search('(?<=#PBS -A )(\w+)', line)
            if (m):
                account = m.group(0)
        try:
            nodes
        except:
            m = re.search('#PBS\s*\-l\s*\S*nodes\=(\w+)', line)
            if (m):
                nodes = m.group(1)
        try:
            ppn
        except:
            m = re.search('#PBS\s*\-l\s*\S*ppn\=(\d+)', line)
            if (m):
                ppn = float(m.group(1))
        try:
            mem
        except:
            m = re.search('#PBS\s*\-l\s*\S*mem\=(\w+)', line)
            if (m):
                mem = m.group(1)
        try:
            walltime
        except:
            m = re.search('#PBS\s*\-l\s*\S*walltime\=(\d+(:\d+)*)', line)
            if (m):
                walltime = m.group(1)
        # gpus
        try:
            gpus
        except:
            m = re.search('#PBS\s*\-l\s*\S*gpus\=(\d+)', line)
            if (m):
                gpus = m.group(1)
        # features
        try:
            features
        except:
            m = re.search('#PBS\s*\-l\s*\S*feature\=(\w+)', line)
            if (m):
                features = m.group(1)
        try:
            queue
        except:
            m = re.search('(?<=#PBS -q )(\w+)', line)
            if (m):
                queue = m.group(0)

# enter if no pbs script is supplied
# example: echo sleep 30 | qsub -l nodes=1:ppn=1
# example: qsub -I -l nodes=1:ppn=1
else:
    # read in qsub command line options 
    line = ' '.join(sys.argv[1:])
    # enter if form is not qsub options
    if not line:
        #for line in sys.stdin.readlines():
        for line in lines:
            line.strip()
            m = re.search('(?<=#PBS -N )(\w+)', line)
            if (m):
                jobname = m.group(0)
            m = re.search('(?<=#PBS -A )(\w+)', line)
            if (m):
                account = m.group(0)
            m = re.search('#PBS\s*\-l\s*\S*nodes\=(\w+)', line)
            if (m):
                nodes = m.group(1)
            m = re.search('#PBS\s*\-l\s*\S*ppn\=(\d+)', line)
            if (m):
                ppn = float(m.group(1))
            m = re.search('#PBS\s*\-l\s*\S*mem\=(\w+)', line)
            if (m):
                mem = m.group(1)
            m = re.search('#PBS\s*\-l\s*\S*walltime\=(\d+(:\d+)*)', line)
            if (m):
                walltime = m.group(1)
            m = re.search('#PBS\s*\-l\s*\S*gpus\=(\d+)', line)
            if (m):
                gpus = m.group(1)
            m = re.search('#PBS\s*\-l\s*\S*feature\=(\w+)', line)
            if (m):
                features = m.group(1)
            m = re.search('(?<=#PBS -q )(\w+)', line)
            if (m):
                queue = m.group(0)
    else:
        m = re.search('(?<= -N )(\w+)', line)
        if (m):
            jobname = m.group(0)
        m = re.search('\-A\s*(\w+)', line)
        if (m):
            account = m.group(1)
        m = re.search('\-l\s*\S*nodes\=(\w+)', line)
        if (m):
            nodes = m.group(1)
        m = re.search('\-l\s*\S*ppn\=(\d+)', line)
        if (m):
            ppn = float(m.group(1))
        m = re.search('\-l\s*\S*mem\=(\w+)', line)
        if (m):
            mem = m.group(1)
        m = re.search('\-l\s*\S*walltime\=(\d+(:\d+)*)', line)
        if (m):
            walltime = m.group(1)
        m = re.search('\-l\s*\S*gpus\=(\d+)', line)
        if (m):
            gpus = m.group(1)
        m = re.search('\-l\s*\S*feature\=(\w+)', line)
        if (m):
            features = m.group(1)
        m = re.search('(?<= -q )(\w+)', line)
        if (m):
            queue = m.group(0)

##### MAIN START #####
if username in exemptusers:
    pass
else:
    # for each must-have attribute check if exists and exit if not try: jobname except: msg = 'PBS job name is missing. Please consider adding a job name to identify your work.\nExample: #PBS -N JobName.' warnings.append(msg) jobname = 'missing' try: account except: account = 'missing' try: nodes except: msg = 'PBS nodes request is required. Example: #PBS -l nodes=1:ppn=1.' errors.append(msg) nodes = 'missing' try: ppn
    except:
        msg = 'PBS processor per node request is required. Example: #PBS -l nodes=1:ppn=1.'
        errors.append(msg)
        ppn = 'missing'
    try:
        mem
    except:
        msg = 'PBS memory request is required. Example: #PBS -l mem=5gb.'
        errors.append(msg)
        mem = 'missing'
    try:
        walltime
    except:
        msg = 'PBS walltime request is required. Example: #PBS -l walltime=1:00:00.'
        errors.append(msg)
        walltime = 'missing'
    try:
        gpus
    except:
        msg = 'PBS GPU request is missing. GPU cluster jobs should utilize at least 1 GPU.\nExceptions include small pre/post processing jobs.\nExample: #PBS -l nodes=1:ppn=1:gpus=1.'
        warnings.append(msg)
        gpus = 'missing'
    try:
        features
    except:
        features = 'missing'

    # rewrite memory to gb
    if mem == 'missing':
        pass
    else:
        m = re.search('(\d*)(\w*)', mem)
        memval = float(m.group(1))
        memsuff = m.group(2)
        if memsuff.lower() == "b":
            memval = memval/(1000**3)
        if memsuff.lower() in ("kb", "k"):
            memval = memval/(1000**2)
        if memsuff.lower() in ("mb", "m"):
            memval = memval/(1000)
        if memsuff.lower() in ("gb", "g"):
            memval = memval
        if memsuff.lower() in ("tb", "t"):
            memval = memval*(1000)

    # rewrite walltime to hours
    if walltime == 'missing':
        pass
    else:
        time = walltime.split(':')
        units = len(time)
        if units == 1:
            wtime = float(time[0])/(60**2)
        if units == 2:
            wtime = float(time[0])/(60)+float(time[1])/(60**2)
        if units == 3:
            wtime = float(time[0])+float(time[1])/60+float(time[2])/(60**2)
        if units == 4:
            wtime = float(time[0])*24+float(time[1])+float(time[2])/60+float(time[3])/(60**2)

    # this section is based on queue
    try:
        queue
    except NameError:
        queue = ""
    # gpus queue
    if queue == 'k40_gpu' or queue == 'k80_gpu':
        msg = 'The k40_gpu and k80_gpu queues have been retired. Please use the PBS option feature.\nExample1: #PBS -l feature=k40. Example2: #PBS -l feature=k80.'
        errors.append(msg)
    # no queue 
    else:
        if nodes == 'missing':
            pass
        else:
            #maxmem = nodes*stdmem
            try:
                nodes = int(nodes)
                if nodes > gpunodes:
                    msg = 'Cannot request more than %s node(s) per job.' % (gpunodes)
                    errors.append(msg)
            #else:
            except:
                nodename = []
                s = "".join(nodes)
                nodename.append(s)
                if len(nodename) > gpunodes:
                    msg = 'Cannot request more than %s node(s) per job.' % (gpunodes)
                    errors.append(msg)
        if ppn == 'missing':
            pass
        else:
            if features == 'k40':
                if ppn > k40cores:
                    msg = 'PPN request must be less than or equal to %s for K40 GPU nodes.' % (k40cores)
                    errors.append(msg)
            if features == 'k80' or features == 'missing':
                if ppn > k80cores:
                    msg = 'PPN request must be less than or equal to %s for K80 GPU nodes.' % (k80cores)
                    errors.append(msg)

        if walltime == 'missing':
            pass
        else:
            if wtime > gpuwtime:
                msg = 'Max walltime request is %shrs.' % (gpuwtime)
                errors.append(msg)

        if mem == 'missing':
            pass
        else:
            if memval > gpumem:
                msg = 'Max memory request is %sGB.' % (gpumem)
                errors.append(msg)

        if gpus == 'missing':
            pass
        else:
            if float(gpus) > k80gpus:
                msg = 'Max GPU request is %s.' % (k80gpus)
                errors.append(msg)

    #accounts = getaccounts()
    #if account == 'missing':
    #    if len(accounts) == 1:
    #        msg = 'PBS account name is required. Using default account "%s".\nAdd an account name to your job script to silence this warning.\nExample: #PBS -A %s.' %s (accounts[0],accounts[0])
    #        warning.append(msg)
    #    elif len(accounts) > 1:
    #        msg = 'PBS account name is required. Multiple accounts available.\nAdd one of your accounts to your job script.\nExample: #PBS -A %s.\nAvailable accounts:' %s (accounts[0])
    #        for line in accounts:
    #            msg = msg + '\n' + line
    #        error.append(msg)
    #    elif not accounts:
    #        msg = 'PBS account name is required. No valid account name for your user. Contact rcc_admin@mcw.edu.'
    #        error.append(msg)
    #else:
    #    if account not in accounts:
    #        msg = 'PBS account name is required. Requested account is not valid.\nAdd one of your accounts to your job script. Example: #PBS -A %s.\nAvailable accounts:' %s (accounts[0])
    #        for line in accounts:
    #            msg = msg + '\n' + line
    #        error.append(msg)
    #    elif not accounts:
    #        msg = 'PBS account name is required. No valid account name for your user. Contact rcc_admin@mcw.edu.'
    #        error.append(msg)
##### MAIN END #####

# pass the input through
sys.stdout.write(line1)
for line in lines:
    sys.stdout.write(line)

# check for duplicate errors and warnings
errors = list(set(errors))
warnings = list(set(warnings))
numerr = str(len(errors))
numwarn = str(len(warnings))
# prints errors for users
if errors or warnings:
    numerr = str(len(errors))
    m = os.popen(sendmailCommand, "w")
    m.write("To: Matt Flister <maflister@mcw.edu>\n")
    m.write("From: Torque Admin <torque-admin@mcw.edu>\n")
    m.write("Subject: Job Blocked by Torque Submit Filter\n")
    m.write('\nUser: ' + os.getlogin() + '\n')
    m.write('Submit Host: ' + os.uname()[1] + '\n')
    m.write('\nSubmit script has '+numerr+' error(s). Please see below.\n----------------------------------------------------------------------------------\n')
    if errors:
        sys.stderr.write('\nYour job submission script has '+numerr+' error(s). Please see below.\n----------------------------------------------------------------------------------\n')
        m.write('Errors:\n----------------------------------------------------------------------------------\n')
    for error in errors:
        sys.stderr.write(error)
        sys.stderr.write('\n----------------------------------------------------------------------------------\n')
        m.write(error)
        m.write('\n----------------------------------------------------------------------------------\n')
    if warnings:
	if float(numwarn) == 1:
            sys.stderr.write('\nYour job submission script has '+numwarn+' advisory. Please see below.\n----------------------------------------------------------------------------------\n')
	else:
            sys.stderr.write('\nYour job submission script has '+numwarn+' advisories. Please see below.\n----------------------------------------------------------------------------------\n')
        m.write('Advisory:\n')
    for warning in warnings:
	sys.stderr.write(warning)
        sys.stderr.write('\n----------------------------------------------------------------------------------\n')
	m.write(warning)
        m.write('\n----------------------------------------------------------------------------------\n')
    sys.stderr.write('\nFor more information please see http://wiki.rcc.mcw.edu/Torque_Submission_Scripts\nand http://wiki.rcc.mcw.edu/Tesla_GPU_Cluster.\n----------------------------------------------------------------------------------\n')
    m.write('Torque job script:\n')
    m.write(line1)
    for line in lines:
	m.write(line)
    m.write('\n----------------------------------------------------------------------------------\n')
    m.close()
    if errors:
        sys.exit(-1)
