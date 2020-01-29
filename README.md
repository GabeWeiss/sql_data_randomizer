# sql_data_randomizer
Script I wrote to help quickly get some random data into a SQL database.

It connects on 127.0.0.1 by default (can be changed via env var or flag). I rely on running the Cloud SQL proxy at the same location as the script to make things consistent. If you're running a local database, of course it will also work fine on that db.

**NOTE** that by default this drops the tables before re-creating them. Don't run this against a database with existing data unless you're okay with said data going away.

Can run *-h* for full usage/options.
