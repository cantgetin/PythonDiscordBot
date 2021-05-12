import os
import discord
import sys
import json
from discord.ext import commands

# Path of project
path = os.path.abspath(os.path.dirname(__file__))
os.chdir(path)  # for relative files
sys.path.insert(0, path)  # for modules load

# Path to data.json file
cwd = os.getcwd()
json_file_path = '%s/%s' % (cwd, 'data.json')
data_props = {}

try:
    with open(json_file_path) as data_file:
        data_props = json.load(data_file)
except IOError as e:
    print('Exception while trying to open json: ' + e.__str__())

token = data_props['token']
initial_extensions = ['cogs.among', 'cogs.osu']
bot = commands.Bot(command_prefix=['.', '@'])

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=".help"))
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    print(f'Successfully logged in and booted...!')


@bot.command(brief='Clears N messages in text channel.')
async def clear(ctx, limit: int = None):
    if ctx.message.author.guild_permissions.administrator:
        passed = 0
        failed = 0
        async for msg in ctx.message.channel.history(limit=limit):
            try:
                await msg.delete()
                passed += 1
            except:
                failed += 1
        await ctx.send(f"[Complete] Removed {passed} messages with {failed} fails")

bot.run(token)  # , bot=True, reconnect=True)
