# sql_data_randomizer
Holds some scripts I've written to help quickly get some random data into a SQL database.

It connects on 127.0.0.1. I rely on running the Cloud SQL proxy at the same location as the script to make things consistent. If you're running a local database, of course it will also work fine on that db. **NOTE** that by default this drops the tables before re-creating them. Don't run this against a database with existing data unless you're okay with said data going away.

Can run *-h* for full usage/options.
