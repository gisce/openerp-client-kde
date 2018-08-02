##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
# Copyright (c) 2007-2009 Albert Cervera i Areny <albert@nan-tic.com>
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

import configparser
import os
import sys
from Koo import Rpc
from . import Debug
from PyQt5.QtCore import QDir, QUrl
import traceback


class Settings(object):
    """
    The ConfigurationManager class handles Koo settings information.
    Those settings can be specified in the command line, .koorc configuration
    file or koo server module.
    """

    rcFile = False
    options = {
        'login.db': 'test',
        'login.url': 'http://admin@localhost:8069',
        'pyrossl.certdir':  os.path.join(sys.prefix, 'share/Koo/certs'),
        'pyrossl.cert': 'client.pem',
        'pyrossl.ca_cert': 'ca.pem',
        'pyrossl.key': None,
        'pyrossl.postconncheck': 1,
        'pyro.dns_uri': 1,
        'pyro.tracelevel': 0,
        'pyro.logfile': '/tmp/pyro_client.log',
        'path.share': os.path.join(sys.prefix, 'share/Koo/'),
        'path.pixmaps': os.path.join(sys.prefix, 'share/pixmaps/Koo/'),
        'path.ui': os.path.join(sys.prefix, 'share/Koo/ui'),
        'tip.autostart': True,
        'tip.position': 0,
        'client.default_path': os.path.expanduser('~'),
        'client.language': False,
        'client.debug': False,
        'client.sentry_dsn': 'sync+http://77cb0018d10842209ec638aeeffedf1a:3be0b6af34d14f7cb562b776e490ad8d@sentry.gisce.net/128',
        'koo.print_directly': False,
        'koo.stylesheet': '',
        'koo.tabs_position': 'top',
        'koo.tabs_closable': True,
        'koo.show_toolbar': True,
        'koo.sort_mode': 'all_items',
        'koo.pos_mode': False,
        'koo.enter_as_tab': False,
        'kde.enabled': True,
        'koo.attachments_dialog': False,
        'koo.load_on_open': True,
        'koo.smtp_server': 'mail.nan-tic.com',
        'koo.smtp_from': 'koo@nan-tic.com',
        'koo.smtp_backtraces_to': 'backtraces@nan-tic.com',
        'koo.custom_ui_dir': False,
        'koo.enable_event_filters': False,  # Not recommended for performance reasons
    }

    @staticmethod
    def saveToFile():
        """
        Stores current settings in the appropiate config file.
        
        :return: True
        :rtype: bool
        """
        if not Settings.rcFile:
            # If no file was specified we try to read it from environment
            # variable o standard path
            Settings.rcFile = os.environ.get('TERPRC') or os.path.join(
                str(QDir.toNativeSeparators(QDir.homePath())), '.koorc')
        try:
            parser = configparser.ConfigParser()
            sections = {}
            for option in list(Settings.options.keys()):
                if not len(option.split('.')) == 2:
                    continue

                optionSection, optionName = option.split('.')

                if not parser.has_section(optionSection):
                    parser.add_section(optionSection)

                # Do not store 'open' settings unless the 'always' flag is
                # present.
                value = str(Settings.options[option])
                if optionSection == 'open' and not Settings.value('open.always'):
                    value = ''

                parser.set(optionSection, optionName, value)

            # Set umask='077' to ensure file permissions used are '600'.
            # This way we can store passwords and other information safely.
            oldUmask = os.umask(63)
            try:
                with open(Settings.rcFile, 'w') as f:
                    parser.write(f)
            except Exception as e:
                Debug.warning('Unable to write config file %s !' %
                              Settings.rcFile)

            finally:
                f.close()
            os.umask(oldUmask)
        except Exception as e:
            Debug.warning('Unable to write config file %s !' % Settings.rcFile)

        return True

    @staticmethod
    def loadFromFile():
        """
        Loads settings from the appropiate config file.
        :return:
        """
        if not Settings.rcFile:
            # If no file was specified we try to read it from environment
            # variable o standard path
            Settings.rcFile = os.environ.get('TERPRC') or os.path.join(
                str(QDir.toNativeSeparators(QDir.homePath())), '.koorc')
        try:
            if not os.path.isfile(Settings.rcFile):
                Settings.save()
                return False

            p = configparser.ConfigParser()
            p.read([Settings.rcFile])
            for section in p.sections():
                for (name, value) in p.items(section):
                    if value == 'True' or value == 'true':
                        value = True
                    if value == 'False' or value == 'false':
                        value = False
                    if value == 'None' or value == 'none':
                        value = None
                    Settings.options[section + '.' + name] = value
        except Exception as e:
            Debug.warning('Unable to read config file %s !' % Settings.rcFile)
        return True

    @staticmethod
    def loadFromRegistry():
        """
        Loads settings from Windows registry.
        :return:
        """

        if os.name != 'nt':
            return

        languages = {
            '1027': 'ca',
            '1031': 'de',
            '1033': 'en',
            '1034': 'es',
            '1040': 'it',
        }

        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Koo")
        value, value_type = winreg.QueryValueEx(key, "Language")
        Settings.options['client.language'] = languages.get(value, False)

    @staticmethod
    def setValue(key, value):
        """
        Sets the value for the given key.
        :param key:
        :param value:
        :return:
        """
        Settings.options[key] = value

    @staticmethod
    def value(key, defaultValue=None, toType=None):
        """
        Returns the value for the given key.

        If defaultValue parameter is given, defaultValue is returned if the
        key does not exist.
        If type is given, it will convert the value to the given type.
        :param key:
        :param defaultValue:
        :param toType:
        :return:
        """
        value = Settings.options.get(key, defaultValue)
        if toType == int:
            return int(value)
        return value

    @staticmethod
    def get(key, defaultValue=None):
        """
        Returns the value associated with the given key. If the key has no valu
        returns defaultValue
        :param key:
        :param defaultValue:
        :return:
        """
        return Settings.options.get(key, defaultValue)

    @staticmethod
    def loadFromServer():
        """
        Tries to load settings from koo server module.
        If the module is not installed, no exception or error is thrown.
        :return:
        """
        try:
            settings = Rpc.session.call(
                '/object', 'execute', 'nan.koo.settings', 'get_settings')
        except:
            settings = {}
        new_settings = {}
        for key, value in settings.items():
            if key == 'stylesheet':
                new_settings['koo.stylesheet_code'] = value
                continue
            if key != 'id':
                new_settings['koo.%s' % key] = value
        Settings.options.update(new_settings)
        Rpc.ViewCache.exceptions = Settings.options.get(
            'koo.cache_exceptions', [])

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
