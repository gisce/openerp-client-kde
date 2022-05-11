##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

from PyQt5.QtCore import *
try:
    from PyQt5.QtNetwork import *
    isQtNetworkAvailable = True
except:
    isQtNetworkAvailable = False

from Koo.Common import Notifier
from Koo.Common import Url
from Koo.Common import Api
from Koo.Common import Debug

from .Cache import *
try:
    from . import tiny_socket
    isNetRpcAvailable = True
except:
    isNetRpcAvailable = False

import xmlrpc.client
import urllib
import base64
import socket
from contextlib import contextmanager

import sys
import os

import traceback
from gettext import gettext as _

try:
    import msgpack
    is_msgpack_available = True
except ImportError:
    is_msgpack_available = False

ConcurrencyCheckField = '__last_update'


@contextmanager
def NoTimeout():
    timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(None)
        yield
    finally:
        socket.setdefaulttimeout(timeout)


class RpcException(Exception):
    def __init__(self, info):
        self.code = None
        self.args = (info,)
        self.info = info
        self.backtrace = None


class RpcProtocolException(RpcException):
    def __init__(self, backtrace):
        self.code = None
        self.args = (backtrace,)
        self.info = backtrace
        self.backtrace = backtrace


class RpcServerException(RpcException):
    def __init__(self, code, backtrace):
        self.code = code
        self.args = (backtrace,)
        self.backtrace = backtrace
        if hasattr(code, 'split'):
            lines = code.split('\n')

            self.type = lines[0].split(' -- ')[0]
            self.info = ''
            if len(lines[0].split(' -- ')) > 1:
                self.info = lines[0].split(' -- ')[1]

            self.data = '\n'.join(lines[2:])
        else:
            self.type = 'error'
            self.info = backtrace
            self.data = backtrace


# @brief The Connection class provides an abstract interface for a RPC
# protocol
class Connection:
    def __init__(self, url):
        self.authorized = False
        self.databaseName = None
        self.uid = None
        self.password = None
        self.url = url

    def stringToUnicode(self, result):
        if isinstance(result, bytes):
            return result.decode('utf-8')
        elif isinstance(result, list):
            return [self.stringToUnicode(x) for x in result]
        elif isinstance(result, tuple):
            return tuple([self.stringToUnicode(x) for x in result])
        elif isinstance(result, dict):
            newres = {}
            for i in result.keys():
                newres[self.stringToUnicode(i)] = self.stringToUnicode(result[i])
            return newres
        else:
            return result

    def unicodeToString(self, result):
        if isinstance(result, str):
            return result.encode('utf-8')
        elif isinstance(result, list):
            return [self.unicodeToString(x) for x in result]
        elif isinstance(result, tuple):
            return tuple([self.unicodeToString(x) for x in result])
        elif isinstance(result, dict):
            newres = {}
            for i in list(result.keys()):
                newres[i] = self.unicodeToString(result[i])
            return newres
        else:
            return result

    def connect(self, database, uid, password):
        self.databaseName = database
        self.uid = uid
        self.password = password

    def call(self, url, method, *args):
        pass


try:
    import Pyro.core
    isPyroAvailable = True
except:
    isPyroAvailable = False

isPyroSslAvailable = False
if isPyroAvailable:
    version = Pyro.core.Pyro.constants.VERSION.split('.')
    if int(version[0]) <= 3 and int(version[1]) <= 10:
        Debug.info('To use SSL, Pyro must be version 3.10 or higher; Pyro version %s was found.' %
                   Pyro.core.Pyro.constants.VERSION)
    else:
        try:
            from M2Crypto.SSL import SSLError
            from M2Crypto.SSL.Checker import WrongHost
            isPyroSslAvailable = True
        except:
            Debug.info(
                'M2Crypto not found. Consider installing in order to use Pryo with SSL.')

if not isPyroSslAvailable:
    # Create Dummy Exception so we do not have to complicate code in PyroConnection if
    # SSL is not available.
    class DummyException(Exception):
        pass
    WrongHost = DummyException
    SSLError = DummyException


# @brief The PyroConnection class implements Connection for the Pyro RPC protocol.
#
# The Pyro protocol is usually opened at port 8071 on the server.
class PyroConnection(Connection):
    def __init__(self, url):
        Connection.__init__(self, url)
        self.url += '/rpc'

        from Koo.Common.Settings import Settings
        Pyro.config.PYRO_TRACELEVEL = int(Settings.value('pyro.tracelevel'))
        Pyro.config.PYRO_LOGFILE = Settings.value('pyro.logfile')
        Pyro.config.PYRO_DNS_URI = int(Settings.value('pyro.dns_uri'))

        if self.url.startswith('PYROLOCSSL'):
            Pyro.config.PYROSSL_CERTDIR = Settings.value('pyrossl.certdir')
            Pyro.config.PYROSSL_CERT = Settings.value('pyrossl.cert')
            Pyro.config.PYROSSL_KEY = Settings.value('pyrossl.key')
            Pyro.config.PYROSSL_CA_CERT = Settings.value('pyrossl.ca_cert')
            Pyro.config.PYROSSL_POSTCONNCHECK = int(
                Settings.value('pyrossl.postconncheck'))

        try:
            self.proxy = Pyro.core.getProxyForURI(self.url)
        except SSLError as e:
            title = _('SSL Error')
            if e.message == 'No such file or directory':
                msg = _('Please check your SSL certificate: ')
                msg += e.message
                msg += '\n%s' % os.path.join(Pyro.config.PYROSSL_CERTDIR,
                                             Pyro.config.PYROSSL_CERT)
                details = traceback.format_exc()
                Notifier.notifyError(title, msg, details)
            else:
                raise

        except Exception as e:
            raise

    def singleCall(self, obj, method, *args):
        encodedArgs = self.unicodeToString(args)
        if self.authorized:
            result = self.proxy.dispatch(
                obj[1:], method, self.databaseName, self.uid, self.password, *encodedArgs)
        else:
            result = self.proxy.dispatch(obj[1:], method, *encodedArgs)
        return self.stringToUnicode(result)

    def call(self, obj, method, *args):
        try:
            try:
                #import traceback
                # traceback.print_stack()
                #print >> sys.stderr, "CALLING: ", obj, method, args
                result = self.singleCall(obj, method, *args)
            except (Pyro.errors.ConnectionClosedError, Pyro.errors.ProtocolError) as x:
                # As Pyro is a statefull protocol, network errors
                # or server reestarts will cause errors even if the server
                # is running and available again. So if remote call failed
                # due to network error or server restart, try to bind
                # and make the call again.
                self.proxy = Pyro.core.getProxyForURI(self.url)
                result = self.singleCall(obj, method, *args)
        except (Pyro.errors.ConnectionClosedError, Pyro.errors.ProtocolError) as err:
            raise RpcProtocolException(str(err))
        except Pyro.core.PyroError as err:
            faultCode = err.args and err.args[0] or ''
            faultString = '\n'.join(err.remote_stacktrace)
            raise RpcServerException(faultCode, faultString)
        except WrongHost as err:
            faultCode = err.args and err.args[0] or ''
            faultString = 'The hostname of the server and the SSL certificate do not match.\n  The hostname is %s and the SSL certifcate says %s\n Set postconncheck to 0 in koorc to override this check.' % (
                err.expectedHost, err.actualHost)
            raise RpcServerException(faultCode, faultString)
        except Exception as err:
            faultCode = err.message
            if Pyro.util.getPyroTraceback(err):
                faultString = ''
                for x in Pyro.util.getPyroTraceback(err):
                    faultString += str(x, 'utf-8', errors='ignore')

            else:
                faultString = err.message
            raise RpcServerException(faultCode, faultString)
        return result

# @brief The SocketConnection class implements Connection for the OpenERP socket RPC protocol.
#
# The socket RPC protocol is usually opened at port 8070 on the server.


class SocketConnection(Connection):
    def call(self, obj, method, *args):
        try:
            s = tiny_socket.mysocket()
            s.connect(self.url)
        except socket.error as err:
            raise RpcProtocolException(str(err))
        try:
            # Remove leading slash (ie. '/object' -> 'object')
            obj = obj[1:]
            encodedArgs = self.unicodeToString(args)
            if self.authorized:
                s.mysend((obj, method, self.databaseName,
                          self.uid, self.password) + encodedArgs)
            else:
                s.mysend((obj, method) + encodedArgs)
            result = s.myreceive()
        except socket.error as err:
            raise RpcProtocolException(str(err))
        except tiny_socket.Myexception as err:
            faultCode = err.faultCode
            faultString = err.faultString
            raise RpcServerException(faultCode, faultString)
        finally:
            s.disconnect()
        return self.stringToUnicode(result)

# @brief The XmlRpcConnection class implements Connection class for XML-RPC.
#
# The XML-RPC communication protocol is usually opened at port 8069 on the server.


class XmlRpcConnection(Connection):
    def __init__(self, url):
        Connection.__init__(self, url)
        self.url += '/xmlrpc'

    def call(self, obj, method, *args):
        remote = xmlrpc.client.ServerProxy(self.url + obj, allow_none=True)
        function = getattr(remote, method)
        try:
            with NoTimeout():
                if self.authorized:
                    result = function(self.databaseName, self.uid,
                                      self.password, *args)

                else:
                    result = function(*args)
        except socket.error as err:
            raise RpcProtocolException(err)
        except xmlrpc.client.Fault as err:
            raise RpcServerException(err.faultCode, err.faultString)
        return result


class MsgpackConnection(Connection):
    def __init__(self, url):
        super(MsgpackConnection, self).__init__(url)

    def call(self, obj, method, *args):
        endpoint = '%s%s' % (self.url, obj)
        try:
            with NoTimeout():
                if self.authorized:
                    m = msgpack.packb(
                        [method, self.databaseName, self.uid, self.password]
                        + list(args)
                    )
                else:
                    m = msgpack.packb([method] + list(args))
                u = urllib.request.urlopen(endpoint, m)
                s = u.read()
                u.close()
                result = msgpack.unpackb(s, raw=False)
                if u.code == 210:
                    raise RpcServerException(
                        result['exception'],
                        result['traceback']
                    )
        except socket.error as err:
            raise RpcProtocolException(err)
        return result

# @brief Creates an instance of the appropiate Connection class.
#
# These can be:
# - SocketConnection if protocol (or scheme) is socket://
# - PyroConnection if protocol
# - XmlRpcConnection otherwise (usually will be http or https)
def createConnection(url):
    qUrl = QUrl(url)
    if qUrl.scheme() == 'socket':
        con = SocketConnection(url)
    elif qUrl.scheme() == 'PYROLOC' or qUrl.scheme() == 'PYROLOCSSL':
        con = PyroConnection(url)
    elif qUrl.scheme().endswith('+msgpack'):
        url = '{}://{}:{}'.format(
            qUrl.scheme().split('+')[0], qUrl.host(), qUrl.port()
        )
        con = MsgpackConnection(url)
    else:
        con = XmlRpcConnection(url)
    return con


class AsynchronousSessionCall(QThread):
    exception = pyqtSignal('PyQt_PyObject')
    called = pyqtSignal('PyQt_PyObject')

    def __init__(self, session, parent=None):
        QThread.__init__(self, parent)
        self.session = session.copy()
        self.obj = None
        self.method = None
        self.args = None
        self.result = None
        self.callback = None
        self.error = None
        self.warning = None
        self.exception = None
        # If false, the behaviour is the same as Session.call()
        # otherwise we use the notification mechanism and behave
        # like Session.execute()
        self.useNotifications = False

    def execute(self, callback, obj, method, *args):
        self.useNotifications = True
        self.exception = None
        self.callback = callback
        self.obj = obj
        self.method = method
        self.args = args
        self.finished.connect(self.hasFinished)
        self.start()

    def call(self, callback, obj, method, *args):
        self.useNotifications = False
        self.exception = None
        self.callback = callback
        self.obj = obj
        self.method = method
        self.args = args
        self.finished.connect(self.hasFinished)
        self.start()

    def hasFinished(self):
        if self.exception:
            if self.useNotifications:
                # Note that if there's an error or warning
                # callback is called anyway with value None
                if self.error:
                    Notifier.notifyError(*self.error)
                elif self.warning:
                    Notifier.notifyWarning(*self.warning)
                else:
                    raise self.exception
            self.exception.emit(self.exception)
        else:
            self.called.emit(self.result)

        if self.callback:
            self.callback(self.result, self.exception)

        # Free session and thus server  as soon as possible
        self.session = None

    def run(self):
        # As we don't want to force initialization of gettext if 'call' is used
        # we handle exceptions depending on 'useNotifications'
        if not self.useNotifications:
            try:
                self.result = self.session.call(
                    self.obj, self.method, *self.args)
            except Exception as err:
                self.exception = err
        else:
            try:
                self.result = self.session.call(
                    self.obj, self.method, *self.args)
            except RpcProtocolException as err:
                self.exception = err
                self.error = (_('Connection Refused'), err.info, err.info)
            except RpcServerException as err:
                self.exception = err
                if err.type in ('warning', 'UserError'):
                    self.warning = (err.info, err.data)
                else:
                    self.error = (_('Application Error'), _(
                        'View details'), err.backtrace)


# @brief The Session class provides a simple way of login and executing function in a server
#
# Typical usage of Session:
#
# \code
# from Koo import Rpc
# Rpc.session.login('http://admin:admin\@localhost:8069', 'database')
# attached = Rpc.session.execute('/object', 'execute', 'ir.attachment', 'read', [1,2,3])
# Rpc.session.logout()
# \endcode
class Session:
    LoggedIn = 1
    Exception = 2
    InvalidCredentials = 3

    def __init__(self):
        self.open = False
        self.url = None
        self.password = None
        self.uid = None
        self.context = {}
        self.userName = None
        self.databaseName = None
        self.connection = None
        self.cache = None
        self.threads = []


    def appendThread(self, thread):
        """
        This function removes all finished threads from the list of running
        threads and appends the one provided.
        We keep a reference to all threads started because otherwise their
        C++ counterparts would be freed by garbage collector. User can also
        keep a reference to it when she calls callAsync or executeAsync but
        with this mechanism she's not forced to it.
        The only inconvenience we could find is that we kept some thread
        objects for much too long in memory, but that doesn't seem worrisome
        by now.

        :param thread:
        :return: None
        :rtype: None
        """
        self.threads = [x for x in self.threads if x.isRunning()]
        self.threads.append(thread)


    def callAsync(self, callback, obj, method, *args):
        """
        Calls asynchronously the specified method on the given object on the
        server.

        When the response to the request arrives the callback function is
        called with the returned value as the first parameter. It returns an
        AsynchronousSessionCall instance that can be used to keep track to what
        query a callback refers to, consider that as a call id.
        If there is an error during the call it simply rises an exception. See
        execute() if you want exceptions to be handled by the notification
        mechanism.

        Example of usage:
            from Koo import Rpc
            def returned(self, value):
                print value
            Rpc.session.login('http://admin:admin\@localhost:8069', 'database')
            Rpc.session.post( returned, '/object', 'execute', 'ir.attachment', 'read', [1,2,3])
            Rpc.session.logout()

        :param callback: Function that has to be called when the result returns
        from the server.
        :param obj: Object name (string) that contains the method
        :type obj: str
        :param method: Method name (string) to call
        :type method: str
        :param exceptionCallback: Function that has to be called when an
        exception returns from the server.
        :param args: Argument list for the given method
        :return:
        """
        caller = AsynchronousSessionCall(self)
        caller.call(callback, obj, method, *args)
        self.appendThread(caller)
        return caller

    def executeAsync(self, callback, obj, method, *args):
        """
        Same as callAsync() but uses the notify mechanism to notify exceptions.

        Note that you'll need to bind gettext as texts sent to
        the notify module are localized.
        :param callback:
        :param obj:
        :param method:
        :param args:
        :return:
        """
        caller = AsynchronousSessionCall(self)
        caller.execute(callback, obj, method, *args)
        self.appendThread(caller)
        return caller


    def call(self, obj, method, *args):
        """
        Calls the specified method on the given object on the server.

        If there is an error during the call it simply rises an exception. See
        execute() if you want exceptions to be handled by the notification
        mechanism.

        :param obj: Object name (string) that contains the method
        :type obj: str
        :param method: Method name to call
        :type method: str
        :param args: Argument list for the given method
        :return:
        """
        if not self.open:
            raise RpcException(_('Not logged in'))
        if self.cache:
            if self.cache.exists(obj, method, *args):
                return self.cache.get(obj, method, *args)
        value = self.connection.call(obj, method, *args)
        if self.cache:
            self.cache.add(value, obj, method, *args)
        return value

    def execute(self, obj, method, *args):
        """
        Same as call() but uses the notify mechanism to notify exceptions.

        Note that you'll need to bind gettext as texts sent to the notify
        module are localized.

        :param obj:
        :param method:
        :param args:
        :return:
        """
        count = 1
        while True:
            try:
                return self.call(obj, method, *args)
            except RpcProtocolException as err:
                if not Notifier.notifyLostConnection(count):
                    raise
            except RpcServerException as err:
                if err.type in ('warning', 'UserError'):
                    if err.info in ('ConcurrencyException') and len(args) > 4:
                        if Notifier.notifyConcurrencyError(args[0], args[2] and args[2][0], args[4]):
                            if ConcurrencyCheckField in args[4]:
                                del args[4][ConcurrencyCheckField]
                            return self.execute(obj, method, *args)
                    else:
                        Notifier.notifyWarning(err.info, err.data)
                else:
                    # Si venim a aquest punt l'error no es controlar i per tant
                    # s'ha de fer raise i tractar on toqui del Qgis.
                    raise
                return
            count += 1

    def login(self, url, db):
        """
        Logs in the given server with specified name and password.

        :param url: Admited protocols are 'http', 'https' and 'socket'
        url string such as 'http://admin:admin\@localhost:8069'.
        :type url: str
        :param db: string with the database name
        :type db: str
        :return:
        :raises: Session.Exception, Session.InvalidCredentials or Session.LoggedIn
        """
        url = QUrl(url)
        _url = str(url.scheme()) + '://' + \
            str(url.host()) + ':' + str(url.port())
        self.connection = createConnection(_url)
        user = Url.decodeFromUrl(str(url.userName()))
        password = Url.decodeFromUrl(str(url.password()))
        try:
            res = self.connection.call('/common', 'login', db, user, password)
        except socket.error as e:
            return Session.Exception
        if not res:
            self.open = False
            self.uid = False
            return Session.InvalidCredentials

        self.url = _url
        self.open = True
        self.uid = res
        self.userName = user
        self.password = password
        self.databaseName = db
        if self.cache:
            self.cache.clear()

        self.connection.databaseName = self.databaseName
        self.connection.password = self.password
        self.connection.uid = self.uid
        self.connection.authorized = True

        self.reloadContext()
        return Session.LoggedIn


    def reloadContext(self):
        """
        Reloads the session context

        Useful when some user parameters such as language are changed.
        :return:
        """
        self.context = self.execute(
            '/object', 'execute', 'res.users', 'context_get') or {}

    def logged(self):
        """
        Returns whether the login function has been called and was successfull
        :return:
        """
        return self.open

    def logout(self):
        """
        Logs out of the server.
        :return: None
        :rtype: None
        """
        if self.open:
            self.open = False
            self.userName = None
            self.uid = None
            self.password = None
            self.connection = None
            if self.cache:
                self.cache.clear()

    def evaluateExpression(self, expression, context=None):
        """
        Uses eval to evaluate the expression, using the defined context plus
        the appropiate 'uid' in it.

        :param expression:
        :param context:
        :return:
        """
        if context is None:
            context = {}
        context['uid'] = self.uid
        if isinstance(expression, str):
            if "'active_id'" in expression:
                expression = expression.replace("'active_id'", "active_id")
            return eval(expression, context)
        else:
            return expression

    def copy(self):
        new = Session()
        new.open = self.open
        new.url = self.url
        new.password = self.password
        new.uid = self.uid
        new.context = self.context
        new.userName = self.userName
        new.databaseName = self.databaseName
        # Create a new connection as Pyro protocol does not allow the use of
        # the same connection in different threads and this copy() function
        # will mostly be called to use the session in new threads.
        new.connection = createConnection(new.url)
        new.connection.databaseName = self.databaseName
        new.connection.password = self.password
        new.connection.uid = self.uid
        new.connection.authorized = True
        return new


session = Session()
session.cache = ActionViewCache()


class Database:
    """
    The Database class handles queries that don't require a previous login,
    served by the db server object
    """

    def list(self, url):
        """
        Obtains the list of available databases from the given URL. None if
        there was an error trying to fetch the list.
        :param url:
        :return:
        """
        try:
            call = self.call(url, 'list')
        except RpcServerException as e:
            if e.type == 'AccessDenied':
                # The server has been configured to not return
                # the list of available databases.
                call = False
            else:
                call = -1
        except Exception as e:
            call = -1
        finally:
            return call

    def call(self, url, method, *args):
        """
        Calls the specified method on the given object on the server. If there
        is an error during the call it simply rises an exception
        :param url:
        :param method:
        :param args:
        :return:
        """
        con = createConnection(url)
        return con.call('/db', method, *args)

    def execute(self, url, method, *args):
        """
        Same as call() but uses the notify mechanism to notify exceptions.
        :param url:
        :param method:
        :param args:
        :return:
        """
        res = False
        try:
            res = self.call(url, method, *args)
        except socket.error as msg:
            Notifier.notifyWarning('', _('Could not contact server!'))
        return res


database = Database()




class RpcProxy(object):
    """
    The RpcProxy class allows wrapping a server object only by giving it's
    name.

    For example:
    obj = RpcProxy('ir.values')
    """
    def __init__(self, resource, useExecute=True):
        self.resource = resource
        self.__attrs = {}
        self.__useExecute = useExecute

    def __getattr__(self, name):
        if not name in self.__attrs:
            self.__attrs[name] = RpcFunction(
                self.resource, name, self.__useExecute)
        return self.__attrs[name]


class RpcFunction(object):
    def __init__(self, object, func_name, useExecute=True):
        self.object = object
        self.func = func_name
        self.useExecute = useExecute

    def __call__(self, *args):
        if self.useExecute:
            return session.execute('/object', 'execute', self.object, self.func, *args)
        else:
            return session.call('/object', 'execute', self.object, self.func, *args)


if isQtNetworkAvailable:

    class RpcReply(QNetworkReply):
        """
        RpcReply class extends QNetworkReply and adds a new
        'openerp://' protocol to access content through the current Rpc.session
        connection.

        URL should be of the form openerp://res.model/function/path_sent_to_the_function
        """
        def __init__(self, parent, url, operation):
            QNetworkReply.__init__(self, parent)

            path = str(url.path())
            path = path.split('/')
            if str(url.host()) == 'client':
                function = path[-1]
                parameters = [[str(x[0]), str(x[1])]
                              for x in url.queryItems()]
                parameters = dict(parameters)
                if 'res_id' in parameters:
                    try:
                        parameters['res_id'] = int(parameters['res_id'])
                    except ValueError:
                        parameters['res_id'] = False

                if function == 'action':
                    Api.instance.executeAction(
                        parameters, data={}, context=session.context)

                return
            elif len(path) >= 3:
                model = str(url.host())
                function = path[1]
                parameter = '/%s' % '/'.join(path[2:])

                try:
                    self.content = session.call(
                        '/object', 'execute', model, function, parameter, session.context)
                except:
                    self.content = ''
                if self.content:
                    self.content = base64.decodestring(self.content)
                else:
                    self.content = ''
            else:
                self.content = ''

            self.offset = 0

            self.setHeader(QNetworkRequest.ContentTypeHeader,
                           QVariant("text/html; charset=utf-8"))
            self.setHeader(QNetworkRequest.ContentLengthHeader,
                           QVariant(len(self.content)))
            QTimer.singleShot(0, self, SIGNAL("readyRead()"))
            QTimer.singleShot(0, self, SIGNAL("finished()"))
            self.open(self.ReadOnly | self.Unbuffered)
            self.setUrl(url)

        def abort(self):
            pass

        def bytesAvailable(self):
            return len(self.content) - self.offset

        def isSequential(self):
            return True

        def readData(self, maxSize):
            if self.offset < len(self.content):
                end = min(self.offset + maxSize, len(self.content))
                data = self.content[self.offset:end]
                self.offset = end
                return data

    class RpcNetworkAccessManager(QNetworkAccessManager):
        """
        RpcNetworkAccessManager class extends QNetworkAccessManager and adds
        a new 'openerp://' protocol to access content through the current
        Rpc.session connection.
        """
        def __init__(self, oldManager):
            QNetworkAccessManager.__init__(self)
            self.oldManager = oldManager
            self.setCache(oldManager.cache())
            self.setCookieJar(oldManager.cookieJar())
            self.setProxy(oldManager.proxy())
            self.setProxyFactory(oldManager.proxyFactory())

        def createRequest(self, operation, request, data):
            if request.url().scheme() != 'openerp':
                return QNetworkAccessManager.createRequest(self, operation, request, data)

            if operation != self.GetOperation:
                return QNetworkAccessManager.createRequest(self, operation, request, data)

            return RpcReply(self, request.url(), self.GetOperation)

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
