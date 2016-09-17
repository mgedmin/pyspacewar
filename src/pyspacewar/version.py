"""
PySpaceWar version number tracker.
"""

version = "0.9.9.dev0"


def get_git_revision(unknown='', format=' (git %s)'):
    """Return the latest revision number of the files in the package."""
    import os
    import subprocess
    package_root = os.path.dirname(__file__)
    try:
        p = subprocess.Popen(['git', 'describe', '--always'],
                             cwd=package_root,
                             stdout=subprocess.PIPE)
    except OSError:  # pragma: nocover
        return unknown
    else:
        return format % p.communicate()[0].strip()


if 'dev' in version:
    version += get_git_revision(format='+git.%s')
