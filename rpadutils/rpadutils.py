import re

import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound

from cogs.utils.chat_formatting import *

from .utils.padguide_api import *


class RpadUtils:
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    print('rpadutils setup')
    n = RpadUtils(bot)
    bot.add_cog(n)

# TZ used for PAD NA
# NA_TZ_OBJ = pytz.timezone('America/Los_Angeles')
NA_TZ_OBJ = pytz.timezone('US/Pacific')

# TZ used for PAD JP
JP_TZ_OBJ = pytz.timezone('Asia/Tokyo')


# https://gist.github.com/ryanmcgrath/982242
# UNICODE RANGE : DESCRIPTION
# 3000-303F : punctuation
# 3040-309F : hiragana
# 30A0-30FF : katakana
# FF00-FFEF : Full-width roman + half-width katakana
# 4E00-9FAF : Common and uncommon kanji
#
# Non-Japanese punctuation/formatting characters commonly used in Japanese text
# 2605-2606 : Stars
# 2190-2195 : Arrows
# u203B     : Weird asterisk thing

JP_REGEX_STR = r'[\u3000-\u303F]|[\u3040-\u309F]|[\u30A0-\u30FF]|[\uFF00-\uFFEF]|[\u4E00-\u9FAF]|[\u2605-\u2606]|[\u2190-\u2195]|\u203B';
JP_REGEX = re.compile(JP_REGEX_STR)

def containsJp(txt):
    return JP_REGEX.search(txt)


class PermissionsError(CommandNotFound):
    """
    Base exception for all others in this module
    """


class BadCommand(PermissionsError):
    """
    Thrown when we can't decipher a command from string into a command object.
    """
    pass


class RoleNotFound(PermissionsError):
    """
    Thrown when we can't get a valid role from a list and given name
    """
    pass


class SpaceNotation(BadCommand):
    """
    Throw when, with some certainty, we can say that a command was space
        notated, which would only occur when some idiot...fishy...tries to
        surround a command in quotes.
    """
    pass

def get_role(roles, role_string):
    if role_string.lower() == "everyone":
        role_string = "@everyone"

    role = discord.utils.find(
        lambda r: r.name.lower() == role_string.lower(), roles)

    if role is None:
        raise RoleNotFound(roles[0].server, role_string)

    return role

def get_role_from_id(bot, server, roleid):
    try:
        roles = server.roles
    except AttributeError:
        server = get_server_from_id(bot, server)
        try:
            roles = server.roles
        except AttributeError:
            raise RoleNotFound(server, roleid)

    role = discord.utils.get(roles, id=roleid)
    if role is None:
        raise RoleNotFound(server, roleid)
    return role

def get_server_from_id(bot, serverid):
    return discord.utils.get(bot.servers, id=serverid)

def normalizeServer(server):
    server = server.upper()
    return 'NA' if server == 'US' else server

cache_folder = 'data/padevents'

def shouldDownload(file_path, expiry_secs):
    if not os.path.exists(file_path):
        print("file does not exist, downloading " + file_path)
        return True

    ftime = os.path.getmtime(file_path)
    file_age = time.time() - ftime
    print("for " + file_path + " got " + str(ftime) + ", age " + str(file_age) + " against expiry of " + str(expiry_secs))

    if file_age > expiry_secs:
        print("file too old, download it")
        return True
    else:
        return False

def writeJsonFile(file_path, js_data):
    with open(file_path, "w") as f:
        json.dump(js_data, f, sort_keys=True, indent=4)

def readJsonFile(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def makeCachedPadguideRequest(time_ms, endpoint, expiry_secs):
    file_path = cache_folder + '/' + endpoint
    if shouldDownload(file_path, expiry_secs):
        resp = makePadguideTsRequest(time_ms, endpoint)
        writeJsonFile(file_path, resp)
    return readJsonFile(file_path)


def writePlainFile(file_path, text_data):
    with open(file_path, "wt", encoding='utf-8') as f:
        f.write(text_data)

def readPlainFile(file_path):
    with open(file_path, "r", encoding='utf-8') as f:
        return f.read()

def makePlainRequest(file_url):
    response = urllib.request.urlopen(file_url)
    data = response.read()  # a `bytes` object
    return data.decode('utf-8')

def makeCachedPlainRequest(file_name, file_url, expiry_secs):
    file_path = cache_folder + '/' + file_name
    if shouldDownload(file_path, expiry_secs):
        resp = makePlainRequest(file_url)
        writePlainFile(file_path, resp)
    return readPlainFile(file_path)

async def boxPagifySay(say_fn, msg):
    for page in pagify(msg, delims=["\n"]):
        await say_fn(box(page))
