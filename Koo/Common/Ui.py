##############################################################################
#
# Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                    http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import os
import subprocess
import tempfile
import importlib.util


def uiToModule(filePath):
    return os.path.split(filePath[:-3])[-1]


def loadUiType(fileName):
    """Load a Qt Designer .ui file and return (Ui_class, None).

    Uses pyside6-uic to compile the .ui file on-the-fly so it works
    with both installed and development trees without a pre-build step.
    Falls back to loading a pre-compiled Python module from the 'ui'
    package when pyside6-uic is not available.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as tmp:
            tmpPath = tmp.name
        try:
            subprocess.run(
                ['pyside6-uic', '-o', tmpPath, fileName],
                check=True,
                capture_output=True,
            )
            spec = importlib.util.spec_from_file_location('_koo_tmp_ui', tmpPath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            if os.path.exists(tmpPath):
                os.unlink(tmpPath)
        uiClasses = [x for x in dir(mod) if x.startswith('Ui_')]
        if not uiClasses:
            raise ValueError('No Ui_ class found in compiled output for %s' % fileName)
        return (getattr(mod, uiClasses[0]), None)
    except Exception:
        module = uiToModule(fileName)
        module = __import__('ui.%s' % module, globals(), locals(), [module])
        uiClasses = [x for x in dir(module) if x.startswith('Ui_')]
        ui = getattr(module, uiClasses[0])
        return (ui, None)

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
