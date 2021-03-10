# sql_data_randomizer
Couple scripts I wrote to help quickly get some random data into a MySQL or PostgreSQL database. If you're looking for something similar for SQL Server, you can find a good one here: https://github.com/dmahugh/cloudsql-samples/blob/master/faker_sample.py

It connects on 127.0.0.1 by default (can be changed via env var or flag). I rely on running the Cloud SQL proxy at the same location as the script to make things consistent. If you're running a local database, of course it will also work fine on that db.

**NOTE** that by default this drops the tables before re-creating them. Don't run this against a database with existing data unless you're okay with said data going away.

Can run *-h* for full usage/options.

Dockerfile and deployment yaml files also handy to run this in a container if you want to scale it up with Kubernetes.

Blog posts breaking things down:

Script: https://medium.com/@GabeWeiss/creating-sample-data-for-mysql-databases-38e3eff4a91b

Containerization basics: https://medium.com/@GabeWeiss/breaking-down-containers-9b0eb94cc0cd (not quite live yet, soon)

Scaling app with Kubernetes and connecting to Cloud SQL using sidecar pattern: https://medium.com/@GabeWeiss/connecting-cloud-sql-kubernetes-sidecar-46e016e07bb4 (also not quite live yet, soon)
