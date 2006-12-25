"""
PySpaceWar version number tracker.

$Id$
"""

svn_revision = "$Revision$"[11:-2]
version = "0.9.3"

if version.endswith('svn'):
    version += svn_revision
    # This is slightly misleading: svn_revision contains the last changed
    # revision number for version.py, not the revision number of the whole
    # repository.  Using os.popen('svnversion').read() would be better, but
    # only if the end-user has subversion installed.
