# -*- coding: utf-8 -*-

import os
import time



class ProcessRunningException(Exception): pass
class PidfileNonExistentException(Exception): pass

class PidfileWatcher:
    """Watches if a pidfile exists. If exist at time of initialization of this
    instance, may also be used to check if the pidfile is changed or deleted.
      This is useful for subprocesses who may want to exit after main process
    is terminated.
    """
    __lastcheck = 0
    pid = None
    pidfile = None

    def __init__(self, path):
        self.pidfile = path
        self.__lastcheck = time.time()
        try:
            pidfile = open(self.pidfile, 'r')
            self.pid = pidfile.read()
            pidfile.close()
        except:
            raise PidfileNonExistentException()

    def check(self):
        try:
            pidfile = open(self.pidfile, 'r')
            pid = pidfile.read()
            pidfile.close()
        except:
            return False
        return pid == self.pid
        

class PidfileCreator:
    def __init__(self, path, log=sys.stdout.write, warn=sys.stderr.write):
        self.pidfile = path
        self.log = log
        self.warn = warn

    def __enter__(self):
        try:
            self.pidfd = os.open(self.pidfile, os.O_CREAT|os.O_WRONLY|os.O_EXCL)
            self.log('locked pidfile %s' % self.pidfile)
        except OSError as e:
            if e.errno == errno.EEXIST:
                pid = self._check()
                if pid:
                    self.pidfd = None
                    raise ProcessRunningException('process already running in %s as pid %s' % (self.pidfile, pid))
                else:
                    os.remove(self.pidfile)
                    self.warn('removed staled lockfile %s' % (self.pidfile))
                    self.pidfd = os.open(self.pidfile, os.O_CREAT|os.O_WRONLY|os.O_EXCL)
            else:
                raise

        os.write(self.pidfd, str(os.getpid()))
        os.close(self.pidfd)
        return self

    def __exit__(self, t, e, tb):
        # return false to raise, true to pass
        if t is None:
            # normal condition, no exception
            self._remove()
            return True
        elif t is PidfileProcessRunningException:
            # do not remove the other process lockfile
            return False
        else:
            # other exception
            if self.pidfd:
                # this was our lockfile, removing
                self._remove()
        return False

    def _remove(self):
        self.log('removed pidfile %s' % self.pidfile)
        os.remove(self.pidfile)

    def _check(self):
        """check if a process is still running

        the process id is expected to be in pidfile, which should exist.

        if it is still running, returns the pid, if not, return False."""
        with open(self.pidfile, 'r') as f:
            try:
                pidstr = f.read()
                pid = int(pidstr)
            except ValueError:
                # not an integer
                self.log("not an integer: %s" % pidstr)
                return False
            try:
                os.kill(pid, 0)
            except OSError:
                self.log("can't deliver signal to %s" % pid)
                return False
            else:
                return pid
