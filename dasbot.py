#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib3
import threading
urllib3.disable_warnings()

import requests, argparse, uuid
from random import randint
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import logging
import datetime
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

GLOBAL_TIMEOUT = 300
SUSHI = {}

TABLE_GROS = {
    76776913: 4, # Kiki
    73275445: 2, # Titine
    138210703: 3, # MuadTib
    122225369: 4, # Benson
    413440057: 4, # Val
    106171943: 4, # Dem
    }

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='Salut les moules! Qui veut bouffer des sushis ??', timeout=GLOBAL_TIMEOUT)

def help_command(bot, update):
    logger.info("Help asked by '%s %s' (id=%s)" % (update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.id))
    help_text = """
Le but du bot c'est de s'assurer que Thibaud Camion il commande le bon nombre de sushis ...
/sushi pour commancer une commande de sushis
/stop pour terminer la commande en cours
/result pour voir la commande en cours
    """
    bot.send_message(chat_id=update.message.chat_id, text=help_text, timeout=GLOBAL_TIMEOUT)

def sushi(bot, update):
    """
    Telegram command to propose a sushi order
    /sushi
    """
    chat_id = update.message.chat_id
    _internal_sushi(bot, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.id, chat_id)

def _internal_sushi(bot, first_name, last_name, user_id, chat_id):
    """
    Telegram command to propose a sushi order
    """
    logger.info("Sushi asked by '%s %s' (id=%s)" % (first_name, last_name, user_id))
    chat_member_count = bot.get_chat_members_count(chat_id)
    global SUSHI
    
    if SUSHI.get(chat_id) is not None:
        bot.send_message(chat_id=chat_id, text="Y a déjà une commande en cours. Si tu veux lancer un nouveau vote, termine celui là avec /stop. Bisous.", timeout=GLOBAL_TIMEOUT)
        return

    vote_id = str(uuid.uuid4())
    SUSHI[chat_id] = {'id': vote_id, 'votes' : {}, 'total': 0}
    
    keyboard = [[InlineKeyboardButton(text="Ouiiiiiiii", callback_data="%s|1" % vote_id),
                 InlineKeyboardButton(text="Bof j'ai pas faim", callback_data="%s|0" % vote_id)]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(chat_id=chat_id, text='Qui qui veut des sushis ?', reply_markup=reply_markup, timeout=GLOBAL_TIMEOUT)

def button(bot, update):
    """
    Telegram button callback for the votes
    """
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    data = query.data.split("|")
    global SUSHI

    if SUSHI.get(chat_id) is None:
        return

    vote_id = SUSHI[chat_id]['id']
    votes = SUSHI[chat_id]['votes']
    total = SUSHI[chat_id]['total']
    logger.info("das_vote_callback - total = %s" % total)

    if len(data) == 2:
        if vote_id == data[0]:
            choice = int(data[1])
            if not user_id in votes.keys():
                if choice == 1:
                    if TABLE_GROS.get(user_id):
                        gros = TABLE_GROS[user_id]
                        logger.info("das_vote_callback - gros = %s" % gros)
                        total += gros
                    else:
                        bot.send_message(chat_id=chat_id, text="id non référencée chez les gros : %s" % user_id, timeout=GLOBAL_TIMEOUT)
                    
                voter = query.from_user.username
                if voter is None:
                    voter = query.from_user.first_name
                text = u"%s a répondu !" % voter
                bot.send_message(chat_id=chat_id, text=text, timeout=GLOBAL_TIMEOUT)
        
                logger.info("das_vote_callback - %s - %s" % (voter, user_id))
                
                SUSHI[chat_id]['votes'][user_id] = choice
                SUSHI[chat_id]['total'] = total

def stoporder(bot, update):
    """
    Telegram command to close a sushi order
    /stop
    """
    _internal_stoporder(bot, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.id, update.message.chat_id)

def _internal_stoporder(bot, first_name, last_name, user_id, chat_id):
    """
    Telegram command to close a sushi order
    """
    _internal_result(bot, first_name, last_name, user_id, chat_id)
    global SUSHI
    if SUSHI.get(chat_id):
        SUSHI[chat_id] = None

def result(bot, update):
    """
    Telegram command to see the current results of a sushi order (without closing it)
    /result
    """
    _internal_result(bot, update.message.from_user.first_name, update.message.from_user.last_name, update.message.from_user.id, update.message.chat_id)

def _internal_result(bot, first_name, last_name, user_id, chat_id):
    """
    Telegram command to see the current results of a sushi order  (without closing it)
    /result
    """
    logger.info("Vote results asked by '%s %s' (id=%s)" % (first_name, last_name, user_id))
    global SUSHI
    if SUSHI.get(chat_id) is None:
        bot.send_message(chat_id=chat_id, text="Y a pas de commande en cours ...", timeout=GLOBAL_TIMEOUT)
    else:
        total = SUSHI[chat_id]['total']
        bot.send_message(chat_id=chat_id, text="Nombre total de rolls a commander: %s" % (total), timeout=GLOBAL_TIMEOUT)
        logger.info("results - %s" % total)

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))
    if update and update.message and update.message.chat_id:
        bot.send_message(chat_id=update.message.chat_id, text=unicode("ERROR !!!!\n%s" % (error)), timeout=GLOBAL_TIMEOUT)

def main(token):
    # Create the Updater and pass it your bot's token.
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("sushi", sushi))
    dp.add_handler(CommandHandler("stop", stoporder))
    dp.add_handler(CommandHandler("result", result))
    dp.add_handler(CallbackQueryHandler(button))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    logger.info("start listening ...")
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="This is Das Bot for Telegram Sushi Tina !",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--token', required=True, help='The bot token !')

    options = parser.parse_args()
    main(options.token)