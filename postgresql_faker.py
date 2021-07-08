from faker import Faker

import argparse
import os
import psycopg2
import re
import sys
import time

parser = argparse.ArgumentParser(description='This script creates a simulated office employee data set in a PostgreSQL database.', add_help=False)
parser.add_argument("--help", action="help", help="Show this help message and exit.")
parser.add_argument("-h", "--host", help="Specify a host destination for the PostgreSQL instance. Defaults to localhost.", default="127.0.0.1")
parser.add_argument("-p", "--port", help="Specify a port for the PostgreSQL connection. Defaults to 5432.", default=5432)
parser.add_argument("-U", "--user", help="Specify a database user.")
parser.add_argument("-W", "--password", help="Specify the db user's password.")
parser.add_argument("-d", "--dbname", help="Specify a database name to use in your PostgreSQL instance.")
parser.add_argument("-l", "--locations", help="Specify number of locations for the fake employee data.", default=8)
parser.add_argument("-e", "--employees", help="Specify number of employees per location for the fake employee data.", default=8)
parser.add_argument("-a", "--auto", help="If the specified database name doesn't exist, passing this flag tells script to automatically create it.", action='store_true')
parser.add_argument("-n", "--dontclean", help="By default the script truncates the tables. Passing this flag means the tables will be left alone.", action='store_true')
parser.add_argument("-c", "--continuous", help="Instead of populating the db as fast as possible, this tells the script to stream instead up to the numbers specified.", action='store_true')
args = parser.parse_args()

# from config import SQL instance connection info, and 
# our database information to connect to the db
SQL_HOST = os.environ.get("SQL_HOST", args.host)
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
        mydb = psycopg2.connect(
            host=SQL_HOST,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            database=DB_NAME
        )
    except (Exception, psycopg2.DatabaseError) as e:
        if re.search(f'FATAL\:[\s]+database \"{DB_NAME}\" does not exist\n', str(e)):
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
                    mydb = psycopg2.connect(
                        host=SQL_HOST,
                        user=DB_USER,
                        password=DB_PASS,
                        port=DB_PORT,
                        database="postgres"
                    )
                    mydb.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                    cur = mydb.cursor()
                    cur.execute(f"CREATE DATABASE {DB_NAME}")
                    mydb.commit()
                    cur.close()
                    mydb.close()
                    mydb = None
                except Exception as e:
                    print(e)
                    sys.exit(1)
            else:
                sys.exit(1)


            # Return here, which will exit into our connection loop, see db
            # is still none, and re-try, but now we've created our DB
            return

        attempt_num = attempt_num + 1
        if attempt_num >= backoff_count:
            wait_amount = wait_amount * 2
        print (f"Couldn't connect to the PostgreSQL instance, trying again in {wait_amount} second(s).")
        print (e)
        time.sleep(wait_amount)
        if wait_amount > 60:
            print ("Giving up on connecting to the database")
            sys.exit(2)
    mydb.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

while mydb == None:
    connect_database()

print("Connected to database successfully")

mycursor = mydb.cursor()

# This is what randomly generates our employee-like data
fake = Faker()

# Create our employee table
def create_employee_table():
    employee_config = """
        CREATE TABLE IF NOT EXISTS employee (
        emp_id SERIAL NOT NULL PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        title TEXT,
        office_id INT,
        pwd TEXT,
        ipaddr TEXT,
        ssn TEXT)"""
    try:
        mycursor.execute(employee_config)
    except (Exception, psycopg2.DatabaseError) as e:
        if e.errno != errorcode.ER_TABLE_EXISTS_ERROR:
            print(e)
            print(e.errno)
            sys.exit(2)


# Fill employee table with data
def create_employees():
    if clean_table:
        try:
            mycursor.execute("DROP TABLE IF EXISTS employee")
        except (Exception, psycopg2.DatabaseError) as e:
            print(e)
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
            jobtitle = fake.job().split("/")[0].replace("'", "''")
            pwd = fake.password()
            ipaddr = fake.ipv4()
            ssn = fake.ssn()
            sql_command = (
                "INSERT INTO employee (first_name, last_name, title, office_id, pwd, ipaddr, ssn) "
                f"VALUES ('{first_name}', '{last_name}', '{jobtitle}', {office_id}, '{pwd}', '{ipaddr}', '{ssn}')"
            )
            try:
                mycursor.execute(sql_command)
            except (Exception, psycopg2.DatabaseError) as e:
                print (e)

            if args.continuous:
                time.sleep(0.5)
                print(f". {first_name} {last_name}")

        mydb.commit()

# Create location table
def create_location_table():
    location_config = """
        CREATE TABLE IF NOT EXISTS location (
        office_id SERIAL NOT NULL PRIMARY KEY,
        address TEXT,
        city TEXT,
        state TEXT)"""
    try:
        mycursor.execute(location_config)
    except (Exception, psycopg2.DatabaseError) as e:
        print(e)
        sys.exit(2)


# Fill location table with data
def generate_locations():
    if clean_table:
        try:
            mycursor.execute("DROP TABLE IF EXISTS location")
        except (Exception, psycopg2.DatabaseError) as e:
            print(e)
            sys.exit(2)
            
    create_location_table()

    for _ in range(LOCATIONS):
        address = fake.street_address()
        city = fake.city()
        state = fake.state_abbr()
        sql_command = f"INSERT INTO location (address, city, state) VALUES ('{address}', '{city}', '{state}')"
        try:
            mycursor.execute(sql_command)
        except (Exception, psycopg2.DatabaseError) as e:
            print(e)

    mydb.commit()

# aaaaaand go!
print(f"Beginning data creation of {LOCATIONS} locations")
generate_locations()
print("Finished creating locations and beginning to create employee records")
create_employees()
print("Finished creating employee records")
