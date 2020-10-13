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
reviewer_df = reviewer_df[reviewer_df['reviewerName'].notnull()] #remove any record with null columns for reviewerName

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
    #Drop any rows with product_id as null
    product_df = product_df[product_df['ProductID'].notnull()]
    #Write product to Postgres
    product_df.to_sql('product_dim', con=engine, if_exists="append", schema= 'musical', index=False)

    #REVIEWER DIMENSION
    #Reading data from postgress for REVIEWER dimension
    sql_read_reviewer = """SELECT * FROM musical.reviewer_dim WHERE "ActiveIndicator" = 'Y'"""
    reviewer_pg_df = pd.read_sql_query(sql=sql_read_reviewer, con=engine)
    #Left Join reviewer from json file to reviewer from postgres table and use it to recreate reviewer_df
    reviewer_df = pd.merge(reviewer_df, reviewer_pg_df, how='left', on='reviewerID')
    #Select changed records only from reviewer_df
    reviewer_chg_df = reviewer_df[(reviewer_df['reviewerName_x'] != reviewer_df['reviewerName_y']) & reviewer_df['reviewerName_y'].notnull()][['reviewerID','reviewerName_x']]
    #Add the metadata for changed dataframe
    reviewer_chg_df['InsertTimestamp'] = [dt.datetime.now(tz=None) for i in reviewer_chg_df.index]
    reviewer_chg_df['UpdateTimestamp'] = [dt.datetime.now(tz=None) for i in reviewer_chg_df.index]
    reviewer_chg_df['ActiveIndicator'] = ['Y' for i in reviewer_chg_df.index]
    #Select new records from reviewer_df
    reviewer_new_df = reviewer_df[reviewer_df['reviewerName_y'].isnull()][['reviewerID','reviewerName_x']]
    #Add the metadata for new dataframe
    reviewer_new_df['InsertTimestamp'] = [dt.datetime.now(tz=None) for i in reviewer_new_df.index]
    reviewer_new_df['UpdateTimestamp'] = [dt.datetime.now(tz=None) for i in reviewer_new_df.index]
    reviewer_new_df['ActiveIndicator'] = ['Y' for i in reviewer_new_df.index]
    #Union of changed and new dataframes
    reviewer_df = pd.concat([reviewer_chg_df,reviewer_new_df])
    #Rename reviewerName_x to reviewerName
    reviewer_df.rename(columns={'reviewerName_x' : 'reviewerName'} ,inplace=True)
    #Drop any row with reviewerId as null and drop any duplicates
    reviewer_df = reviewer_df[reviewer_df['reviewerID'].notnull()]
    #Write dataframe with changed and new records to a worktable in postgres
    reviewer_df.to_sql('reviewer_wt', con=engine, if_exists="replace", schema= 'work_schema', index=False)

    sql_update = """UPDATE musical.reviewer_dim
                    SET "ActiveIndicator" = 'N'
                    , "UpdateTimestamp" = LOCALTIMESTAMP
                    FROM work_schema.reviewer_wt as wt
                    WHERE reviewer_dim."reviewerID"=wt."reviewerID"
                    AND reviewer_dim."ActiveIndicator"='Y'
                    """

    sql_insert = """INSERT INTO musical.reviewer_dim 
                    SELECT "reviewerID", "reviewerName", LOCALTIMESTAMP, LOCALTIMESTAMP, "ActiveIndicator" FROM work_schema.reviewer_wt"""
    
    #Applying update and insert queries to main table from WT
    with engine.begin() as conn:
        conn.execute(sql_update)
        print("Reviewer dimension update complete.")
        conn.execute(sql_insert)
        print("Reviewer dimension insert complete.")

    #FACT TABLE LOAD
                        
except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)
    sys.exit(1)

finally:
    #closing database connection.
    if(connection):
        connection.close()
        print("PostgreSQL connection is closed")
