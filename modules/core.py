import typing
import logging

import discord
from discord.ext import commands
from tinydb import Query

Servers = Query()

def list_append(key, element):
    def transform(doc):
        doc[key].append(element)
    return transform

def guild_in_db():
    async def predicate(ctx):
        try:
            if not ctx.bot.db.contains(Servers.id == ctx.guild.id):
                ctx.bot.db.insert({'id': ctx.guild.id, 'requestChannel': None, 'roles': []})
                logging.info(f'[Bot] Guild initalized to database: {ctx.guild} ({ctx.guild.id})')
            return True
        except:
            return False
    return commands.check(predicate)

class RoleRequest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='list', invoke_without_command=True, case_insensitive=True)
    @commands.guild_only()
    async def _list(self, ctx):
        '''Lists all requestable roles'''
        return await ctx.send('LIST') # TODO

    @_list.command(name='all')
    @commands.has_guild_permissions(manage_roles=True)
    async def _list_all(self, ctx):
        '''Lists all roles in the server'''
        return await ctx.send('LIST ALL') # TODO

    @_list.command(name='colors', aliases=['color', 'colour', 'colours'])
    async def _list_colors(self, ctx):
        '''Shows an image of requestable colored roles'''
        return await ctx.send('LIST COLORS') # TODO


    @commands.command(name='join')
    @commands.guild_only()
    async def _join(self, ctx, role: discord.Role):
        '''
        Joins or requests a requestable roles
        
        If the role is a public role, it will be joined. If the role is a restricted role, a request is submitted.
        '''
        return await ctx.send('JOIN') # TODO

    @commands.command(name='leave')
    @commands.guild_only()
    async def _leave(self, ctx, role: discord.Role):
        '''Leaves or cancels a request for a requestable role'''
        return await ctx.send('LEAVE') # TODO


    @commands.group(name='request', invoke_without_command=True, case_insensitive=True)
    @commands.guild_only()
    async def _request(self, ctx):
        '''
        Manages restricted role requests
        
        To make or cancel your own role request, use the 'join' or 'leave' commands.
        '''
        return await ctx.send_help('request')

    @_request.command(name='channel')
    @commands.has_guild_permissions(manage_roles=True)
    async def _request_channel(self, ctx, channel: typing.Optional[discord.TextChannel]):
        '''Sets the channel that requests will be posted in'''
        return await ctx.send('REQUEST CHANNEL') # TODO

    @_request.command(name='approve')
    async def _request_approve(self, ctx, id: str):
        '''Approves a restricted role requests'''
        # check if can read channel
        return await ctx.send('REQUEST APPROVE') # TODO

    @_request.command(name='deny')
    async def _request_deny(self, ctx, id: str):
        '''Denies a restricted role requests'''
        # check if can read channel
        return await ctx.send('REQUEST DENY') # TODO


    @commands.group(name='roles', invoke_without_command=True, case_insensitive=True, aliases=['role'])
    @commands.guild_only()
    async def _role(self, ctx):
        '''
        Manages the server's requestable roles
        
        To see a list of roles, use the 'list' command.
        '''
        return await ctx.send_help('roles')

    @_role.command(name='add', usage='<role> [public|restricted|p|r]')
    @commands.has_guild_permissions(manage_roles=True)
    @guild_in_db()
    async def _role_add(self, ctx, role: discord.Role, type: typing.Optional[str] = 'public'):
        '''
        Adds a role to the requestable roles
        '''
        Roles = Query()
        types = {
            'public': 'public',
            'restricted': 'restricted',
            'restrict': 'restricted',
            'p': 'public',
            'r': 'restricted'
        }

        if self.bot.db.contains((Servers.id == ctx.guild.id) & (Servers.roles.any(Roles.id == role.id))):
           raise commands.errors.BadArgument(f'{role.name} is already a requestable role.') 

        if not type.lower() in types:
            commands.errors.BadArgument(f'{type} is not a valid type.') 

        self.bot.db.update(list_append('roles', {'id': role.id, 'type': types[type]}), Servers.id == ctx.guild.id)
        await ctx.send(f':white_check_mark: {role.name} added as a requestable {types[type]} role.')
         
        # return await ctx.send('ROLE ADD') # TODO

    @_role.command(name='remove')
    @commands.has_guild_permissions(manage_roles=True)
    @guild_in_db()
    async def _role_remove(self, ctx, role: discord.Role):
        '''Removes role from the requestable roles'''
        return await ctx.send('ROLE REMOVE') # TODO

    @_role.command(name='restict')
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_restict(self, ctx, role: discord.Role):
        '''Makes a public role restricted'''
        return await ctx.send('ROLE RESTRICT') # TODO

    @_role.command(name='public', aliases=['unrestrict'])
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_public(self, ctx, role: discord.Role):
        '''Makes a restricted role public'''
        return await ctx.send('ROLE PUBLIC') # TODO


def setup(bot):
    bot.add_cog(RoleRequest(bot))
    logging.info('[Extension] Core module loaded')

def teardown(bot):
    bot.remove_cog('RoleRequest')
    logging.info('[Extension] Core module unloaded')