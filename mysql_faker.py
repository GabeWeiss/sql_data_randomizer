from faker import Faker

import argparse
import os
import sys
import time
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode

parser = argparse.ArgumentParser(description='This script creates a simulated office employee data set in a MySQL database.', add_help=False)
parser.add_argument("--help", action="help", help="Show this help message and exit.")
parser.add_argument("-h", "--host", help="Specify a host destination for the PostgreSQL instance. Defaults to localhost.", default="127.0.0.1")
parser.add_argument("-P", "--port", help="Specify a port for the PostgreSQL connection. Defaults to 3306.", default=3306)
parser.add_argument("-u", "--user", help="Specify a database user.")
parser.add_argument("-p", "--password", help="Specify the db user's password.")
parser.add_argument("-D", "--dbname", help="Specify a database name to use in your PostgreSQL instance.")
parser.add_argument("-l", "--locations", help="Specify number of locations for the fake employee data.", default=8)
parser.add_argument("-e", "--employees", help="Specify number of employees per location for the fake employee data.", default=8)
parser.add_argument("-a", "--auto", help="If the specified database name doesn't exist, passing this flag tells script to automatically create it.", action='store_true')
parser.add_argument("-n", "--dontclean", help="By default the script truncates the tables. Passing this flag means the tables will be left alone.", action='store_true')
parser.add_argument("-c", "--continuous", help="Instead of populating the db as fast as possible, this tells the script to stream instead up to the numbers specified.", action='store_true')
args = parser.parse_args()

# from config import SQL instance connection info, and 
# our database information to connect to the db
SQL_HOST = os.environ.get("SQL_HOST", args.host) # Defaults to using localhost/Cloud SQL Proxy
DB_PORT  = os.environ.get("DB_PORT", args.port)
DB_USER  = os.environ.get("DB_USER", args.user)
DB_PASS  = os.environ.get("DB_PASS", args.password)
DB_NAME  = os.environ.get("DB_NAME", args.dbname)

# configurable defaults for how many variations you want
LOCATIONS = 0
try:
    LOCATIONS = int(args.locations)
except:
    print("Locations count must be an integer.")
    sys.exit(1)
# This is number of employees per location, not total
EMPLOYEES = 0
try:
    EMPLOYEES = int(args.employees)
except:
    print("Employee count must be an integer.")
    sys.exit(1)

# parsing/handling commandline options
auto_create = False
if args.auto:
    auto_create = True
create_db = False

# Note: By default, each time you run this script, it cleans the tables out
# If you want to add more data instead of starting fresh, you can pass the flag '-c'
# and it won't clean out the database, but will just add more random values to it
clean_table = True
if args.dontclean:
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
if not DB_PORT:
    print ("You have to specify a database port either by environment variable or pass one in with the -P flag.")
    sys.exit(2)


# Wait for our database connection
mydb = None
attempt_num = 0
wait_amount = 1
# backoff_count is the static count for how many times we should try at one
# second increments before expanding the backoff time exponentially
# Once the wait time passes a minute, we'll give up and exit with an error
backoff_count = 5
def connect_database():
    global attempt_num
    global wait_amount
    global mydb
    try:
        mydb = mysql.connector.connect(
            host=SQL_HOST,
            user=DB_USER,
            passwd=DB_PASS,
            port=DB_PORT
        )
    except Error as e:
        attempt_num = attempt_num + 1
        if attempt_num >= backoff_count:
            wait_amount = wait_amount * 2
        print ("Couldn't connect to the MySQL instance, trying again in {} second(s).".format(wait_amount))
        print (e)
        time.sleep(wait_amount)
        if wait_amount > 60:
            print ("Giving up on connecting to the database")
            sys.exit(2)

while mydb == None:
    connect_database()

print("Connected to database successfully")

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
            sys.exit(2)

    else:
        print(e)
        sys.exit(2)

# Create our employee table
def create_employee_table():
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
        if e.errno != errorcode.ER_TABLE_EXISTS_ERROR:
            print(e)
            print(e.errno)
            sys.exit(2)


# Fill employee table with data
def create_employees():
    if clean_table:
        try:
            mycursor.execute("DROP TABLE employee")
        except Error as e:
            if e.errno != errorcode.ER_BAD_TABLE_ERROR:
                print("There was a problem dropping the existing employee table.")
                sys.exit(2)

    create_employee_table()

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

            if args.continuous:
                time.sleep(0.5)
                print(f". {first_name} {last_name}")

        mydb.commit()

# Create location table
def create_location_table():
    location_config = """
        CREATE TABLE location (
        office_id INT NOT NULL AUTO_INCREMENT,
        address VARCHAR(80),
        city VARCHAR(40),
        state CHAR(2),
        PRIMARY KEY (office_id))"""
    try:
        mycursor.execute(location_config)
    except Error as e:
        if e.errno != errorcode.ER_TABLE_EXISTS_ERROR:
            print(e)
            print(e.errno)
            sys.exit(2)


# Fill location table with data
def generate_locations():
    if clean_table:
        try:
            mycursor.execute("DROP TABLE location")
        except Error as e:
            if e.errno != errorcode.ER_BAD_TABLE_ERROR:
                print("There was a problem dropping the existing location table.")
                sys.exit(2)

    create_location_table()

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
print("Beginning data creation of {} locations".format(LOCATIONS))
generate_locations()
print("Finished creating locations and beginning to create employee records")
create_employees()
print("Finished creating employee records")
