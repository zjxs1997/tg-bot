import logging
import os
import pickle
import random
from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, Filters, InlineQueryHandler
from config import davy_bot_TOKEN, key_word_DIR


if not os.path.exists(key_word_DIR):
    key_word_DIR = dict()
else:
    fin = open(key_word_DIR, 'rb')
    key_word_dict = pickle.load(fin)
    fin.close()

updater = Updater(token=davy_bot_TOKEN)
dispatcher = updater.dispatcher
jobqueue = updater.job_queue



alert_schedule_dict = dict()


def start(bot, update):
    welcome_word = 'hello from bot!\n'
    welcome_word += 'please use /add command to add keywords and their responces.\n'
    welcome_word += 'use /list command to see all responces of one keyword'
    bot.send_message(chat_id=update.message.chat_id, text=welcome_word)

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


def add(bot, update, args):
    if len(args) != 2:
        bot.send_message(chat_id=update.message.chat_id, text='the number of arguments must be 2!')
        return
    if args[0] not in key_word_dict:
        key_word_dict[args[0]] = [args[1]]
    else:
        if args[1] in key_word_dict[args[0]]:
            bot.send_message(chat_id=update.message.chat_id, text='already exist!')
            return
        key_word_dict[args[0]].append(args[1])
    fout = open(key_word_DIR, 'wb')
    pickle.dump(key_word_dict, fout)
    fout.close()
    bot.send_message(chat_id=update.message.chat_id, text='done!')

add_handler = CommandHandler('add', add, pass_args=True)
dispatcher.add_handler(add_handler)


def list_keyword(bot, update, args):
    if len(args) != 1:
        bot.send_message(chat_id=update.message.chat_id, text='the number of arguments must be 1!')
        return
    if args[0] not in key_word_dict:
        bot.send_message(chat_id=update.message.chat_id, text='keyword not exist!')
        return
    all_list = '\n'.join(key_word_dict[args[0]])
    bot.send_message(chat_id=update.message.chat_id, text=all_list)

list_handler = CommandHandler('list', list_keyword, pass_args=True)
dispatcher.add_handler(list_handler)


def delete_key_word(bot, update, args):
    if len(args) != 2:
        bot.send_message(chat_id=update.message.chat_id, text='the number of arguments must be 2!')
        return
    if args[0] not in key_word_dict or args[1] not in key_word_dict[args[0]]:
        bot.send_message(chat_id=update.message.chat_id, text='keyword not exist!')
        return
    key_word_dict[args[0]].remove(args[1])
    if len(key_word_dict[args[0]]) == 0:
        key_word_dict.pop(args[0])
    bot.send_message(chat_id=update.message.chat_id, text='done!')

delete_handler = CommandHandler('del', delete_key_word, pass_args=True)
dispatcher.add_handler(delete_handler)


def echo(bot, update):
    key_list = list(key_word_dict.keys())
    candidate_list = []
    for key in key_list:
        if key in update.message.text:
            candidate_list.extend(key_word_dict[key])
    
    if len(candidate_list) == 0:
        bot.send_message(chat_id=update.message.chat_id, text=update.message.text)
    else:
        word = random.choice(candidate_list)
        bot.send_message(chat_id=update.message.chat_id, text=word)

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)


def replyPic(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='黄图？')

replyPic_handler = MessageHandler(Filters.photo, replyPic)
dispatcher.add_handler(replyPic_handler)


def pic(bot, update):
    photo_dir = os.listdir('photo')
    random_photo = random.choice(photo_dir)
    full_dir = os.path.join('photo', random_photo)
    bot.send_photo(chat_id=update.message.chat_id, photo=open(full_dir, 'rb'))

pic_handler = CommandHandler('pic', pic)
dispatcher.add_handler(pic_handler)



def caps(bot, update, args):
    text_caps = ' '.join(args).upper()
    bot.send_message(chat_id=update.message.chat_id, text=text_caps)

caps_handler = CommandHandler('caps', caps, pass_args=True)
dispatcher.add_handler(caps_handler)


def callback_alertme_wrapper(user_id):
    def callback_alertme(bot, job):
        bot.send_message(chat_id=user_id, text='alert you!')
    return callback_alertme


def alertme(bot, update, args):
    if len(args) != 1 or not args[0].isnumeric():
        bot.send_message(chat_id=update.message.chat_id, text='usage: /alertme <interval>, interval must be an int number!')
        return
    if update.message.chat_id in alert_schedule_dict:
        bot.send_message(chat_id=update.message.chat_id, text='already alerting you!')
        return
    time_interval = int(args[0])
    alertme_job = jobqueue.run_repeating(callback_alertme_wrapper(update.message.chat_id), interval=time_interval, first=0)
    alert_schedule_dict[update.message.chat_id] = alertme_job

alertme_handler = CommandHandler('alertme', alertme, pass_args=True)
dispatcher.add_handler(alertme_handler)


def stop_alertme(bot, update):
    if update.message.chat_id not in alert_schedule_dict:
        bot.send_message(chat_id=update.message.chat_id, text='not alerting you')
        return
    alert_schedule_dict[update.message.chat_id].schedule_removal()
    alert_schedule_dict.pop(update.message.chat_id)
    bot.send_message(chat_id=update.message.chat_id, text='asshole')

stop_alertme_handler = CommandHandler('stopalert', stop_alertme)
dispatcher.add_handler(stop_alertme_handler)


def callback_alarmme(bot, job):
    bot.send_message(chat_id=job.context, text='alarm you!')

def callback_alarm_timer(bot, update, job_queue, args):
    bot.send_message(chat_id=update.message.chat_id, text='alarm you in %d seconds' % int(args[0]))
    job_queue.run_once(callback_alarmme, int(args[0]), context=update.message.chat_id)

timer_handler = CommandHandler('alarmme', callback_alarm_timer, pass_job_queue=True, pass_args=True)
dispatcher.add_handler(timer_handler)



# ...
from telegram import InlineQueryResultArticle, InputTextMessageContent
def inline_caps(bot, update):
    query = update.inline_query.query
    if not query:
        return
    results = []
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    bot.answer_inline_query(update.inline_query.id, results)

inline_caps_handler = InlineQueryHandler(inline_caps)
dispatcher.add_handler(inline_caps_handler)



# must be added last
def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='wrong command!')

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)



updater.start_polling()


