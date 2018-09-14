# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

__author__ = 'ufian'

import time
from time import mktime
from datetime import datetime, timedelta

import mongoengine as me
import telepot
import random
from telepot.loop import MessageLoop

import config
from model import User, Message, Status
import feedparser

import bs4

class BotWrapper():
    BOT = None
    
def get_status():
    status = Status.objects.first()
    if status is None:
        status = Status(status="Nope")
        status.save()
        
    return status

def handle_message(msg):
    try:
        content_type, chat_type, chat_id = telepot.glance(msg)
        
        text = msg.get('text')
        if text is None:
            return
    
        user = User.objects.filter(user_id=chat_id).first()
        if user is None:
            user = User(user_id=chat_id, status=True)
            user.save()
    
        if text == '/start':
            if user.status:
                BotWrapper.BOT.sendMessage(chat_id, "Подписка оформлена")
            else:
                user.status = True
                user.save()
                BotWrapper.BOT.sendMessage(chat_id, "Подписка востановлена")
            
        elif text == '/stop':
            if not user.status:
                BotWrapper.BOT.sendMessage(chat_id, "Подписка не оформлена")
            else:
                user.status = False
                user.save()
                BotWrapper.BOT.sendMessage(chat_id, "Подписка остановлена")
        elif text == '/status':
             BotWrapper.BOT.sendMessage(chat_id, get_status().status)
        elif text == '/info':
             BotWrapper.BOT.sendMessage(chat_id, "Подписано {} аккаунтов".format(User.objects.count()))
    except:
        pass

def get_connect():
    return me.connect(
        config.DB['db'],
        host=config.DB['host'],
        port=config.DB['port'],
        serverSelectionTimeoutMS=2500
    )

def update_feed_messages():
    url = "http://forum.awd.ru/feed.php?f=326&t=326384&rand={0}".format(random.randint(0, 1000000))
    feed = feedparser.parse(url)
    entries = feed.get('entries')
    
    if entries is None or not isinstance(entries, list):
        return
    
    for post in entries[::-1]:
        post_id = post.get('id')
        content = post.get('content', [{}])
        if len(content) == 0:
            continue
        text = content[0].get('value')
        datestruct = post.get("published_parsed")
        if post_id is None or text is None or datestruct is None:
            continue
        
        text, _, _ = text.rpartition('Статистика:')

        bs = bs4.BeautifulSoup(text, 'html.parser')
        for div in bs.find_all("blockquote"):
            div.decompose()
            
        text = bs.get_text()
        
        db_post = Message.objects.filter(message_id=post_id).first()
        if db_post is not None:
            continue
        else:
            db_post = Message(
                message_id=post_id,
                text=text,
                date=datetime.fromtimestamp(mktime(datestruct))
            )
            db_post.save()
        text_lower = text.lower()
        
        for i in range(0, 10):
            text_lower = text_lower.replace('  ', ' ')
        
        if 'мест нет' in text_lower:
            continue

        if 'записи нет' in text_lower or 'нет записи' in text_lower:
            continue

        if 'пусто' in text_lower and len(text_lower) < 20:
            continue
            
        if 'helpvisaus' in text_lower:
            continue
            
        if ('помогу' in text_lower or 'поможем' in text_lower) and 'записаться' in text_lower:
            continue
            
        if 'записи на собеседование нет' in text_lower:
            continue

        if 'нет доступных мест' in text_lower:
            pos = text_lower.index('нет доступных мест')
            if pos == 0 or not('а' <= text_lower[pos-1] <= 'я'):
                continue

        if 'нет мест' in text_lower:
            pos = text_lower.index('нет мест')
            if pos == 0 or not('а' <= text_lower[pos-1] <= 'я'):
                continue
                

        for user in User.objects.filter(status=True):
            BotWrapper.BOT.sendMessage(user.user_id, "{0}: {1}".format(db_post.date + timedelta(hours=3), text)) #, disable_notification=(user.user_id < 0))
    

if __name__ == '__main__':
        get_connect()
        BotWrapper.BOT = telepot.Bot(config.BOT_TOKEN)
        
        ml = MessageLoop(BotWrapper.BOT, handle_message)
        ml.run_as_thread()
        
        while True:
            status = get_status()
            
            def printstatus(message):
                status.status = message
                status.save()
                print(message)

            printstatus("Feed")
            try:
                update_feed_messages()
            except:
                printstatus("Error")
            printstatus("Loop")

            n = 25
            waittime = random.randint(50, 180)
            for i in xrange(0, n):
                time.sleep(waittime // n)
                printstatus("Wait {}..".format(i))
            
