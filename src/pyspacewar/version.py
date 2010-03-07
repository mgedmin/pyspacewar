"""
PySpaceWar version number tracker.
"""

version = "0.9.7dev"


def get_bzr_revision(unknown='', format='+r%s'):
    """Return the latest revision number of the files in the package."""
    import os, subprocess, pyspacewar
    package_root = os.path.dirname(__file__)
    try:
        p = subprocess.Popen(['bzr', 'revno', package_root],
                             stdout=subprocess.PIPE)
    except OSError:
        return unknown
    else:
        return format % p.communicate()[0].strip()


if version.endswith('dev'):
    version += get_bzr_revision()

