#!/usr/bin/python

#---------------------------------------------------------------#
# File: $TORQUE_HOMEDIR/sbin/qsub_filter_gpu.py
# Auth: Matthew Flister <maflister@mcw.edu>
# Desc: This is a GPU specific filter for Torque's qsub command.
#---------------------------------------------------------------#


#TODO
# logging?


import sys, re, os, pwd, grp

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
exemptUsers = ["akrruser"]
exemptJobs = ["matlab"]

sendmailCommand = "/usr/sbin/sendmail -t"

### DO NOT CHANGE ANYTHING BELOW THIS ###
# get default account or list of accounts
def get_accounts_cli(user):
    accounts = {}
    command = 'mam-list-accounts -u %s --show "Name,Active,Description" --format csv' % user
    cli_data = os.popen(command, "r").readlines()[1:]
    for i in cli_data:
        account,isactive,description = i.strip().split(',')
        if isactive == 'True':
            accounts[account] = description
    return accounts

# check group membership
def getgroups(user):
    gids = [g.gr_gid for g in grp.getgrall() if user in g.gr_mem]
    gid = pwd.getpwnam(user).pw_gid
    gids.append(grp.getgrgid(gid).gr_gid)
    return [grp.getgrgid(gid).gr_name for gid in gids]

def checkPBS(lines):
    pbs = False
    for line in lines:
        if "#PBS" in line:
            pbs = True
            break
    return pbs

def getCommands(lines):
    commands = []
    for line in lines:
        if "#PBS" in line or "#!" in line or "#" in line:
            continue
        elif not line.strip():
            continue
        else:
            commands.append(line)
    return commands

errors = []
warnings = []

# grab lines from stdin
lines = sys.stdin.readlines()
pbs = checkPBS(lines)

if len(sys.argv) == 2:
    if pbs:
        for line in lines:
            if not line.strip(): # skip blank lines between shabang and first #PBS line
                continue
            if "#" in line and "#PBS" not in line:
                continue
            m = re.search('(?<=#PBS -N )(\w+)', line)
            if (m):
                jobname = m.group(0)
            m = re.search('(?<=#PBS -A )(\w+)', line)
            if (m):
                account = m.group(0)
            m = re.search('#PBS\s*\-l\s*\S*nodes\=(\w+)', line)
            if (m):
                nodes = m.group(1)
                try:
                    int(nodes)
                    nodes = int(nodes)
                except:
                    nodes = 1
            m = re.search('#PBS\s*\-l\s*\S*ppn\=(\d+)', line)
            if (m):
                ppn = m.group(1)
            m = re.search('#PBS\s*\-l\s*\S*gpus\=(\d+)', line)
            if (m):
                gpus = m.group(1)
            m = re.search('#PBS\s*\-l\s*\S*mem\=(\w+)', line)
            if (m):
                mem = m.group(1)
            m = re.search('#PBS\s*\-l\s*\S*walltime\=(\d+(:\d+)*)', line)
            if (m):
                walltime = m.group(1)
            m = re.search('#PBS\s*\-l\s*\S*feature\=(\w+)', line)
            if (m):
                features = m.group(1)
            m = re.search('(?<=#PBS -q )(\w+)', line)
            if (m):
                queue = m.group(0)
            m = re.search('#PBS\s*\-l\s*\S*software\=(\w+)\:(\d+)', line)
            if (m):
                software = m.group(1)
                licCount = m.group(2)
            # check for module load
            m = re.search('(?<=module load )(\w+)\/(\S+)', line)
            if (m):
                app = m.group(1)
                version = m.group(2)

else:
    # get qsub command line
    line = ' '.join(sys.argv[1:])
    if line:
        m = re.findall('\-N\s*(\w+)', line)
        if (m):
            jobname = m[-1]
        m = re.search('\-A\s*(\w+)', line)
        if (m):
            account = m.group(1)
        m = re.search('\-l\s*\S*nodes\=(\w+)', line)
        if (m):
            nodes = m.group(1)
            try:
                int(nodes)
                nodes = int(nodes)
            except:
                nodes = 1
        m = re.search('\-l\s*\S*ppn\=(\d+)', line)
        if (m):
            ppn = m.group(1)
        m = re.search('\-l\s*\S*mem\=(\w+)', line)
        if (m):
            mem = m.group(1)
        m = re.search('\-l\s*\S*walltime\=(\d+(:\d+)*)', line)
        if (m):
            walltime = m.group(1)
        m = re.search('\-l\s*\S*feature\=(\w+)', line)
        if (m):
            features = m.group(1)
        m = re.search('\-q\s*(\w+)', line)
        if (m):
            queue = m.group(1)
        m = re.search('\-I', line)
        if (m):
            interactive = True
        m = re.search('\-l\s*\S*software\=(\w+)\:(\d+)', line)
        if (m):
            software = m.group(1)
            licCount = m.group(2)

    # deal with script
    if pbs:
        for line in lines:
            if not line.strip(): # skip blank lines between shabang and first #PBS line
                continue
            if "#" in line and "#PBS" not in line:
                continue
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
                        int(nodes)
                        nodes = int(nodes)
                    except:
                        nodes = 1
            try:
                ppn
            except:
                m = re.search('#PBS\s*\-l\s*\S*ppn\=(\d+)', line)
                if (m):
                    ppn = m.group(1)
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
            try:
                gpus
            except:
                m = re.search('#PBS\s*\-l\s*\S*gpus\=(\d+)', line)
                if (m):
                    gpus = m.group(1)
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
            try:
                software
            except:
                m = re.search('#PBS\s*\-l\s*\S*software\=(\w+)\:(\d+)', line)
                if (m):
                    software = m.group(1)
                    licCount = m.group(2)
            try:
                app
            except:
                m = re.search('(?<=module load )(\w+)\/(\S+)', line)
                if (m):
                    app = m.group(1)
                    version = m.group(2)

##### MAIN START #####
# for each must-have attribute check if exists and exit if not 
try:
    jobname
except:
    msg = 'PBS job name is missing. Please consider adding a job name to identify your work.\nExample: #PBS -N JobName.'
    warnings.append(msg)
    jobname = 'missing'
try:
    account
except:
    account = 'missing'
try:
    nodes = int(nodes)
except:
    msg = 'PBS nodes request is required. Example: #PBS -l nodes=1:ppn=1.'
    errors.append(msg)
    nodes = 'missing'
try:
    ppn = int(ppn)
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
try:
    software
except:
    software = 'missing'
try:
    interactive
except:
    interactive = False
try:
    app
except:
    app = False

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
        maxmem = nodes*gpumem
        nodes = int(nodes)
        if nodes > gpunodes:
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
    if interactive:
        if nodes > gpunodes:
            msg = 'Max nodes request must be less than or equal to %s for interactive jobs.' % (gpunodes)
            errors.append(msg)
        if ppn > 4:
            msg = 'Max ppn request must be less than or equal to 4 for interactive jobs.'
            errors.append(msg)
        if mem == "missing":
            pass
        else:
            if memval > intermem:
                msg = 'Max memory request must be less than or equal to %sgb for interactive jobs.' % (intermem)
                errors.append(msg)
        if walltime == 'missing':
            pass
        else:
            if wtime > interwtime:
                msg = 'Max walltime request for interactive job is %shrs.' % (interwtime)
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

# Check for matlab licensing if matlab is going to run
# #PBS -l software=matlab:1
# module load matlab/2019b
# /path/to/matlab -nodisplay -nosplash myscript.m
groups = getgroups(username)
licMatlab = False
if software == "matlab" and licCount != 0:
    licMatlab = True
matlab = False
for line in lines:
    if "matlab " in line:
        print 'test'
        matlab = True
if licMatlab or matlab:
    if "matlab_users" not in groups:
        msg = 'You are not authorized to use MATLAB on this cluster. Please contact rcc_admin@mcw.edu'
        errors.append(msg)
    elif not licMatlab:
        msg = 'You are attempting to run MATLAB but have not requested a license. Example: #PBS -l software=matlab:1'
        errors.append(msg)
    elif not matlab:
        msg = 'You have specified a MATLAB license but are not running MATLAB in your job.'
        errors.append(msg)

# Check for module load and filter for apps with special reqs
if app:
    if app == "pytorch" and version >= '1.3.1':
        if not features or features != "k80":
            msg = 'Pytorch >= 1.3.1 requires a K80 GPU. Add "#PBS -l feature=k80" to the #PBS header of your script.'
            errors.append(msg)

##### MAIN END #####

# pass the input through
for line in lines:
    sys.stdout.write(line)

# check for duplicate errors or warnings
if username in exemptUsers or jobname in exemptJobs:
    errors = []
    warnings = []
elif pbs or interactive:
    errors = list(set(errors))
    warnings = list(set(warnings))
    numerr = str(len(errors))
    numwarn = str(len(warnings))
else:
    errors = []
    warnings = []
    msg = 'PBS options are missing. Please make sure you are submitting a Torque script.'
    errors.append(msg)

# prints errors for users
if errors or warnings:
    numerr = str(len(errors))
    #m = os.popen(sendmailCommand, "w")
    #m.write("To: Matt Flister <maflister@mcw.edu>\n")
    #m.write("From: <no-reply@rcc.mcw.edu>\n")
    #m.write("Subject: Job Blocked by Torque Submit Filter\n")
    #m.write('\nUser: ' + os.getlogin() + '\n')
    #m.write('Submit Host: ' + os.uname()[1] + '\n')
    #m.write('\nSubmit script has '+numerr+' error(s). Please see below.\n----------------------------------------------------------------------------------\n')
    if errors:
        sys.stderr.write('\nYour job submission script has '+numerr+' error(s). Please see below.\n----------------------------------------------------------------------------------\n')
    #    m.write('Errors:\n----------------------------------------------------------------------------------\n')
    for error in errors:
        sys.stderr.write(error)
        sys.stderr.write('\n----------------------------------------------------------------------------------\n')
    #    m.write(error)
    #    m.write('\n----------------------------------------------------------------------------------\n')
    if warnings:
	if int(numwarn) == 1:
            sys.stderr.write('\nYour job submission script has '+numwarn+' advisory. Please see below.\n----------------------------------------------------------------------------------\n')
	else:
            sys.stderr.write('\nYour job submission script has '+numwarn+' advisories. Please see below.\n----------------------------------------------------------------------------------\n')
    #    m.write('Advisory:\n')
    for warning in warnings:
	sys.stderr.write(warning)
        sys.stderr.write('\n----------------------------------------------------------------------------------\n')
#	m.write(warning)
#        m.write('\n----------------------------------------------------------------------------------\n')
    sys.stderr.write('\nFor more information please see http://wiki.rcc.mcw.edu/Torque_Submission_Scripts\nand http://wiki.rcc.mcw.edu/Tesla_GPU_Cluster.\n----------------------------------------------------------------------------------\n')
#    m.write('Torque job script:\n')
#    for line in lines:
#	m.write(line)
#    m.write('\n----------------------------------------------------------------------------------\n')
#    m.close()
    if errors:
        sys.exit(-1)
