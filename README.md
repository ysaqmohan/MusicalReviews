# MusicalReviews
JSON - Mongo - Pandas - Postgres DWH

Data lake/ODS - MongoDB
Tranformation engine - Pandas
DWH - Postgres

The project works on linux environment. The directory structure is as follows:
/<project directory>/data
/<project directory>/python
  
Edit the <project directory> in your python script for replication of results.
Place the JSON file in data directory. The repository includes the file.

Project uses python3. So install the following packages with pip3:
1. pymongo
2. numpy 
3. pandas
4. pycopg2

The db dump for postgres is also attached. Use it to deploy the DB and tables.
Run json_l_mongo.py in python directory with python3 to load data into mongo
mongo_tl_postgres.py in python directory with python3 for reading from mongo, transforming and loading the data into postgres.
