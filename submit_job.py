#!/usr/bin/env python

from __future__ import print_function
import os
import os.path
import subprocess
import sys
from time import localtime, strftime

subcmd = "bsub"

def write_to_log(logfile, fn, jobname, outlines):
    tstr = strftime("%Y-%m-%d %H:%M:%S", localtime())
    jobid = outlines[0].split()[1].replace("<", "").replace(">", "")
    cwd = os.getcwd()
    cwd = cwd.replace('/cluster/home/thoelef', '~')
    cwd = cwd.replace('/cluster/work/beta3/thoelef', '~/escr')
   
    logfile.write("{0}\t{1}\t{2}\t{3}\t{4}\n".format(tstr, jobid, cwd, fn, jobname))
    

def get_euler_jobname(filename):
    jobname = filename
    with open(filename) as infile:
        lines = infile.readlines()        
        for l in lines:
            splits = l.strip().split()
            if len(splits) < 2:
                continue
            if splits[0] == "#BSUB" and splits[1] == "-J":
                jobname = splits[2]
    return jobname


def submit_job(infile_filename):
    with open(infile_filename) as infile:
        outp = subprocess.check_output(subcmd, stdin=infile).decode("utf-8")
        outlines = outp.split('\n')
        print(outlines[0])
    return outlines


def process_file(fn, logfile):
    if not os.path.isfile(fn):
        print("Invalid filename: ", fn)
        return
    
    outlines = submit_job(fn)
    jobname = get_euler_jobname(fn)
    write_to_log(logfile, fn, jobname, outlines)


def run(logfile):
    filenames = sys.argv[1:]
    for fn in filenames:
        process_file(fn, logfile)


if __name__ == "__main__":
    logfile_fn = "/cluster/home/thoelef/log-euler.txt"
    with open(logfile_fn, "a", encoding="utf-8") as log:
        run(log)