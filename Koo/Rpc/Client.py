import erppeek

class Client(object):
    def __new__(cls, session):
        return erppeek.Client(session.url, session.databaseName, session.userName, session.password)
