"""
Function to drop root privileges
<http://stackoverflow.com/questions/2699907/dropping-root-permissions-in-python>

This has to be used in 2 places:
* `run_as.py`, whose root privilege will be passed to `tunnel.py`. Root is
  no more needed after `tunnel.py` is started, and will be dropped.
* `tunnel.py`, which will need root to setup TUN device. After that, root will
  be dropped.
"""

import grp
import os
import pwd

def dropRoot(uid_name='nobody', gid_name='nobody'):
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(gid_name).gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)

    # Ensure a very conservative umask
    old_umask = os.umask(077)
