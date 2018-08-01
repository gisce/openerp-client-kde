##############################################################################
#
# Copyright (c) 2008 Albert Cervera i Areny <albert@nan-tic.com>
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
import sys
import zipfile
from zipimport import zipimporter


def get_zipfiles(directory):
    """
    Return a list of the zip files on the directory

    :param directory: Directory to list
    :return: List of the zipfiles on the directory
    :rtype: list(str)
    """
    ret = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            if full_path.endswith(".zip"):
                ret.append(full_path)
    return ret


def scan(module, directory):
    """
    This helper function searches all available modules in a given directory.
    It's used to scan the Plugins, Fields, View and Search directories.
    :param module:
    :param directory:
    :return:
    """
    pluginImports = __import__(module, globals(), locals())
    # Check if it's being run using py2exe or py2app environment
    frozen = getattr(sys, 'frozen', None)
    if frozen == 'macosx_app' or hasattr(pluginImports, '__loader__'):
        # If it's run using py2exe or py2app environment, all files will be in
        # a single zip file and we can't use listdir() to find all available
        # plugins.
        pluginsPath = os.path.dirname(pluginImports.__loader__.path)
        zipFiles = get_zipfiles(os.path.dirname(pluginImports.__loader__.path))
        moduleDir = os.sep.join(module.split('.'))
        files = [file for file in zipFiles if moduleDir in file]
        import importlib
        importlib.import_module("Plugins.ViewSettings")

        #for zfile in files:
        #    importer = zipimporter(zfile)
        #    if importer.is_package(zfile):
        #        importer.load_module("__init__")
                #d = os.path.dirname(zfile)
                #newModule = os.path.basename(zfile)[:-4]
                #__import__('%s.%s' % (module, newModule),
                #           globals(), locals(), [newModule])


        #files = [file for file in files if '__init__.py' in file]
        #for file in files:

    else:
    """ 
    if True:
        for i in os.listdir(directory):
            path = os.path.join(directory, i, '__init__.py')
            if os.path.isfile(path):
                __import__('%s.%s' % (module, i), globals(), locals(), [i])
