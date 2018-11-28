#!/usr/bin/env python

from __future__ import print_function
import os
import os.path
import subprocess
import sys
from time import localtime, strftime

class Logger:
    def write(self, jobinfo):
        raise NotImplementedError()


class TextLogger(Logger):
    def __init__(self, fp):
        self.fp = fp

    def write(self, jobinfo):
        tstr = strftime("%Y-%m-%d %H:%M:%S", localtime())
        #with open(self.filename, "a", encoding="utf-8") as logfile:
        self.fp.write(u"{0}\t{1}\t{2}\t{3}\t{4}\n".format(
            tstr, 
            jobinfo.get('jobid', 0), 
            jobinfo.get('cwd', "NONE"),
            jobinfo['filename'],
            jobinfo.get('jobname', jobinfo['filename'])
        ))


class SQLiteLogger(Logger):
    def __init__(self, connection, table_name="jobs", create_always=False):
        self.conn = connection
        self.table_name = table_name
        self.ensure_table_exists(create_always=create_always)

    def ensure_table_exists(self, create_always=False):
        r = self.conn.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", 
            (self.table_name, )
            )
        if not len(r.fetchall()):      
            self.create_table()        
        elif create_always:
            self.delete_table()
            self.create_table()
        

    def delete_table(self):        
        self.conn.execute("""DROP TABLE {}""".format(self.table_name))
        self.conn.commit()


    def create_table(self):        
        self.conn.execute("""CREATE TABLE {}
            (id INTEGER primary key,
            jobid INT, 
            datetime DATETIME,
            directory TEXT,
            jobscript TEXT,
            jobname TEXT
            )""".format(self.table_name))
        self.conn.commit()

    def write(self, jobinfo):
        tstr = strftime("%Y-%m-%d %H:%M:%S", localtime())

        self.conn.execute("""INSERT INTO {}(jobid, datetime, directory, jobscript, jobname)
          VALUES (?, ?, ?, ?, ?)""".format(self.table_name),
          (jobinfo['jobid'], tstr, jobinfo['cwd'], jobinfo['filename'], jobinfo['jobname'])
          )
        self.conn.commit()

class JobRunner:
    def __init__(self, filename, logger):
        self.filename = filename
        self.logger = logger

    
    def run(self):
        try:
            output = self.submit()
            jobinfo = self.get_jobinfo(output)
            jobinfo['filename'] = self.filename            
            self.logger.write(jobinfo)
        except IOError as e:            
            print(e)
            
    
    def submit(self):
        raise NotImplementedError()


    def get_jobinfo(self, output):
        raise NotImplementedError()


class EulerJobRunner(JobRunner):
    def submit(self):
        subcmd = "bsub"
        with open(self.filename) as infile:
            outp = subprocess.check_output(subcmd, stdin=infile)
            if sys.version_info[0] == 3:
                outp = outp.decode("utf-8")
            outlines = outp.split('\n')
            print(outlines[0])
        return outlines

    
    def get_jobinfo(self, output):
        jobinfo = {'jobname': self.filename}

        with open(self.filename) as infile:
            lines = infile.readlines()        
            for l in lines:
                splits = l.strip().split()
                if len(splits) < 2:
                    continue
                if splits[0] == "#BSUB" and splits[1] == "-J":
                    jobinfo['jobname'] = splits[2]

        jobinfo['jobid'] = output[0].split()[1].replace("<", "").replace(">", "")
        cwd = os.getcwd()
        cwd = cwd.replace('/cluster/home/thoelef', '~')
        cwd = cwd.replace('/cluster/work/beta3/thoelef', '~/escr')
        jobinfo['cwd'] = cwd

        return jobinfo


class DaintJobRunner(JobRunner):
    def submit(self):
        subcmd = "sbatch"
        outp = subprocess.check_output([subcmd, self.filename])
        if sys.version_info[0] == 3:
            outp = outp.decode("utf-8")
        outlines = outp.split('\n')
        print(outlines[0])
        return outlines


    def get_jobinfo(self, output):
        jobinfo = {'jobname': self.filename}

        with open(self.filename) as infile:
            lines = infile.readlines()     

            for l in lines:
                splits = l.strip().split()
                if len(splits) < 2:
                    continue
                if splits[0] == "#SBATCH" and splits[1].startswith("--job-name"):
                    jobname = splits[1].split('=')[1].replace('"', '')
                    jobinfo['jobname'] = jobname

        jobinfo["jobid"] = output[0].split()[3]
        cwd = os.getcwd()
        cwd = cwd.replace('/users/thoelef', '~')
        cwd = cwd.replace('/mnt/lnec/fthoele', '~/mscr')
        cwd = cwd.replace('/scratch/rosa/fthoele', '~/rscr')
        jobinfo['cwd'] = cwd

        return jobinfo


def get_cluster(hostname=None):
    homedir = os.getenv("HOME")
    clusters = {
        "daint": {"logfile": os.path.join(homedir, "log-daint.txt"),
                "runner": DaintJobRunner},
        "euler": {"logfile": os.path.join(homedir, "log-euler.txt"),
                "runner": EulerJobRunner},        
    }

    if not hostname:
        hostname = os.getenv("HOSTNAME")

    if hostname.startswith("eu"):
        return clusters['euler']
    elif "daint" in hostname:
        return clusters['daint']
    else:
        raise NotImplementedError("Unknown cluster: {}".format(hostname))


def run(runner_class, logger):
    filenames = sys.argv[1:]
    for fn in filenames:
        runner = runner_class(fn, logger)
        runner.run()


if __name__ == "__main__":
    cluster = get_cluster()
    
    from io import open
    
    with open(cluster['logfile'], "a", encoding="utf-8") as logfile:
        logger = TextLogger(logfile)
        run(cluster['runner'], logger)