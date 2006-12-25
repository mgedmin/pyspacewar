#!/usr/bin/env python
"""
A game inspired by Spacewar.

Copyright (c) 2005-2006 Marius Gedminas and Ignas Mikalajunas.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

$Id$
"""

import os
import sys

# Set up python path if running from a source tree.
pkgdir = os.path.join(os.path.dirname(__file__), 'src')
if os.path.isdir(pkgdir):
    sys.path.insert(0, pkgdir)

from pyspacewar.main import main
main()