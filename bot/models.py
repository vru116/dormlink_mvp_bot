from peewee import *

db = SqliteDatabase('data/db.sqlite')

class BaseModel(Model):
    class Meta:
        database = db

class Listing(BaseModel):
    id = AutoField()
    author_id = IntegerField()
    dorm = CharField(default="Общежитие 1")  # фиксируем одну общагу для MVP
    type = CharField()       # 'куплю' или 'продам'
    category = CharField()
    description = TextField()
    contact = CharField()
    status = CharField(default='активно')  # 'активно' или 'продано'
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
