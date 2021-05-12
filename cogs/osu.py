import aiohttp
from discord.ext import commands
import json
import os

# Path to data.json file
cwd = os.path.dirname(os.path.abspath("data.json"))
json_file_path = '%s/%s' % (cwd, 'data.json')
data_props = {}

try:
    with open(json_file_path) as data_file:
        data_props = json.load(data_file)
except IOError as e:
    print('Exception while trying to open json file: ' + e.__str__())

osu_api_key = data_props['osu_api_key']


class Osu(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def use_api(self, ctx, url):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as channel:
                    res = await channel.json()
                    return res
            except Exception:
                await ctx.send('Invalid URL parse :wheelchair:')
                return

    async def parse_match(self, ctx, games, column):
        plist = {}
        for game in games:
            try:
                del game['play_mode']
            except:
                pass
            try:
                del game['match_type']
            except:
                pass
            try:
                del game['team_type']
            except:
                pass
            try:
                del game['start_time']
                del game['end_time']
                del game['scoring_type']
            except:
                pass
            scoresum = 0
            game['newscores'] = []
            game['playercount'] = 0
            for score in game['scores']:
                g = dict()

                g['user_id'] = score['user_id']
                plist[g['user_id']] = 0
                g['score'] = score['score']
                g['maxcombo'] = score['maxcombo']
                g['enabled_mods'] = score['enabled_mods']
                scoresum += int(score['score'])
                game['playercount'] += 1
                game['newscores'].append(g)

            game['scoresum'] = scoresum

        player_number = 0
        text_string = ''
        print('started parsing match scores')
        for player in plist:
            player_number = player_number + 1
            map_number = 0
            player_username = await self.get_username(ctx, player)
            text_string += (player_number.__str__() + '. ' + player_username + ': ')
            if column:
                text_string += '\n'
            for game in games:
                map_number = map_number + 1
                for score in game['scores']:
                    if player == score['user_id']:
                        text_string += score['score'] + ' '
                        if column:
                            text_string += '\n'
            print('player ' + player_number.__str__() + ' finished')
            text_string += '\n'

        return text_string

    async def get_username(self, ctx, player_id):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                        "https://osu.ppy.sh/api/get_user?u=" + player_id + "&k=" + osu_api_key) as channel:
                    res = await channel.json()
                    return res[0]['username']
            except Exception:
                await ctx.send('get username error')
                return

    @commands.command(pass_context=True, brief="Parses osu! multi match and gets all scores for each player in order")
    async def ms(self, ctx, url):
        print('.ms ' + url.__str__() + ' requested by ' + ctx.author.name.__str__())
        if 'https://osu.ppy.sh/community/matches' in url:
            try:
                url = url.split("matches/")
            except:
                await ctx.send('Invalid URL :wheelchair:')
                return
            url = url[1]
            print('fgdsgdsg' + url)
            res = await self.use_api(ctx, "https://osu.ppy.sh/api/get_match?k=" + osu_api_key + "&mp=" + url)
            message = await self.parse_match(ctx, res['games'], False)
            await ctx.send(message)

    @commands.command(pass_context=True, brief="Same as .ms but in column")
    async def msc(self, ctx, url):
        print('.ms ' + url.__str__() + ' requested by ' + ctx.author.name.__str__())
        if 'https://osu.ppy.sh/community/matches' in url:
            try:
                url = url.split("matches/")
            except:
                await ctx.send('Invalid URL :wheelchair:')
                return
            url = url[1]
            print('fgdsgdsg' + url)
            res = await self.use_api(ctx, "https://osu.ppy.sh/api/get_match?k=" + osu_api_key + "&mp=" + url)
            message = await self.parse_match(ctx, res['games'], True)
            await ctx.send(message)


def setup(bot):
    bot.add_cog(Osu(bot))
