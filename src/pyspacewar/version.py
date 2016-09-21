"""
PySpaceWar version number tracker.
"""

version = "1.0.1.dev0"


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
        ver = p.communicate()[0].strip()
        if not isinstance(ver, str):
            ver = ver.decode('UTF-8', 'replace')
        return format % ver


if 'dev' in version:
    version += get_git_revision(format='+git.%s')
