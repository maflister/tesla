#!/bin/bash
if [[ $EUID -ne 0 ]]; then
   export TMPDIR=/scratch/local/$USER/$PBS_JOBID
   export SCRATCH=/scratch/global/$USER/$PBS_JOBID
fi
