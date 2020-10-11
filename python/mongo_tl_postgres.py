import json
from pymongo import MongoClient
import pandas as pd
import psycopg2
import sys
import datetime as dt
import sqlalchemy

#connecting to mongdb
client = MongoClient('localhost', 27017)
db = client['MusicalReviewsDB']
musical_reviews = db['MusicalReviews']

#read from mongodb except _id column of the collection
mr_df = pd.DataFrame(list(musical_reviews.find({}, {'_id':0})))

#Reviewer dimension from mr_df
reviewer_df = mr_df[['reviewerID','reviewerName']].drop_duplicates()

#product dimension from mr_df
product_df = mr_df['asin'].drop_duplicates()

#connecting to Postgres
try:
    engine = sqlalchemy.create_engine('postgres://postgres:Susi@123@localhost:5432/reviews_db')
    with engine.connect() as connection:
        print("Postgres connection established: ", bool(connection))
    
    #PRODUCT DIMENSION
    #Reading data from postgress for product dimension
    products_pg_df = pd.read_sql_query('select * from musical.product_dim', con=engine)
    #Left Join product from json file to product from postgres table and use it to recreate product_df
    product_df = pd.merge(product_df, products_pg_df, how='left', left_on='asin', right_on='ProductID')
    #select only non matching records
    product_df = product_df[product_df['ProductID'].isnull()]['asin']
    #convert series (because it had only one column) to dataframe
    product_df = product_df.to_frame()
    #Add current timestamp as insert timestamp
    product_df['InsertTimestamp'] = [dt.datetime.now(tz=None) for i in product_df.index]
    #Rename asin column as productID
    product_df.rename(columns={'asin': 'ProductID'}, inplace=True)
    #Write product to Postgres
    product_df.to_sql('product_dim', con=engine, if_exists="append", schema= 'musical', index=False)
            
except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)
    sys.exit(1)

finally:
    #closing database connection.
    if(connection):
        connection.close()
        print("PostgreSQL connection is closed")