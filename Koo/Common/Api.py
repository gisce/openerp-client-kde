##############################################################################
#
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
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


class KooApi(object):
    """
    KooApi class provides an interface several Koo components relay on being
    available for their proper use.
    """
    def execute(self, actionId, data={}, type=None, context={}):
        """
        Executes the given actionId (which can be a report, keword, etc.).
        :param actionId:
        :param data:
        :param type:
        :param context:
        :return:
        """
        pass

    def executeReport(self, name, data={}, context={}):
        """
        Executes the server action to open a report.
        :param name:
        :param data:
        :param context:
        :return:
        """
        return True

    def executeAction(self, action, data={}, context={}):
        """
        Executes the given server action (which can ba report, keyword, etc.).
        :param action:
        :param data:
        :param context:
        :return:
        """
        pass

    def executeKeyword(self, keyword, data={}, context={}):
        """
        Executes the given server keyword action.
        :param keyword:
        :param data:
        :param context:
        :return:
        """
        return False

    def createWindow(self, view_ids, model, res_id=False, domain=None,
                     view_type='form', window=None, context=None, mode=None,
                     name=False, autoReload=False, target='current'):
        """
        Opens a new window (a new tab with Koo application) with the given
        model.
        :param view_ids:
        :param model:
        :param res_id:
        :param domain:
        :param view_type:
        :param window:
        :param context:
        :param mode:
        :param name:
        :param autoReload:
        :param target:
        :return:
        """
        pass

    def createWebWindow(self, url, title):
        """
        Opens a new window (a new tab with Koo application) with the given url.
        :param url:
        :param title:
        :return:
        """
        pass

    def windowCreated(self, window, target):
        """
        This callback function is (should be) executed each time a new window
        (tab in Koo) is opened.
        :param window:
        :param target:
        :return:
        """
        pass


# This variable should point to a KooApi instance
instance = None
