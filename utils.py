import io
import logging
import re
import subprocess

import dict_deep
import discord
from discord.ext import commands
from tinydb import Query

import config

Servers = Query()

async def cmdSuccess(ctx, text, *, delete_after = None):
    return await ctx.send(f'{config.greenTick} {text}', delete_after = delete_after)

async def cmdFail(ctx, text, *, delete_after = None):
    return await ctx.send(f'{config.redTick} {text}', delete_after = delete_after)

def getGitInfo(ref_commit = None):
    GIT_REPO_URL = 'https://github.com/7bitlyrus/rolerequest'
    GIT_COMMIT_BASE = GIT_REPO_URL + '/commit/'
    GIT_COMPARE_BASE = GIT_REPO_URL + '/compare/'
    GIT_REPO_REGEX = r'(?:https?://)?(?:\w+@)?([^:/\s]+)[:|/]([^/\s]+)/([^/.\s]+)(?:.git)?'

    try:
        commit_hash = subprocess.check_output(['git','rev-parse','HEAD']).decode('ascii').strip()
        origin_url = subprocess.check_output(['git','config','--get','remote.origin.url']).decode('ascii').strip()
        modified = subprocess.call(['git','diff-index','--quiet','HEAD']) != 0
    except Exception as e:
        logging.warn(e)
        return False

    if ref_commit is None: # We are initing commit info on bot startup, we only want the commit hash
        return commit_hash

    fork = re.match(GIT_REPO_REGEX, GIT_REPO_URL).groups() != re.match(GIT_REPO_REGEX, origin_url).groups()
    multiple = ref_commit != commit_hash

    commit_short = (f'{ref_commit[:7]}..' if multiple else '') + commit_hash[:7] + ('*' if modified else '')
    commit_url = f'{GIT_COMPARE_BASE}{ref_commit}^...{commit_hash}' if multiple else f'{GIT_COMMIT_BASE}{commit_hash}'
    s = 's' if multiple else ''

    version = f'Commit{s} `{commit_short}` (Fork)' if fork else f'Commit{s} [`{commit_short}`]({commit_url})'

    return version

def guild_in_db():
    async def predicate(ctx):
        if not ctx.bot.db.contains(Servers.id == ctx.guild.id):
            default_document = {
                'id': ctx.guild.id, 
                'requests_opts': {
                    'channel': None,
                    'hidejoins': False
                }, 
                'requests': {},
                'roles': {}
            }

            ctx.bot.db.insert(default_document)
            logging.info(f'[Bot] Guild initalized to database: {ctx.guild} ({ctx.guild.id})')
        return True
    return commands.check(predicate)

def getGuildDoc(bot, guild):
    return bot.db.get( Servers.id == guild.id )

def guildKeySet(bot, guild, key, val):
    def predicate(key, val):
        def transform(doc):
            dict_deep.deep_set(doc, key, val)
        return transform

    return bot.db.update(predicate(key, val), Servers.id == guild.id)

def guildKeyDel(bot, guild, key):
    def predicate(key):
        def transform(doc):
            dict_deep.deep_del(doc, key)
        return transform

    return bot.db.update(predicate(key), Servers.id == guild.id)

async def sendListEmbed(ctx, title, lst, *, raw_override=None, footer=None):
    # Overall - 128 - footer - title, description, field values
    footer_len = 0 if not footer else len(footer)
    LEN_LIMITS = (6000 - 128 - len(title) - footer_len, 2048, 1024) 

    lengths = list(map(lambda x: len(x), lst))

    lenOverall = 0
    lastItem = None

    # Start building with description
    description = ''
    for i in range(len(lst)):
        # Description < Overall, so we won't have to worry about hitting it yet; + 1 for newline
        if len(description) + lengths[i] + 1 > LEN_LIMITS[1]: break 

        description += lst[i] + '\n'
        lastItem = i

    lenOverall += len(description)

    # If description is full, start with fields
    fields = []
    for f in range(24): # 24 Fields, reserve last one for maximum length link
        if lastItem + 1 == len(lst): break
        if lenOverall + lengths[lastItem+1] + 1 > LEN_LIMITS[0]: break

        fields.append('')
        for i in range(lastItem+1, len(lst)):
            if lenOverall + len(fields[f]) + lengths[i] + 1 > LEN_LIMITS[0]: break
            if len(fields[f]) + lengths[i] + 1 > LEN_LIMITS[2]: break

            fields[f] += lst[i] + '\n'
            lastItem = i

        lenOverall += len(fields[f])

    # If its still too large, send the 'raw' list as a file.
    if lastItem + 1 < len(lst):
        fields.append(f'Showing {lastItem+1} items.')
        raw = '\r\n'.join(lst) if not raw_override else raw_override
        file = discord.File(fp=io.BytesIO(str.encode(raw)), filename='list.txt')
    else:
        file = None

    # Create the embed object (finally)
    embed = discord.Embed(title=title, description=description)
    if footer: embed.set_footer(text=footer)
    for field in fields:
        embed.add_field(name='\uFEFF', value=field, inline=False) # \uFEFF = ZERO WIDTH NO-BREAK SPACE

    message = await ctx.send(embed=embed, file=file)

    # Update the message embed with the file url
    if file: 
        url = message.attachments[0].url
        newValue = fields[len(fields)-1] + f' [See all {len(lst)}.]({url})'

        embed.remove_field(len(fields)-1)
        embed.add_field(name='\uFEFF', value=newValue, inline=False)

        return await message.edit(embed=embed)
    else:
        return message