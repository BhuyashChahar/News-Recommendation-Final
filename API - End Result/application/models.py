import flask
from application import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Document):
    user_id     =   db.IntField( unique=True )
    first_name  =   db.StringField( max_length=50 )
    last_name   =   db.StringField( max_length=50 )
    email       =   db.StringField( max_length=30 )
    password    =   db.StringField( )
    ip          =   db.StringField( )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def get_password(self, password):
        return check_password_hash(self.password, password)

class UserParameters(db.Document):
    user_id     =   db.IntField( unique = True )
    session_id  =   db.IntField( required = True )


class Articles(db.Document):
    articleID   =   db.StringField( )
    Datetime   =   db.DateTimeField( )
    Category    =   db.StringField( )
    Subcategory =   db.StringField( )
    Headline     =   db.StringField( )
    Summary     =   db.StringField( )
    Entire_News =   db.StringField( )
    News_Link   =   db.StringField( )
    Author   =   db.StringField( )

class Rating(db.Document):
    user_id     =   db.IntField( )
    articleID   =   db.StringField( max_length=10 )
    Rating      =   db.IntField( )

class Clickstream(db.Document):
    user_id     =   db.IntField( )
    session_id   =   db.StringField( max_length=10 )
    articleID       =   db.StringField( )
    article_rank      =   db.IntField( )
    article_clicked     =   db.IntField( )
    time_spent          =   db.StringField( )
