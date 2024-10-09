"""
PySpaceWar version number tracker.
"""

# zest.releaser insists on this being stored in a variable called __version__
# but we want version elsewhere in the codebase.
__version__ = '1.2.0'
version = __version__


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
        return format % ver.replace('-', '.') if ver else unknown


if 'dev' in version:
    version += get_git_revision(format='+git.%s')
