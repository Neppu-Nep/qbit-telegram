#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple bot for using qBit client via Telegram.

import bot_auth
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler)
import logging
import re
from qbittorrent import Client
from qbittorrent import client
from requests import exceptions


class Bot:
    qb = None
    download_folder = "./downloads"
    logged_in = False
    TOKEN = bot_auth.token
    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    logger = logging.getLogger(name=__name__)

    IP = 0
    LOGIN_PROMPT = 1

    ADD_FILE = 0
    ADD_MAGNET_LINK = 0

    ip_port_text = None
    username_password = None

    def start(self, bot, update):
        self.ip_port_text = None
        self.username_password = None
        self.logged_in = False
        user = update.message.from_user
        if str(user.id) in bot_auth.user_id:
            self.logger.info("Authorized usage tried by: %s -- %s" % (user.username, user.id))
            update.message.reply_text(
                "Hello, I'm QBitTorrent Remote controller.\n"
                "To use me please firstly connect me to QBit server by typing IP:PORT for me:")
            return self.IP
        else:
            self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
            update.message.reply_text(
                "You don't have rights to use me! Who the f*** are you?")
            return ConversationHandler.END

    def ip(self, bot, update):
        self.ip_port_text = update.message.text
        user = update.message.from_user
        if re.match('^(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}|localhost):\d{1,5}$', self.ip_port_text):
            self.logger.info("User %s entered a right IP and PORT" % user.id)
            self.logger.info("Trying to connect to client")
            try:
                self.qb = Client("http://%s/" % self.ip_port_text)
                try:
                    self.qb.torrents()
                    self.logger.info("Logging in was successful.")
                    update.message.reply_text("Logged in! Now you can use me.\n"
                                              "To get info about commands type /help")
                    self.logged_in = True
                except client.LoginRequired:
                    self.logger.info("Login required.")
                    update.message.reply_text("Username and password is required to connect client.\n"
                                              "Please enter an username and password by seperating them with space.\n"
                                              "If you don't know username and password you can"
                                              " '/cancel'. and try again later")
                    return self.LOGIN_PROMPT
            except exceptions.ConnectionError:
                self.logger.info("Connection refused.")
                update.message.reply_text("Connection to given IP address is refused."
                                          "\nPlease try again by typing /start")
                self.ip_port_text = None

        else:
            self.logger.info("User %s entered a wrong IP and PORT" % user.id)
            update.message.reply_text("Please enter a proper ip and port. You can restart by typing /start")
        return ConversationHandler.END

    def login(self, bot, update):
        self.logger.info("Checking if message fits the RegEX")
        username_password = update.message.text
        self.username_password = username_password
        user = update.message.from_user
        if re.match('^[^ ]+ [^ ]+$', username_password):
            username_password_split = username_password.split(" ")
            self.logger.info("Trying to login with given username and password")
            try:
                self.qb.login(username=username_password_split[0], password=username_password_split[1])
                self.qb.torrents()
                self.logger.info("Logging in was successful.")
                update.message.reply_text("Logged in! Now you can use me.\n"
                                          "To get info about commands type /help")
                self.logged_in = True
            except client.LoginRequired:
                self.logger.info("Username and Password was wrong")
                update.message.reply_text("Username and Password was wrong\n"
                                          "Please enter a new username and password by seperating them with space.\n"
                                          "If you don't know username and password you can"
                                          " '/cancel'. and try again later")
                return self.LOGIN_PROMPT
            return ConversationHandler.END
        else:
            self.logger.info("Typed message does not match what is asked.")
            update.message.reply_text("Please enter a new username and password by seperating them with space.\n"
                                      "And make sure your username or password does not contain "
                                      "any space(\" \") character"
                                      "If you don't know username and password you can"
                                      " '/cancel'. and try again later")
            return self.LOGIN_PROMPT

    def reconnect(self, bot, update):
        user = update.message.from_user
        if self.ip_port_text is not None and not self.logged_in and str(user.id) in bot_auth.user_id:
            try:
                self.qb = Client("http://%s/" % self.ip_port_text)
                try:
                    self.qb.torrents()
                    self.logger.info("Logging in was successful.")
                    update.message.reply_text("Logged in! Now you can use me.\n"
                                              "To get info about commands type /help")
                    self.logged_in = True
                except client.LoginRequired:
                    self.logger.info("Trying to log in using previous info")
                    username_password_split = self.username_password.split(" ")
                    self.qb.login(username=username_password_split[0], password=username_password_split[1])
                    try:
                        self.qb.torrents()
                        self.logger.info("Logging in was successful.")
                        update.message.reply_text("Logged in! Now you can use me.\n"
                                                  "To get info about commands type /help")
                        self.logged_in = True
                    except client.LoginRequired:
                        self.logger.info("Logging in with old info was unsuccessful.")
                        update.message.reply_text("Logging in with old info was unsuccessful.\n"
                                                  "You can try again later (/reconnect)\nor type new info using /start")

            except exceptions.ConnectionError:
                self.logger.info("Connection refused.")
                update.message.reply_text("Connection to client IP address is refused."
                                          "\nPlease try again by typing /start"
                                          "\nOr try to /reconnect later.")
        elif str(user) not in bot_auth.user_id:
            self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
            update.message.reply_text(
                "You don't have rights to use me! Who the f*** are you?")
        elif self.logged_in:
            self.logger.info("User tried to use reconnect while already logged in.")
            update.message.reply_text("You are already logged in. You don't need to reconnect")

        elif self.ip_port_text is None:
            self.logger.info("User tried to use reconnect without any previous info.")
            update.message.reply_text("You don't have any previous info. \nPlease type /start to connect")


    def cancel(self, bot, update):
        user = update.message.from_user
        self.logger.info("User %s canceled the conversation." % user.first_name)
        update.message.reply_text('Bye! I hope we can talk again some day.')
        self.ip_port_text = None

        return ConversationHandler.END

    def list_downloading_torrents(self, bot, update):
        user = update.message.from_user
        try:
            if str(user.id) in bot_auth.user_id and self.logged_in:
                output = ""
                self.logger.info("%s tried listing downloading." % update.message.from_user)
                if len(self.qb.torrents()) > 0:
                    for torrent in self.qb.torrents(filter="downloading"):
                        output += "--%s, %s%%\n" % (torrent["name"], int(torrent["progress"]*100))
                    update.message.reply_text("Torrents currently downloading:\n%s" % output)
                else:
                    update.message.reply_text("There is no torrents to list.")
            elif not self.logged_in:
                self.logger.info("Usage without logging in tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You should first login by typing /start")
            else:
                self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You don't have rights to use me! Who the f*** are you?")
        except exceptions.ConnectionError:
            self.logger.info("Connection is lost. Retrying to connect...")
            self.logged_in = False
            update.message.reply_text(
                "Ups. Connection to qBit Client is lost. \nRetrying to connect with previous info.")
            return self.reconnect(bot=bot, update=update)

    def list(self, bot, update):
        user = update.message.from_user
        try:
            if str(user.id) in bot_auth.user_id and self.logged_in:
                output = ""
                self.logger.info("%s tried listing." % update.message.from_user)
                if len(self.qb.torrents()) > 0:
                    for torrent in self.qb.torrents():
                        output += "--%s, %s, %s%%\n" % (torrent["name"],torrent["state"].upper(),int(torrent["progress"]*100))
                    update.message.reply_text("Torrents currently downloading:\n%s" % output)
                else:
                    update.message.reply_text("There is no torrents to list.")
            elif not self.logged_in:
                self.logger.info("Usage without logging in tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You should first login by typing /start")
            else:
                self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You don't have rights to use me! Who the f*** are you?")
        except exceptions.ConnectionError:
            self.logger.info("Connection is lost. Retrying to connect...")
            self.logged_in = False
            update.message.reply_text(
                "Ups. Connection to qBit Client is lost. \nRetrying to connect with previous info.")
            return self.reconnect(bot=bot, update=update)

    def pause(self, bot, update, args):
        user = update.message.from_user
        try:
            if str(user.id) in bot_auth.user_id and self.logged_in:
                torrents_to_pause = []
                torrents_copy = self.qb.torrents().copy()
                for arg in args:
                    for torrent in torrents_copy:
                        if re.match(arg, torrent["name"], re.IGNORECASE):
                            torrents_copy.remove(torrent)
                            torrents_to_pause.append(str(torrent["hash"]))

                self.qb.pause_multiple(torrents_to_pause)
                self.logger.info("Paused following: %s" % args)
                output = ""
                for torrent in torrents_to_pause:
                    output += "--%s, %s%%\n" % (torrent["name"], int(torrent["progress"]*100))
                update.message.reply_text("Following torrents paused:\n%s" % output)
            elif not self.logged_in:
                self.logger.info("Usage without logging in tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You should first login by typing /start")
            else:
                self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You don't have rights to use me! Who the f*** are you?")
        except exceptions.ConnectionError:
            self.logger.info("Connection is lost. Retrying to connect...")
            self.logged_in = False
            update.message.reply_text(
                "Ups. Connection to qBit Client is lost. \nRetrying to connect with previous info.")
            return self.reconnect(bot=bot, update=update)

    def pause_all(self, bot, update):
        user = update.message.from_user
        try:
            if str(user.id) in bot_auth.user_id:
                self.qb.pause_all()
                self.logger.info("Paused all")
            elif not self.logged_in:
                self.logger.info("Usage without logging in tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You should first login by typing /start")
            else:
                self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You don't have rights to use me! Who the f*** are you?")
        except exceptions.ConnectionError:
            self.logger.info("Connection is lost. Retrying to connect...")
            self.logged_in = False
            update.message.reply_text(
                "Ups. Connection to qBit Client is lost. \nRetrying to connect with previous info.")
            return self.reconnect(bot=bot, update=update)

    def resume(self, bot, update, args):
        user = update.message.from_user
        try:
            if str(user.id) in bot_auth.user_id:
                torrents_to_resume = []
                torrents_copy = self.qb.torrents().copy()
                for arg in args:
                    for torrent in torrents_copy:
                        if re.match(arg, torrent["name"], re.IGNORECASE):
                            torrents_copy.remove(torrent)
                            torrents_to_resume.append(str(torrent["hash"]))

                self.qb.resume_multiple(torrents_to_resume)
                self.logger.info("Paused following: %s" % args)
                output = ""
                for torrent in torrents_to_resume:
                    output += "--%s, %s%%\n" % (torrent["name"], int(torrent["progress"]*100))
                update.message.reply_text("Following torrents resumed:\n%s" % output)
            elif not self.logged_in:
                self.logger.info("Usage without logging in tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You should first login by typing /start")
            else:
                self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You don't have rights to use me! Who the f*** are you?")
        except exceptions.ConnectionError:
            self.logger.info("Connection is lost. Retrying to connect...")
            self.logged_in = False
            update.message.reply_text(
                "Ups. Connection to qBit Client is lost. \nRetrying to connect with previous info.")
            return self.reconnect(bot=bot, update=update)

    def resume_all(self, bot, update, args):
        user = update.message.from_user
        try:
            if str(user.id) in bot_auth.user_id:
                self.qb.resume_all()
                self.logger.info("Resumed all")
            elif not self.logged_in:
                self.logger.info("Usage without logging in tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You should first login by typing /start")
            else:
                self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You don't have rights to use me! Who the f*** are you?")
        except exceptions.ConnectionError:
            self.logger.info("Connection is lost. Retrying to connect...")
            self.logged_in = False
            update.message.reply_text(
                "Ups. Connection to qBit Client is lost. \nRetrying to connect with previous info.")
            return self.reconnect(bot=bot, update=update)

    def add(self, bot, update):
        user = update.message.from_user
        try:
            if str(user.id) in bot_auth.user_id:
                update.message.reply_text("Send .torrent file you want to download.")
                return self.ADD_FILE
            elif not self.logged_in:
                self.logger.info("Usage without logging in tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You should first login by typing /start")
            else:
                self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You don't have rights to use me! Who the f*** are you?")
            return ConversationHandler.END
        except exceptions.ConnectionError:
            self.logger.info("Connection is lost. Retrying to connect...")
            self.logged_in = False
            update.message.reply_text(
                "Ups. Connection to qBit Client is lost. \nRetrying to connect with previous info.")
            self.reconnect(bot=bot, update=update)
            return ConversationHandler.END

    def add_magnet(self, bot, update):
        user = update.message.from_user
        try:
            if str(user.id) in bot_auth.user_id:
                update.message.reply_text("Send magnet you want to download.")
                return self.ADD_MAGNET_LINK
            elif not self.logged_in:
                self.logger.info("Usage without logging in tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You should first login by typing /start")
            else:
                self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You don't have rights to use me! Who the f*** are you?")
            return ConversationHandler.END
        except exceptions.ConnectionError:
            self.logger.info("Connection is lost. Retrying to connect...")
            self.logged_in = False
            update.message.reply_text(
                "Ups. Connection to qBit Client is lost. \nRetrying to connect with previous info.")
            self.reconnect(bot=bot, update=update)
            return ConversationHandler.END

    def add_file(self, bot, update):
        try:
            user = update.message.from_user
            if str(user.id) in bot_auth.user_id:
                update.message.reply_text("File received. ")
                file = bot.get_file(file_id=update.message.document.file_id)
                # print(file)
                document = update.message.document
                file_extension = document.file_name.split(".")[-1]
                if re.match("^torrent$", file_extension, re.IGNORECASE):
                    # file.
                    file.download(custom_path="%s/%s" % (self.download_folder, document.file_name))
                    file_read = open("%s/%s" % (self.download_folder, document.file_name), "rb")
                    self.logger.info("Torrent file downloaded to %s" % self.download_folder)
                    self.qb.download_from_file(file_read)
                    self.logger.info("Started downloading %s" % document.file_name)
                    update.message.reply_text("Downloading the file.")
            elif not self.logged_in:
                self.logger.info("Usage without logging in tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You should first login by typing /start")
            else:
                self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You don't have rights to use me! Who the f*** are you?")

            return ConversationHandler.END
        except exceptions.ConnectionError:
            self.logger.info("Connection is lost. Retrying to connect...")
            self.logged_in = False
            update.message.reply_text(
                "Ups. Connection to qBit Client is lost. \nRetrying to connect with previous info.")
            self.reconnect(bot=bot, update=update)
            return ConversationHandler.END

    def add_magnet_link(self, bot, update):
        try:
            user = update.message.from_user
            if str(user.id) in bot_auth.user_id:
                update.message.reply_text("Link received.")
                magnet_link = update.message.text
                self.qb.download_from_link(magnet_link)
                update.message.reply_text("Downloading the file.")
            elif not self.logged_in:
                self.logger.info("Usage without logging in tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You should first login by typing /start")
            else:
                self.logger.info("Unauthorized usage tried by: %s -- %s" % (user.username, user.id))
                update.message.reply_text(
                    "You don't have rights to use me! Who the f*** are you?")

            return ConversationHandler.END
        except exceptions.ConnectionError:
            self.logger.info("Connection is lost. Retrying to connect...")
            self.logged_in = False
            update.message.reply_text(
                "Ups. Connection to qBit Client is lost. \nRetrying to connect with previous info.")
            self.reconnect(bot=bot, update=update)
            return ConversationHandler.END
			
    def help(self, bot, update):
        update.message.reply_text("Simple bot for using qBit client via Telegram.\n"
                                  "Available commands:\n"
                                  "/start\n"
                                  "--- Start logging in process with new info.\n"
                                  "/reconnect\n"
                                  "--- Try to reconnect using previously entered info.\n"
                                  "/pause NAME1 NAME2 NAME3 ...\n"
                                  "--- Pause torrents : NAME1, NAME2 etc.\n"
                                  "/pause_all\n"
                                  "--- Pause all torrents.\n"
                                  "/resume NAME1 NAME2 NAME3 ...\n"
                                  "--- Resume torrents : NAME1, NAME2 etc.\n"
                                  "/resume_all\n"
                                  "--- Resume all torrents. \n"
                                  "/list\n"
                                  "--- List all torrents.\n"
                                  "/downloading\n"
                                  "--- List all torrents with Downloading status\n"
                                  "/add\n"
                                  "--- Start downloading of a new .torrent file.\n"
                                  "/add_magnet\n"
                                  "--- Start downloading of a new magnet link.\n"
                                  "/help\n"
                                  "--- Display this message.\n"
                                  "PS: NAME1 NAME2 etc. does *NOT* have to be FULL name.")

    def error(self, bot, update, error):
        self.logger.warn('Update "%s" caused error "%s"' % (update, error))

    def main(self):
        # Create the EventHandler and pass it your bot's token.
        updater = Updater(self.TOKEN)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
        conv_handler_start = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],

            states={
                self.IP: [MessageHandler(Filters.text, self.ip)],
                self.LOGIN_PROMPT: [MessageHandler(Filters.text, self.login)]
            },

            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        conv_handler_torrent = ConversationHandler(
            entry_points=[CommandHandler("add", self.add)],

            states={
                self.ADD_FILE: [MessageHandler(Filters.document, self.add_file)]
            },

            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        conv_handler_magnet = ConversationHandler(
            entry_points=[CommandHandler("add_magnet", self.add_magnet)],

            states={
                self.ADD_MAGNET_LINK: [MessageHandler(Filters.text, self.add_magnet_link)]
            },

            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        # dp.add_handler()
        dp.add_handler(conv_handler_start)
        dp.add_handler(conv_handler_torrent)
        dp.add_handler(conv_handler_magnet)
        dp.add_handler(CommandHandler("downloading", self.list_downloading_torrents))
        dp.add_handler(CommandHandler("list", self.list))
        dp.add_handler(CommandHandler("pause", self.pause, pass_args=True))
        dp.add_handler(CommandHandler("resume", self.resume, pass_args=True))
        dp.add_handler(CommandHandler("pause_all", self.pause_all))
        dp.add_handler(CommandHandler("resume_all", self.resume_all, pass_args=True))
        dp.add_handler(CommandHandler("reconnect", self.reconnect))
        dp.add_handler(CommandHandler("help", self.help))
        # log all errors
        dp.add_error_handler(self.error)

        # Start the Bot
        updater.start_polling()

        # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()


if __name__ == '__main__':
    bot = Bot()
    bot.main()
