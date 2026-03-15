from peewee import *

db = SqliteDatabase('data/db.sqlite')

class BaseModel(Model):
    class Meta:
        database = db

class Listing(BaseModel):
    id = AutoField()
    author_id = IntegerField()
    dorm = CharField(default="Общежитие 1")
    type = CharField()
    category = CharField()
    description = TextField()
    contact = CharField()
    status = CharField(default='активно')
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    photo_file_id = CharField(null=True)
    photo_type = CharField(null=True)
