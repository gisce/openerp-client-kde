##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

import ConfigParser, optparse
import os
import sys
import gettext
import rpc
from PyQt4.QtCore import QDir

def get_home_dir():
	return str(QDir.toNativeSeparators(QDir.homePath()))

class configmanager(object):
	def __init__(self,fname=None):
		self.options = {
			'login.login': 'demo',
			'login.server': 'localhost',
			'login.port': '8069',
			'login.db': 'terp',
			'login.protocol': 'http://',
			'path.share': os.path.join(sys.prefix, 'share/ktiny/'),
			'path.pixmaps': os.path.join(sys.prefix, 'share/pixmaps/ktiny/'),
			'path.ui': os.path.join(sys.prefix, 'share/ktiny/ui'), 
			'tip.autostart': False,
			'tip.position': 0,
			'printer.preview': True,
			'logging.logger': '',
			'logging.level': 'DEBUG',
			'logging.output': 'stdout',
			'logging.verbose': False,
			'client.default_path': os.path.expanduser('~'),
			'stylesheet' : '',
			'tabs_position' : 'left',
			'show_toolbar' : True,
			'sort_mode' : 'all_items'
		}
		parser = optparse.OptionParser()
		parser.add_option("-c", "--config", dest="config",help=_("specify alternate config file"))
		parser.add_option("-v", "--verbose", action="store_true", default=False, dest="verbose", help=_("enable basic debugging"))
		parser.add_option("-d", "--log", dest="log_logger", default='', help=_("specify channels to log"))
		parser.add_option("-l", "--log-level", dest="log_level",default='ERROR', help=_("specify the log level: INFO, DEBUG, WARNING, ERROR, CRITICAL"))
		parser.add_option("-u", "--user", dest="login", help=_("specify the user login"))
		parser.add_option("-p", "--port", dest="port", help=_("specify the server port"))
		parser.add_option("-s", "--server", dest="server", help=_("specify the server ip/name"))
		parser.add_option("", "--stylesheet", dest="stylesheet", help=_("specify stylesheet to apply"))
		(opt, args) = parser.parse_args()


		self.rcfile = fname or opt.config or os.environ.get('TERPRC') or os.path.join(get_home_dir(), '.ktinyrc')
		self.load()

		if opt.verbose:
			self.options['logging.verbose']=True
		self.options['logging.logger'] = opt.log_logger
		self.options['logging.level'] = opt.log_level
		self.options['stylesheet'] = opt.stylesheet
	
		for arg in ('login', 'port', 'server'):
			if getattr(opt, arg):
				self.options['login.'+arg] = getattr(opt, arg)

	def save(self, fname = None):
		try:
			p = ConfigParser.ConfigParser()
			sections = {}
			for o in self.options.keys():
				if not len(o.split('.'))==2:
					continue
				osection,oname = o.split('.')
				if not p.has_section(osection):
					p.add_section(osection)
				p.set(osection,oname,self.options[o])
			p.write(file(self.rcfile,'wb'))
		except:
			import logging
			log = logging.getLogger('common.options')
			log.warn('Unable to write config file %s !'% (self.rcfile,))
		return True

	def load(self, fname=None):
		try:
			self.rcexist = False
			if not os.path.isfile(self.rcfile):
				self.save()
				return False
			self.rcexist = True

			p = ConfigParser.ConfigParser()
			p.read([self.rcfile])
			for section in p.sections():
				for (name,value) in p.items(section):
					if value=='True' or value=='true':
						value = True
					if value=='False' or value=='false':
						value = False
					self.options[section+'.'+name] = value
		except Exception, e:
			import logging
			log = logging.getLogger('common.options')
			log.warn('Unable to read config file %s !'% (self.rcfile,))
		return True

	def __setitem__(self, key, value):
		self.options[key]=value

	def __getitem__(self, key):
		return self.options[key]

	def get(self, key, defaultValue):
		return self.options.get(key, defaultValue)

	def loadSettings(self):
		try:
			settings = rpc.session.call( '/object', 'execute', 'nan.ktiny.settings', 'get_settings' )[0]
		except:
			return
		self.options.update( settings )
		#self.options['stylesheet'] = settings['stylesheet']
		#self.options['tabs_position'] = settings['tabs_position']
		#self.options['show_toolbar'] = settings['show_toolbar']
		#self.options['sort_mode'] = settings['sort_mode']
		#self.options['limit'] = settings['limit']
		#self.options['requests_refresh_interval'] = settings['requests_refresh_interval']

options = configmanager()
