function findMinMax() {
    var max = 0;
    var min = db.MusicalReviews.findOne().reviewerName.length;

    db.MusicalReviews.find().forEach(function(doc) {
        var currentLength = doc.reviewerName.length; 
        if (currentLength > max) {
           max = currentLength;
        }
        if (currentLength < min) {
           min = currentLength;
        }
    });

     print(max);
     print(min);
}

findMinMax();
