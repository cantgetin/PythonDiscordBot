import time
from threading import Timer
from cogs import config
from discord import utils
from discord.ext import commands
from discord import ChannelType
import random

list_of_lobbies = []
mutedList = []
cooldown_list = []
comma = "'"
cooldown_time = 1200


class Among(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, brief="Mutes everyone in voice chat you're in. Only for admins")
    async def mv(self, ctx):
        if ctx.message.author.guild_permissions.administrator:
            print('.mv requested by ' + ctx.author.name.__str__())
            leader = ctx.author
            start = time.time()
            try:
                channel = self.bot.get_channel(leader.voice.channel.id)
                for member in list(channel.members):
                    await member.edit(deafen=True, mute=True)
                    if member not in mutedList:
                        mutedList.append(member)
                end = time.time()
                endedTime = round((end - start), 2)
                await ctx.send('muted everyone in voice channel ' + channel.name + ' in ' + endedTime.__str__() + 's.')
            except AttributeError:
                print("exception in .mv")

    @commands.command(pass_context=True, brief="Unmutes everyone in voice chat you're in. Only for admins")
    async def uv(self, ctx):
        if ctx.message.author.guild_permissions.administrator:
            print('.uv requested by ' + ctx.author.name.__str__())
            leader = ctx.author
            start = time.time()
            end = None
            try:
                channel = self.bot.get_channel(leader.voice.channel.id)
                for member in list(channel.members):
                    await member.edit(deafen=False, mute=False)
                end = time.time()
                endedTime = round((end - start), 2)
                await ctx.send('unmuted everyone in voice channel ' + channel.name + ' in ' + endedTime.__str__() + 's.')
            except AttributeError:
                print("exception in .uv")
            print(end - start)

    @commands.command(pass_context=True, brief="Unmutes everyone who were muted by .mv before. Only for admins")
    async def uvall(self, ctx):
        if ctx.message.author.guild_permissions.administrator:
            print('.uvall requested by ' + ctx.author.name.__str__())
            start = time.time()
            end = None
            try:
                for member in list(mutedList):
                    await member.edit(deafen=False, mute=False)
                end = time.time()
                ended_time = round((end - start), 2)
                await ctx.send('unmuted everyone who were muted before for ' + ended_time.__str__() + 's.')
            except AttributeError:
                print("exception in .uvall")
            print(end - start)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot started')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = utils.get(message.guild.members, id=payload.user_id)
        emoji = None
        try:
            emoji = str(payload.emoji)
            role = utils.get(message.guild.roles, id=config.ROLES[emoji])
            print(member.__str__() + ' added reaction for role' + role.__str__())

            if len([i for i in member.roles if i.id not in config.EXCROLES]) < config.MAX_ROLES_PER_USER:
                await member.add_roles(role)
                print('[SUCCESS] User {0.display_name} has been granted with role {1.name}'.format(member, role))
                print('Колличество правильных ролей: ' + (
                    len([i for i in member.roles if i.id not in config.EXCROLES])).__str__())

            elif ((len([i for i in member.roles if i.id not in config.EXCROLES]) >= config.MAX_ROLES_PER_USER) and (
                    emoji not in config.SPECIALROLES)):
                await message.remove_reaction(payload.emoji, member)
                print('[ERROR] Too many roles for user {0.display_name}'.format(member))

            elif ((len([i for i in member.roles if i.id not in config.EXCROLES]) >= config.MAX_ROLES_PER_USER) and (
                    emoji in config.SPECIALROLES)):
                await member.add_roles(role)
                print('[SUCCESS] User {0.display_name} has been granted with role {1.name}'.format(member, role))
                print('Колличество правильных ролей: ' + (
                    len([i for i in member.roles if i.id not in config.EXCROLES])).__str__())

        except KeyError:
            print('[ERROR KeyError, no role found for ' + emoji)
        except Exception:
            print('exception in on_raw_reaction_add')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = utils.get(message.guild.members, id=payload.user_id)
        emoji = None
        try:
            emoji = str(payload.emoji)
            role = utils.get(message.guild.roles, id=config.ROLES[emoji])
            print(member.__str__() + ' removed reaction for role' + role.__str__())
            await member.remove_roles(role)
            print('[SUCCESS] Role {1.name} has been remove for user {0.display_name}'.format(member, role))

        except KeyError:
            print('[ERROR] KeyError, no role found for ' + emoji)
        except Exception:
            print('exception in on_raw_rection_remove')

    @commands.command(pass_context=True, brief="Working @here with cooldown to gather players")
    async def here(self, ctx):
        if not list_of_lobbies:
            self.fill_list_of_lobbies(ctx)
        try:
            channel = self.bot.get_channel(ctx.author.voice.channel.id)
            self.get_all_users_in_lobby(ctx, channel.id)
            self.check_timers()
            self.check_users()
            if self.check_if_lobby_on_cooldown(channel.id) and self.check_if_user_is_not_on_cooldown(ctx, channel.id):
                if ctx.prefix.__str__() == '@':
                    try:
                        i = 0
                        for member in list(channel.members):
                            i += 1
                        count_needed = 10 - i
                        shit = ctx.message
                        await shit.delete()
                        await ctx.send('@here ' + ctx.author.__str__() + ' needs ' +
                                       count_needed.__str__() + ' more people in ' + channel.name)
                        print('@here called from  ' + channel.id.__str__())
                        self.set_timer_on_lobby(channel.id)
                        self.set_timer_on_users_in_lobby(ctx)
                        self.clear_cooldown_list()
                    except Exception as e:
                        print('Exception in @here command ' + e.__str__())
                        await ctx.send('Something went wrong')
            else:
                await ctx.send("You're on cooldown.")

        except Exception:
            print('Exception in @here command')
            await ctx.send('You are not in voice channel@')

    def check_if_lobby_on_cooldown(self, lobby_id):
        for lobby in list_of_lobbies:
            if lobby_id.__str__() in lobby.__str__():
                if 'Timer' in lobby.__str__():
                    return False
                else:
                    return True

    def fill_list_of_lobbies(self, ctx):
        channels = (c.id for c in ctx.message.guild.channels if c.type == ChannelType.voice)
        print('list of lobbies:')
        i = 0
        for c in channels:
            i += 1
            print('added vc #' + i.__str__() + ' ' + c.__str__())
            list_of_lobbies.append((c.__str__(), 0))  # time.perf_counter()))

    def check_timers(self):
        print('reset timer called')
        i = 0
        for x in list_of_lobbies:
            print('123 ' + x.__str__())
            if 'stopped' in x.__str__():
                print('found stopped timer, reseting timer')
                list_of_lobbies[i] = (x.__str__().split(comma)[1], 0)
            i += 1

    def set_timer_on_lobby(self, lobby_id):
        i = 0
        for x in list_of_lobbies:
            if x.__str__().split(comma)[1] == lobby_id.__str__():
                t = Timer(cooldown_time, function=self.timer_ended)
                t.start()
                list_of_lobbies[i] = (x.__str__().split(comma)[1], t)
                # x = (x.__str__()[2:-5], t)
                print('lobby  ' + lobby_id.__str__() + ' set on 30 min cooldown ')
            i += 1

    def get_all_users_in_lobby(self, ctx, lobby_id):
        leader = ctx.author
        channel = self.bot.get_channel(leader.voice.channel.id)
        for member in list(channel.members):
            if member.id.__str__() not in cooldown_list.__str__():
                cooldown_list.append((member.id.__str__(), 0))

    def check_if_user_is_not_on_cooldown(self, ctx, lobby_id):
        leader = ctx.author
        channel = self.bot.get_channel(leader.voice.channel.id)
        print('user on cooldown method launched')
        for member in list(channel.members):
            i = 0
            for x in cooldown_list:
                if member.id.__str__() == cooldown_list[i].__str__().split(comma)[1]:
                    if 'started' in cooldown_list[i].__str__():
                        print('user '+member.__str__()+' is on cooldown. Returning False')
                        return False
                i += 1
        return True

    def check_users(self):
        print('reset user cooldown called')
        i = 0
        for x in cooldown_list:
            if 'stopped' in x.__str__():
                print('found stopped timer on user, reseting timer')
                cooldown_list[i] = (x.__str__().split(comma)[1], 0)
            i += 1

    def set_timer_on_users_in_lobby(self, ctx):
        leader = ctx.author
        channel = self.bot.get_channel(leader.voice.channel.id)
        i = 0
        print(list(channel.members).__str__())
        for x in cooldown_list:
            print('12312312313')
            if x.__str__().split(comma)[1] in list(channel.members).__str__():
                t = Timer(cooldown_time, function=self.timer_ended)
                t.start()
                cooldown_list[i] = (x.__str__().split(comma)[1], t)
            i += 1

    def clear_cooldown_list(self):
        if ', 0' in cooldown_list:
            cooldown_list.remove(', 0')
        elif 'stopped' in cooldown_list:
            cooldown_list.remove('stopped')

    @commands.command(pass_context=True, brief="Secret command. Only for admins")
    async def dd(self, ctx):
        if ctx.message.author.guild_permissions.administrator:
            await ctx.send('list of lobbies')
            for x in list_of_lobbies:
                await ctx.send(x)
            await ctx.send('list of users')
            for x in cooldown_list:
                await ctx.send(x)

    @commands.command(pass_context=True, brief="Gives random roles to people with no role")
    async def dd2(self, ctx):
        if ctx.message.author.guild_permissions.administrator:
            role1 = utils.get(ctx.message.guild.roles, id=755324676720427070)
            role2 = utils.get(ctx.message.guild.roles, id=755324708924162141)
            for member in ctx.guild.members:
                if len([i for i in member.roles]) == 1:
                    r = random.randint(1, 100)
                    if r > 50:
                        #await ctx.send(r)
                        await member.add_roles(role1)
                    elif r < 50:
                        #await ctx.send(r)
                        await member.add_roles(role2)
                    await ctx.send('user'+member.__str__()+' has been given random role')
                else:
                    await ctx.send('user '+member.__str__()+' has too many roles:   '+len([i for i in member.roles]).__str__())

    def timer_ended(self):
        pass


def setup(bot):
    bot.add_cog(Among(bot))
