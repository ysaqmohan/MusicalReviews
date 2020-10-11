import json
from pymongo import MongoClient

#connecting to mongdb
client = MongoClient('localhost', 27017)
db = client['MusicalReviewsDB']
musical_reviews = db['MusicalReviews']

#read from json file into a list
file_data = [json.loads(line) for line in open('/projects/MusicalReviews/data/reviews_Musical_Instruments_5.json','r')]

#insert into mongodb
musical_reviews.insert_many(file_data)

#close mongodb collection
client.close()