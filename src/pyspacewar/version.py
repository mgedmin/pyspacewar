"""
PySpaceWar version number tracker.

$Id$
"""

svn_revision = "$Revision$"[11:-2]
version = "0.9.1svn"

if version.endswith('svn'):
    version += svn_revision
    # This is slightly misleading: svn_revision contains the last changed
    # revision number for version.py, not the revision number of the whole
    # repository.
