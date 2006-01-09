"""
PySpaceWar version number tracker.

$Id$
"""

svn_revision = "$Revision$"
version = "0.9.0+svn"

if version.endswith('svn'):
    version += svn_revision
