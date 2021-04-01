import MySQLdb
import sqlite3

"""DBObjects contains only 4 objects: Database, Query, Table and Results
The Query class supports replacement of arguments if the string ?0, ?1
and so forth are in the query. So replaces Apple with Oranges is very simple"""

class Database():
    def __init__(self, *args):
        self._db = MySQLdb.connect(args[0], args[1], args[2], args[3])
        self.host=args[0]   # host
        self.userid=args[1] # userid
        self.pwd = args[2]  # password
        self.dbname = args[3] # database name
        self._cursor = self._db.cursor() # save the cursor

    def commit(self):
        self._db.commit()

    def create(self, dbname):
        self._cursor.execute("drop database if exists "+dbname)
        self._cursor.execute("Create database "+ dbname)
        self._dbname = dbname
        self._db=MySQLdb.connect(self.host, self.userid, self.pwd, dbname)
        self._cursor.execute("use "+dbname)
        self._cursor= self._db.cursor()

    def getName(self):
        return self._dbname

    @property
    def cursor(self):
        return self._cursor

    def getTables(self):
        tquery = Query(self.cursor, "show tables")
        res = tquery.execute()
        rows = res.getRows()
        # create array of table objects
        self.tables = []
        for r in rows:
            self.tables.append(Table(self._db, r))
        return self.tables

# base class Column
class Column():
    def __init__(self, name):
        self._name=name
        self._primary = False

    def isPrimary(self):
       return self._primary

    @property
    def name(self):
        return self._name

# holds primary key string as table is created
class Primary() :
    primaryString = ""

# Query object makes queries and returns Results
class Query():
    def __init__(self, cursor, *qstring):
        self.qstring = qstring[0]
        self.multiple=False
        if len(qstring) >1:
            self.vals = qstring[1]
            self.multiple = True
        self.cursor = cursor

        # executes the query and returns all the results
    def execute(self):
        print (self.qstring)
        if not self.multiple:
            self.cursor.execute(self.qstring)
            rows = self.cursor.fetchall()
            return Results(rows)
        else:
            self.cursor.executemany(self.qstring, self.vals)

    def executeMultiple(self, vals):
        print (self.qstring, vals)
        self.cursor.executemany(self.qstring, vals)


# Query object makes queries and returns Results
class VariableQuery():
    def __init__(self, cursor, qstring):
        self.qstringMaster = qstring  #master copy
        self.qstring = self.qstringMaster
        self.cursor = cursor

    # copies master and inserts arguments into it
    def insertArgs(self, *args):
        index = 0
        self.qstring = self.qstringMaster
        # replaces ?0, ?1 etc with the provided args
        # to create a revised query
        for arg in args:
            tempstr = "?" + str(index)
            self.qstring = self.qstring.replace(tempstr, "'" + arg + "'")
            index += 1

    # executes the query and returns all the results
    def execute(self):
        print (self.qstring)
        self.cursor.execute(self.qstring)
        rows = self.cursor.fetchall()
        return Results(rows)

    #executes the query and returns only the first result
    def executeFetchone(self):
        self.cursor.execute(self.qstring)
        rows = self.cursor.fetchone()
        return Results(rows)

    # fetches the next result
    def fetchOne(self):
        rows = self.cursor.fetchone()
        return Results(rows)

    #fetches up to max more results
    def fetchMany(self, max):
        rows = self.cursor.fetchmany(max)
        return Results(rows)

# Integer column- may be a primary key
class Intcol(Column)  :
    def __init__(self, name, primary):
        super().__init__(name)
        self._primary = primary

    def getName(self):
        idname = self.name+" INT NOT NULL "
        if self._primary:
            Primary.primaryString = ("PRIMARY KEY (" + self.name + ")")
        return idname
# Float col
class Floatcol(Column):
    def __init__(self, name):
        super().__init__(name)

    def getName(self):
        idname =  self.name + " FLOAT NOT NULL "
        return idname
# character column - length is  the 2nd argument
class Charcol(Column):
    def __init__(self, name, width:int):
        super().__init__(name)
        self.width=width
    def getName(self):
        idname =  self.name + " VARCHAR("+str(self.width)+") NULL "
        return idname

class Table():
    def __init__(self, db, name):
        self.cursor = db.cursor()
        self.db = db
        self.tname = name   # first of tuple
        self.colList=[]     # list of column names generated
        self._primarystring = ""

    def getColumns(self):
        print(self.tname)
        sql="show columns from "+ "".join(self.tname)
        tquery = Query(self.cursor, sql)
        self.columns = tquery.execute().getRows()
        return self.columns

    @property
    def name(self):     # gets table name
        return self.tname

    # get contents of a column
    def getColumnContents(self, cname):
        query = Query(self.cursor, "select " + cname + " from "
                      + self.tname[0])
        results = query.execute()
        return results.getRows()

    # add a column
    def addColumn(self, column):
        self.colList.append(column)

    # creates the sql to make the columbs
    def addRows(self, varnames):
        qry = "insert into "+self.tname +"("
        i = 0
        for i in range(0, len(self.colList)-1):
            c = self.colList[i]
            qry += c.name + ","
        qry += self.colList[-1].name+") values ("
        for i in range(0, len(self.colList) - 1):
            qry += "%s,"
        qry +="%s)"
        query = Query(self.cursor, qry, varnames)
        query.execute()
        self.db.commit()

# contains the result of a query
class Results():
    def __init__(self, rows):
        self.rows = rows

    def getRows(self):
        return self.rows



# Table class used to create all the table
class SqltTable(Table):
    def __init__(self, db, name):
        self.cursor = db.cursor()
        self.db = db
        self.tname = name   # first of tuple
        self.colList=[]     # list of column names generated
        self._primarystring = ""


    # creates the sql to make the columns--Sqlite differs slightly
    def addRows(self, varnames):
        qry = "insert into "+self.tname +"("
        i = 0
        for i in range(0, len(self.colList)-1):
            c = self.colList[i]
            qry += c.name + ","

        qry += self.colList[-1].name+") values ("
        for i in range(0, len(self.colList) - 1):
            qry += "?,"
        qry +="?);"

        query = Query(self.cursor, qry, varnames)
        print(qry+"\n", varnames)
        query.execute()
        self.db.commit()

    # creates the table and columns
    def create(self):
        sql = "create table " +  self.name + " ("
        for col in self.colList:
            sql += col.getName()+","

        sql += Primary.primaryString
        sql +=");"
        print (sql)
        self.cursor.execute(sql)

    def getColumns(self):
        tn = self.tname[0]
        print(self.tname)
        sql="select name from pragma_table_info('"+tn+"')"
        print(sql)
        self.cursor.execute(sql)
        self.columns = self.cursor.fetchall()
        return self.columns


class SqltDatabase(Database):
    def __init__(self, *args):
        self._db = sqlite3.connect(args[0])
        self._dbname = args[0]
        self._cursor = self._db.cursor()

    def commit(self):
        self._db.commit()

    def create(self, dbname):
        pass
    def getTables(self):
        tbQuery = Query(self.cursor,
                        "select name from sqlite_master where type='table'")

        # create array of table objects
        self.tables=[]
        rows = tbQuery.execute().getRows()
        for r in rows:
            self.tables.append(SqltTable(self._db, r))
        return self.tables
