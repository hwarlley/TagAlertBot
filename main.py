#!/usr/bin/env python3


#############################################
#                                           #
#  IMPORT                                   #
#                                           #
#############################################

import re
import logging
from time import time, strftime

from config import *
from aux import *


#############################################
#                                           #
#  HANDLERS                                 #
#                                           #
#############################################

# Handle messages from banned users, doing...nothing
@bot.message_handler(func=lambda message: is_banned(message.from_user.id))
def skip_messages(message):
    pass


# /start or /help: Explain bot's features and add user if not present in DB
@bot.message_handler(commands=['start', 'help'])
def help(message):
    if is_flooding(message.from_user.id):
        return

    param = message.text.split()
    send_log(message, "help")
    if len(param) == 1:
        if is_group(message):
            bot.reply_to(message, lang('help_group', message.from_user.id), parse_mode="markdown")
        else:
            bot.send_message(message.chat.id, lang('help', message.from_user.id), parse_mode="markdown")

        check_and_add(message.from_user.id, message.from_user.username)
    elif len(param) == 2:
        # m_id[0] -> message id
        # m_id[1] -> chat id
        m_id = param[1].split('_')

        try:
            bot.send_message(-int(m_id[1]), lang('findmsg_group', message.from_user.id) % message.from_user.username, reply_to_message_id=int(m_id[0]))
            bot.reply_to(message, lang('findmsg_private', message.from_user.id))
        except Exception:
            bot.reply_to(message, lang('findmsg_error', message.from_user.id), parse_mode="markdown")

    else:
        bot.reply_to(message, lang('start_error', message.from_user.id), parse_mode="markdown")


# Retrieve the message
@bot.message_handler(func=lambda message: is_retrieve(message))
def retrieve(message):
    if is_group(message) or is_flooding(message.from_user.id):
        return

    send_log(message, "retrieve")
    
    # m_id[0] -> message id
    # m_id[1] -> chat id
    m_id = (message.text)[9:].split('_')

    try:
        bot.send_message(-int(m_id[1]),
                         lang('findmsg_group', message.from_user.id) % message.from_user.username,
                         reply_to_message_id=int(m_id[0])
                        )
        bot.reply_to(message, lang('findmsg_private', message.from_user.id))
    except Exception:
        bot.reply_to(message, lang('findmsg_error', message.from_user.id), parse_mode="markdown")

    check_and_add(message.from_user.id, message.from_user.username)


# /ignoreXXXX - Add XXX to ignored list for user
@bot.message_handler(func=lambda message: is_ignore(message))
def ignore_h(message):
    if is_group(message) or is_flooding(message.from_user.id):
        return

    send_log(message, "ignore")
    
    if (ignore(message.from_user.id, (message.text)[7:]) == 1):
        bot.reply_to(message, lang('ignore_user_success', message.from_user.id)  % (message.text)[7:])
    else:
        bot.reply_to(message, lang('ignore_user_fail', message.from_user.id) % (message.text)[7:])

    check_and_add(message.from_user.id, message.from_user.username)


# /ignoreXXXX - Add XXX to ignored list for user
@bot.message_handler(func=lambda message: is_unignore(message))
def unignore_h(message):
    if is_group(message) or is_flooding(message.from_user.id):
        return

    send_log(message, "unignore")
    
    if (unignore(message.from_user.id, (message.text)[9:]) == 1):
        bot.reply_to(message, lang('unignore_user_success', message.from_user.id)  % (message.text)[9:])
    else:
        bot.reply_to(message, lang('unignore_user_fail', message.from_user.id) % (message.text)[9:])

    check_and_add(message.from_user.id, message.from_user.username)


# /enable: Update (or add new) settings for user in DB enabling alerts
@bot.message_handler(commands=['enable'])
def enablealerts(message):
    if is_flooding(message.from_user.id):
        return

    send_log(message, "enable")
    if is_private(message):
        if message.from_user.username is None:
            # No username set
            bot.send_message(message.chat.id, lang('warning_no_username', message.from_user.id))

        else:
            if check_and_add(message.from_user.id, message.from_user.username, enabled=True):
                # Present in database, enable alerts and update the username (even if not needed)
                update_user(message.from_user.id, message.from_user.username, new_enabled=True)
                global enabled_users
                enabled_users += 1

            bot.send_message(message.chat.id, lang('enable_success', message.from_user.id), parse_mode="markdown")

    else:
        bot.reply_to(message, lang('warning_group', message.from_user.id), parse_mode="markdown")

  
# /disable: Update (or add new) settings for user in DB disabling alerts
@bot.message_handler(commands=['disable'])
def disablealerts(message):
    if is_flooding(message.from_user.id):
        return

    send_log(message, "disable")
    if is_private(message):
        if message.from_user.username is None:
            bot.send_message(message.chat.id, lang('warning_no_username', message.from_user.id))

        else:
            if check_and_add(message.from_user.id, message.from_user.username, "en", enabled=True):
                # Present in database, enable alerts and update the username (even if not needed)
                update_user(message.from_user.id, message.from_user.username, new_enabled=False)
                global enabled_users
                enabled_users -= 1

            bot.send_message(message.chat.id, lang('disable_success', message.from_user.id), parse_mode="markdown")

    else:
        bot.reply_to(message, lang('warning_group', message.from_user.id), parse_mode="markdown")


@bot.message_handler(commands=['setlang'])
def setlang(message):
    if is_flooding(message.from_user.id):
        return

    send_log(message, "setlang")
    if is_private(message):
        msg = bot.reply_to(message, "%s\n%s" % (lang("setlang_start", message.from_user.id), setlang_list), parse_mode="markdown")
    else:
        bot.reply_to(message, lang('warning_group', message.from_user.id), parse_mode="markdown")


@bot.message_handler(commands=lang_list)
def setlang_update(message):
    if is_flooding(message.from_user.id):
        return
    send_log(message, "change language")
    if is_private(message):
        if message.from_user.username is None:
            bot.send_message(message.chat.id, lang('warning_no_username', message.from_user.id))
        else:
            new_lang = message.text[1:3].lower()
            if check_and_add(message.from_user.id, message.from_user.username, new_lang):
                # Present in database, change his lang
                update_user(message.from_user.id, message.from_user.username, new_lang)
            bot.send_message(message.chat.id, lang('setlang_success', message.from_user.id), parse_mode="markdown")
    else:
        bot.reply_to(message, lang('warning_group', message.from_user.id), parse_mode="markdown")


# /donate: Beg for some money (not so useful, though :P)
@bot.message_handler(commands=['dona', 'donate'])
def dona(message):
    if is_flooding(message.from_user.id):
        return
    send_log(message, "donate")

    if is_private(message):
        bot.send_message(message.chat.id, lang('donate', message.from_user.id), parse_mode="markdown", disable_web_page_preview="true")
    else:
        bot.reply_to(message, lang('donate', message.from_user.id), parse_mode="markdown", disable_web_page_preview="true")

    check_and_add(message.from_user.id, message.from_user.username)



#/credits: Let's thanks someone
@bot.message_handler(commands=['credits'])
def credits(message):
    if is_flooding(message.from_user.id):
        return
    send_log(message, 'credits')
    
    msg = "Bot created by @Zaphodias.\nThanks to @Pilota for helping the bot become more popular.\n\nTranslators:\n*Arabic*: @MRVMVX.\n*Spanish*: @giosann and @imiguelacuna.\n*German*: @F63NNKJ4.\n\nJoin @zaphodiasgroup to get help."

    if is_private(message):
        bot.send_message(message.chat.id, msg, parse_mode="markdown")
    else:
        bot.reply_to(message, msg, parse_mode="markdown")


# /feedback or /report: Share the email address so users can contact owner
@bot.message_handler(commands=['feedback', 'report'])
def feedback(message):
    if is_flooding(message.from_user.id):
        return
    send_log(message, "feedback")
    if is_group(message):
        bot.reply_to(message, lang('warning_group', message.from_user.id), parse_mode="markdown")
    else:
        msg = bot.reply_to(message, lang('feedback_start', message.from_user.id), parse_mode="markdown")
        bot.register_next_step_handler(msg, feedback_send)
    
   
def feedback_send(message):
    if is_flooding(message.from_user.id):
        return
    if message.text.lower() == "/cancel" or message.text.lower() == "/cancel@tagalertbot":
        send_log(message, "cancel")
        bot.reply_to(message, lang('feedback_cancel', message.from_user.id), parse_mode="markdown")

    elif message.text[0] == '/':
        pass

    else:
        send_feedback(message)
        bot.reply_to(message, lang('feedback_success', message.from_user.id), parse_mode="markdown")


# /stats: Show some numbers
@bot.message_handler(commands=['stats', 'statistics'])
def stats(message):
    if is_flooding(message.from_user.id):
        return
    send_log(message, "stats")
    bot.reply_to(message, lang('stats', message.from_user.id) % (known_users, enabled_users), parse_mode="markdown")
    check_and_add(message.from_user.id, message.from_user.username)


# /ban: For admin only, ability to ban by ID
@bot.message_handler(commands=['ban'])
def banhammer(message):
    if admin_id == message.from_user.id:
        param = message.text.split()
        if len(param) > 1:
            if check_and_add(message.from_user.id, message.from_user.username):
                
                # Present in database, ban id and update the username (even if not needed)
                ban_user(int(param[1]))
                
                timestamp = strftime("%Y-%m-%d %H:%M:%S")
                log_bot.send_message(admin_id, lang('banned_success', message.from_user.id) % (timestamp, int(param[1])))
        else:
            bot.reply_to(message, lang('too_many_args', message.from_user.id))


# /unban: For admin only, ability to unabn by ID
@bot.message_handler(commands=['unban'])
def unbanhammer(message):
    if admin_id == message.from_user.id:
        param = message.text.split()
        if len(param) > 1:
            if check_and_add(message.from_user.id, message.from_user.username):
                
                # Present in database, ban id and update the username (even if not needed)
                unban_user(int(param[1]))

                timestamp = strftime("%Y-%m-%d %H:%M:%S")
                log_bot.send_message(admin_id, lang('unbanned_success', message.from_user.id) % (timestamp, int(param[1])))
        else:
            bot.reply_to(message, lang('too_many_args', message.from_user.id))


# /sourcecode: Show a link for source code on github
@bot.message_handler(commands=['sourcecode'])
def sourcecode(message):
    if is_flooding(message.from_user.id):
        return
    send_log(message, "sourcecode")
    bot.reply_to(message, lang('sourcecode', message.from_user.id), parse_mode="markdown")


# Every text, photo or video. Search for @tags, search every tag in DB and contact the user if alerts are enabled
@bot.message_handler(content_types=['text', 'photo', 'video'])
def aggiornautente(message):
    if is_group(message):
        matched = []

        if message.text is not None:
            matched = list(set(re.findall("@([a-zA-Z0-9_]*)", message.text)))

        if message.caption is not None:
            matched = list(set(re.findall("@([a-zA-Z0-9_]*)", message.caption)))

        if len(matched) > 0:
            if is_flooding(message.from_user.id):
                return
            send_log(message, "TAG")

        for user in matched:
            try:
                # Search for `user` in the JSON file and get the ID
                (userid, enabled) = get_by_username(user)
            except ValueError:
                # If username is not present, is not enabled
                enabled = False

            if enabled and not is_ignored(userid, message.from_user.id):
                mittente = message.from_user.first_name.replace("_", "\_")
                if message.from_user.username is not None:
                    mittente = "@%s" % message.from_user.username.replace("_", "\_")

                testobase = lang('alert_main', userid) % (mittente, message.chat.title.replace("_", "\_"))
                comando = lang('alert_link', userid) % (message.message_id, -message.chat.id, message.from_user.id)

                if message.content_type == 'text':
                    testo = "%s\n%s\n\n%s" % (testobase, message.text.replace("_", "\_"), comando)
                    if message.reply_to_message is not None and message.text is not None:
                        testo = "%s\n\n%s" % (testo, lang('alert_reply', userid))
                        bot.send_message(userid, testo, parse_mode="markdown", disable_web_page_preview="true")
                        bot.forward_message(userid, message.chat.id, message.reply_to_message.message_id)

                    else:
                        bot.send_message(userid, testo, parse_mode="markdown", disable_web_page_preview="true")


                elif message.content_type == 'photo' or message.content_type == 'video':
                    testo = "%s\n\n%s" % (testobase, comando)
                    bot.send_message(userid, testo, parse_mode="markdown", disable_web_page_preview="true")
                    bot.forward_message(userid, message.chat.id, message.message_id)

                    if message.reply_to_message is not None:
                        bot.send_message(userid, lang('alert_reply', userid), parse_mode="markdown")
                        bot.forward_message(userid, message.chat.id, message.reply_to_message.message_id, disable_web_page_preview="true")


    check_and_add(message.from_user.id, message.from_user.username)


#############################################
#                                           #
#  POLLING                                  #
#                                           #
#############################################

bot.polling(none_stop=True)
