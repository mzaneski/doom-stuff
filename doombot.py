import sys
import os
import subprocess
import threading
import time
import asyncio
import datetime
import random
import pyinotify

import discord

from doom_monitor import T_DoomMonitor
from collections import deque

OWNER_ID = ''
BOT_TOKEN = ''

def command(admin_only=False, **m_kwargs):
    def wrap(func):
        async def deco(bot, message, *args, **kwargs):
            if deco.admin_only and not message.author.server_permissions.administrator:
                chk1 = not message.author.server_permissions.administrator
                chk2 = not message.author.id == OWNER_ID
                if chk1 and chk2:
                    return
            if message.channel.is_private:
                return

            await func(bot, message, *args, **kwargs)

        setattr(deco, 'admin_only', admin_only)

        for k in m_kwargs:
            setattr(deco, k, m_kwargs[k])

        return deco
    return wrap

@command()
async def help(bot, message, **kwargs):
    cmds = 'USER COMMANDS:\n'
    cmds_admin = '\nADMIN COMMANDS:\n'
    for cmd in bot.commands:
        w = ''
        try:
            h = getattr(bot.commands[cmd], 'help_str')
        except:
            h = ''
        if bot.commands[cmd].admin_only:
            cmds_admin += (bot.command_prefix + cmd + ' ' + h + w + '\n')
        else:
            cmds += (bot.command_prefix + cmd + ' ' + h + w + '\n')
    await bot.send_message(message.channel, '```' + cmds + cmds_admin + '```')

@command(admin_only=True, allow_whitelist=False, help_str='<single char>')
async def prefix(bot, message, split_text=[''], **kwargs):
    try:
        if len(split_text[1]) > 1:
            raise IndexError
        bot.command_prefix = split_text[1]
    except IndexError:
        await bot.send_message(message.channel, 'Invalid arguments. Proper usage: {}prefix <single char>'.format(bot.command_prefix))
    except ValueError:
        await bot.send_message(message.channel, 'Invalid arguments. Choose a different character')
    else:
        await bot.send_message(message.channel, 'Bot command prefix changed to {}'.format(bot.command_prefix))

@command()
async def doom(bot, message, **kwargs):
    if len(bot.reader.players) < 1:
        pnames = 'No players connected.'
    else:
        pnames = 'Players connected: ' + ', '.join([pname for pname in bot.reader.players])

    with open('./config/hostname.cfg', 'r') as f:
        line = f.readline()
        server_info = line[line.find(' ')+2:-2]

    s = '**{0}** `{1}`\n{2}'.format(bot.server_ip, server_info, pnames)
    await bot.send_message(message.channel, s)

class DoomBot(discord.Client):

    def __init__(self, owner_id, bot_token):
        super().__init__(max_messages=100)

        self.owner = owner_id
        self.token = bot_token

        self.command_prefix = '!'

        self.commands = {}
        self.commands['help'] = help
        self.commands['prefix'] = prefix
        self.commands['doom'] = doom

        self.server_ip = '127.0.0.1:10666'
        self.doom_channel_id = ''
        self.doom_channel = discord.Object(id=self.doom_channel_id)
        self.reader = None

    def run(self):
        super().run(self.token)

        self.loop.create_task(self.listen_for_server())

    async def on_ready(self):
        print('Bot logged in successfully. ' + datetime.datetime.now().strftime("%H:%M %m-%d-%Y"))
        print(self.user.name)
        print(self.user.id)

    async def on_message(self, message):
        if message.content and message.content[0] == self.command_prefix:
            content = message.content.split(' ')
            if content[0][1:] in self.commands:
                await self.commands[content[0][1:]](self, message, split_text=content)

    def get_logger_pid(self):
        proc = subprocess.Popen('./utils/get_logger_pid.sh',
                                stdout=subprocess.PIPE)

        out, _ = proc.communicate(timeout=5)
        PID = out.decode('ascii').strip()
        if proc.poll() is None:
            proc.kill()

        if PID.isspace() or not PID.isdigit():
            return None
        else:
            return PID

    async def listen_for_server(self, wait_time=10):
        PID = self.get_logger_pid()
        while not PID:
            await asyncio.sleep(wait_time)
            PID = self.get_logger_pid()

        if self.reader is None:
            self.loop.create_task(self.monitor_server(PID))

    async def monitor_server(PID, wait_time=1):
        cmd = ['tail', '-f', '-n', '1', '--pid={}'.format(PID), '/proc/{}/fd/1'.format(PID)]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        out_q = deque()
        self.reader = T_DoomMonitor(proc.stdout, out_q, interval=wait_time)
        self.reader.start()

        try:
            while not self.reader.eof():
                while out_q:
                    line = out_q.popleft()
                    if self.doom_channel.id != '':
                        await self.send_message(self.doom_channel, line)

                if not proc.poll() is None and self.reader.is_alive():
                    self.reader.stop_monitoring()

                await asyncio.sleep(wait_time)
        finally:
            if self.reader.is_alive() and not self.reader.abort:
                self.reader.stop_monitoring()

            self.reader.join()
            proc.stdout.close()
            if proc.poll() is None:
                proc.kill()

            self.reader = None
            self.loop.create_task(self.listen_for_server())

if __name__ == '__main__':
    cl = DoomBot(OWNER_ID, BOT_TOKEN)

    cl.run()
