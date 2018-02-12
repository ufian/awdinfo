# -*- coding: utf-8 -*-

__author__ = 'ufian'

import mongoengine as me


class User(me.Document):
    meta = {'collection': 'users'}
    
    user_id = me.IntField(required=True)
    status = me.BooleanField(required=True)
    

class Message(me.Document):
    meta = {'collection': 'messages'}
    
    message_id = me.StringField(required=True)
    text = me.StringField(required=True)
    date = me.DateTimeField(required=True)
    
class Status(me.Document):
    meta = {'collection': 'info'}
    
    status = me.StringField(required=True)
