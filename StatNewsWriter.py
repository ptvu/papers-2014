from apsw import Connection, CantOpenError, connection_hooks

def setwal(db):
    '''
    Set WAL (write-ahead logs) for SQLite database.
    Much faster and better concurrency than default logging.
    This function is called by connection_hooks, and is called every time a db connection is created.
    See http://apidoc.apsw.googlecode.com/hg/tips.html
    '''
    if not db.readonly("main"):
        db.cursor().execute("pragma journal_mode=wal")

connection_hooks.append(setwal)

class DatabaseController(object):
    def __init__(self,name):
        '''
        Set up C{apsw} connection and cursor for database given filename.

        @param name: database file name
        @type name: C{string}
        '''
        self.filename = name
        try:
            self.db = Connection(self.filename)
        except CantOpenError:
            print "Can't open database %s"%(self.filename)
            raise

        # rowDict function used to manipulate output into dictionary form.
        self.primaryCursor = self.db.cursor()
        self.primaryCursor.setrowtrace(self.__rowDict)

    def __rowDict(self,cursor,row):
        '''
        Transform rows returned into dicts, {colname:value}

        @param cursor: C{apsw} connection cursor, called automatically from C{rowtrace}
        @type cursor: C{apsw.Connection.cursor}
        @param row: a row from the database
        @type row: C{tuple}
        '''
        desc = cursor.getdescription()
        desc = [val[0] for val in desc]  # extract just the names of table columns
        d = dict(zip(desc,row))  # turn into a dictionary, name:value pairs
        return d

    def getTableNames(self):
        '''
        Return a list of table names in the database

        @return: List of strings of table names in database
        @rtype: C{list[string]}
        '''
        self.primaryCursor.execute("select name from sqlite_master;")
        return [a['name'] for a in self.primaryCursor.fetchall()]  # make a flat array of names

class StatNewsWriterInterface(object):
    def __init__(self,dbc):
        '''
        Pairs with the provided database controller object and structures the database as needed.
        Sets up necessary tables for the application.

        @param dbc: Database controller, underlying interface layer
        @type dbc: C{L{DatabaseController}}
        '''
        self.dbc = dbc
        self.structureDatabase()

    def structureDatabase(self):
        '''
        Set up the database for a StatNews application.

        Table: Data
            - time: (int) UTC timecode of document creation
            - source: (text) text describing origin of document (NY Times, Washington Post, US Patent office)
            - content: (text) text of article
            - title: (text) title of document
            - location: (text) text of location of publication
            - url: (text) text of url of article
            - meta: (int) extra data, possibly link to another table, application specific
        '''

        tables = self.dbc.getTableNames()

        '''  Temporary change: Removing unique constraint from database, likely causing massive slowdowns - we can do this check in memory very easily with     hierarchical search...
        if ('Data' not in tables):
            self.dbc.primaryCursor.execute("create table Data (time int, source text, content text, \
                        title text, location text, url text, meta int, \
                        UNIQUE(time,source,content,title) ON CONFLICT IGNORE);")
            self.dbc.primaryCursor.execute("create index if not exists time_index on Data (time);")
        '''
        if ('Data' not in tables):
            self.dbc.primaryCursor.execute("CREATE TABLE Data(rowid integer primary key autoincrement,time integer,source text,content text,title text,location text,url text,meta blob);")
#            self.dbc.primaryCursor.execute("create index if not exists time_index on Data (time);")

    def writeDataHandler(self,**kwargs):
        '''
        Save data to Data table of database.

        @keyword data: dictionary representing row of table to insert, or list of dicts for many rows.
        @type data: C{list[dict]} or C{dict}
        '''
        if 'data' not in kwargs:
            raise Exception("'data' is a required keyword argument of writeDataHandler.")

        data = kwargs['data']

        if type(data) is dict:
            # single row
            self.dbc.primaryCursor.execute("insert into Data values(:rowid, :time, :source, :content, :title, :location, :url, :meta );",data)
        elif type(data) is list:
            # multiple rows
            self.dbc.primaryCursor.executemany("insert into Data values(:rowid, :time, :source, :content, :title, :location, :url, :meta );",data)
        else:
            raise TypeError("StatNewsDatabaseInterface.writeDataHandler takes a list of dicts or a dict as input.")

