"""
PySpaceWar version number tracker.

$Id$
"""

version = "0.9.4+svn"


def get_svn_revision(unknown=''):
    """Return the latest revision number of the files in the package."""
    import os, subprocess, pyspacewar
    package_root = os.path.dirname(__file__)
    try:
        p = subprocess.Popen(['svnversion', package_root],
                             stdout=subprocess.PIPE)
    except OSError:
        return unknown
    else:
        return p.communicate()[0].strip()


if version.endswith('svn'):
    version += get_svn_revision()

