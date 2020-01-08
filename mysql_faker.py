from faker import Faker

import os
import sys
import getopt
import time
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode

# from config import SQL instance connection info, and 
# our database information to connect to the db
SQL_HOST = os.environ.get("SQL_HOST", "127.0.0.1") # Defaults to using localhost/Cloud SQL Proxy
DB_USER  = os.environ.get("DB_USER", None)
DB_PASS  = os.environ.get("DB_PASS", None)
DB_NAME  = os.environ.get("DB_NAME", None)

# configurable defaults for how many variations you want
LOCATIONS = 8
EMPLOYEES = 8 # This is number of employees per location, not total

# parsing/handling commandline options
auto_create = False
create_db = False
# Note: By default, each time you run this script, it cleans the tables out
# If you want to add more data instead of starting fresh, you can pass the flag '-c'
# and it won't clean out the database, but will just add more random values to it
clean_table = True
fullCmdArguments = sys.argv
argumentList = fullCmdArguments[1:]
unixOptions = "hH:u:p:d:l:e:ac"
gnuOptions = ["help", "host=", "user=", "passwd=", "dbname=", "locations=", "employees=", "auto", "dontclean"]

# probably don't NEED to do all this try/catch, but makes it easier to catch what/where goes wrong sometimes
# this chunk is just handling arguments
try:
    arguments, values = getopt.getopt(argumentList, unixOptions, gnuOptions)
except getopt.error as err:
    print (str(err))
    sys.exit(2)

for currentArgument, currentValue in arguments:
    if currentArgument in ("-h", "--help"):
        print ("\nusage: python mysql_faker.py [-h | -u user | -p passwd | -d dbname | -l locations | -e employees]\nOptions and arguments (and corresponding environment variables):\n-d db\t: database name to connect to or create if it doesn't exist\n-e emps\t: number of employees per location to create\n-h\t: display this help\n-l locs\t: number of locations to create\n-p pwd\t: password for the database user\n-u usr\t: database user to connect with\n-a\t: automatically create the database if it's missing\n-c\t: DON'T clean out the tables before inserting new random data. Default is to start clean\n\nOther environment variables:\nDB_USER\t: database user to connect with. Overridden by the -u flag\nDB_PASS\t: database password. Overridden by the -p flag.\nDB_NAME\t: database to connect to. Overridden by the -d flag.\n")
        sys.exit(0)

    if currentArgument in ("-H", "--host"):
        SQL_HOST = currentValue
    elif currentArgument in ("-u", "--user"):
        DB_USER = currentValue
    elif currentArgument in ("-p", "--passwd"):
        DB_PASS = currentValue
    elif currentArgument in ("-d", "--dbname"):
        DB_NAME = currentValue
    elif currentArgument in ("-l", "--locations"):
        LOCATIONS = int(currentValue)
    elif currentArgument in ("-e", "--employees"):
        EMPLOYEES = int(currentValue)
    elif currentArgument in ("-a", "--auto"):
        auto_create = True
    elif currentArgument in ("-c", "--dontclean"):
        clean_table = False

# Make sure that we have all the pieces we must have in order to connect to our db properly
if not DB_USER:
    print ("You have to specify a database user either by environment variable or pass one in with the -u flag.")
    sys.exit(2)
if not DB_PASS:
    print ("You have to specify a database password either by environment variable or pass one in with the -p flag.")
    sys.exit(2)
if not DB_NAME:
    print ("You have to specify a database name either by environment variable or pass one in with the -d flag.")
    sys.exit(2)

try:
    mydb = mysql.connector.connect(
        host=SQL_HOST,
        user=DB_USER,
        passwd=DB_PASS
    )
except Error as e:
    print ("Couldn't connect to the MySQL instance.")
    sys.exit(2)

mycursor = mydb.cursor()

# This is what randomly generates our employee-like data
fake = Faker()

# Attempt to switch to our specified database
# If it doesn't exist, then go through a flow to create it
try:
    mycursor.execute("USE {}".format(DB_NAME))
except Error as e:
    if e.errno == errorcode.ER_BAD_DB_ERROR:
        if auto_create == False:
            u_input = input("Your database doesn't exist, would you like to create it (Y/n)? ")
            if u_input == "Y":
                create_db = True
            else:
                print ("The database doesn't exist and you've chosen to not create it.")
                sys.exit(0)
        else:
            create_db = True

        if create_db:
            try:
                mycursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
                mycursor.execute("USE {}".format(DB_NAME))
            except Error as e:
                print ("Wasn't able to create the database.")
                print (e)
                sys.exit(2)
    else:
        print(e)
        sys.exit(2)

# Create our employee table
def create_employees():
    if clean_table:
        try:
            mycursor.execute("DROP TABLE employee")
        except Error as e:
            if e.errno != errorcode.ER_BAD_TABLE_ERROR:
                print("There was a problem dropping the existing employee table.")
                sys.exit(2)

    employee_config = """
        CREATE TABLE employee (
        emp_id INT NOT NULL AUTO_INCREMENT,
        first_name VARCHAR(40),
        last_name VARCHAR(40),
        title VARCHAR(80),
        office_id INT,
        pwd CHAR(15),
        ipaddr CHAR(15),
        ssn CHAR(11),
        PRIMARY KEY (emp_id))"""
    try:
        mycursor.execute(employee_config)
    except Error as e:
        print(e)
        sys.exit(2)

    for office_id in range(1, LOCATIONS + 1):
        # generate some random employees for each office location
        for _ in range(EMPLOYEES):
            first_name = fake.first_name()
            last_name = fake.last_name()
            # Job titles have a lot of whacky things that come through, so be sure we're cleaning
            # our input a bit. If there's a slash, get rid of it, and if it has an apostrophe, we
            # need to escape it so it doesn't munge our SQL
            jobtitle = fake.job().split("/")[0].replace("'", "\\'")
            pwd = fake.password()
            ipaddr = fake.ipv4()
            ssn = fake.ssn()
            sql_command = (
                "INSERT INTO employee (first_name, last_name, title, office_id, pwd, ipaddr, ssn) "
                "VALUES ('{}', '{}', '{}', {}, '{}', '{}', '{}')".format(first_name, last_name, jobtitle, office_id, pwd, ipaddr, ssn)
            )
            try:
                mycursor.execute(sql_command)
            except Error as e:
                print (e)

        mydb.commit()

# Create location table
def generate_locations():
    if clean_table:
        try:
            mycursor.execute("DROP TABLE location")
        except Error as e:
            if e.errno != errorcode.ER_BAD_TABLE_ERROR:
                print("There was a problem dropping the existing location table.")
                sys.exit(2)

    location_config = """
        CREATE TABLE location (
        office_id INT NOT NULL AUTO_INCREMENT,
        address VARCHAR(80),
        city VARCHAR(40),
        state CHAR(2),
        PRIMARY KEY (office_id))"""
    mycursor.execute(location_config)

    for _ in range(LOCATIONS):
        address = fake.street_address()
        city = fake.city()
        state = fake.state_abbr()
        sql_command = "INSERT INTO location (address, city, state) VALUES ('{}', '{}', '{}')".format(address, city, state)
        try:
            mycursor.execute(sql_command)
        except Error as e:
            print(e)

    mydb.commit()

# aaaaaand go!
generate_locations()
create_employees()
