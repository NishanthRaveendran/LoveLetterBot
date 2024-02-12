import discord
from discord import File
from discord.ext import commands
import random
import string
import asyncio
from player import Player
from game import Game


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

love_letter_channel_id = None
active = False
lobby = []
channels = []
deck = [8, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 1, 1, 1]


@bot.event
async def on_ready():
  print('We have logged in as {0.user}'.format(bot))

@bot.event
async def on_guild_join(guild):
  global love_letter_channel_id
  # This function is called when the bot joins a new server
  channel_name = "love-letter"
  # Check if the channel already exists; if not, create it
  existing_channel = discord.utils.get(guild.text_channels, name=channel_name)

  if existing_channel is None:
    # Create the text channel with bot-only permissions
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        bot.user: discord.PermissionOverwrite(send_messages=True)
    }
    new_channel = await guild.create_text_channel(channel_name,
                                                  overwrites=overwrites)
    love_letter_channel_id = new_channel.id 
    print(f"Bot-welcome channel '{channel_name}' created in {guild.name}!")

    await new_channel.send("Love Letter Bot is here! Wagwan fam :P")
    await new_channel.send("Type !ll to join the lobby.")
    await new_channel.send("Type !start to start the game. You need 3 or 4 players in the lobby to start a game.")
    await new_channel.send("Type !clear to clear the lobby.")
    await new_channel.send("If you delete this channel, type !loveletter in any text channel to reset.")

@bot.command(name='loveletter')
async def channel(ctx):
  guild = ctx.guild
  global love_letter_channel_id
  # This function is called when the bot joins a new server
  channel_name = "love-letter"
  # Check if the channel already exists; if not, create it
  existing_channel = discord.utils.get(guild.text_channels, name=channel_name)

  if existing_channel is None:
    # Create the text channel with bot-only permissions
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        bot.user: discord.PermissionOverwrite(send_messages=True)
    }
    new_channel = await guild.create_text_channel(channel_name,
                                                  overwrites=overwrites)
    love_letter_channel_id = new_channel.id 
    print(f"Bot-welcome channel '{channel_name}' created in {guild.name}!")

    await new_channel.send("Love Letter Bot is here! Wagwan fam :P")
    await new_channel.send("Type !ll to join the lobby.")
    await new_channel.send("Type !start to start the game. You need 3 or 4 players in the lobby to start a game.")
    await new_channel.send("Type !clear to clear the lobby.")

@bot.command(name='ll')
async def play(ctx):
    if ctx.channel.name != "love-letter":
      await ctx.send("This command can only be used in the 'love-letter' channel.")
      return
    # Custom logic to handle joining the lobby
    if len(lobby) == 4:
      await ctx.send('Game in progress. Wait')
    elif ctx.author.name in lobby:
      await ctx.send('You are already in the lobby')
    else:
      lobby.append(ctx.author.name)
      await ctx.send('You have been added to the lobby')
      await ctx.send(f'Current lobby: {lobby}')
      if len(lobby) == 4: 
        await ctx.send('Lobby full, start game with !start')

@bot.command(name='clear')
async def clear(ctx):
    if ctx.channel.name != "love-letter":
      await ctx.send("This command can only be used in the 'love-letter' channel.")
      return
      
    if lobby:
      lobby.clear()
      await ctx.send('Lobby cleared')
    else:
      await ctx.send('Lobby is empty')

@bot.command(name='start')
async def start(ctx):
    if ctx.channel.name != "love-letter":
      await ctx.send("This command can only be used in the 'love-letter' channel.")
      return
  
    global active
  
    if len(lobby) < 2:
      await ctx.send('Not enough players in lobby')
    elif active:
      await ctx.send("Game already active")
    else:   
      # Create a new text channel
      active = True
      channels.clear()
      code = ''.join(random.choices(string.ascii_letters, k=3))
      category = await ctx.guild.create_category(f'Love Letter - {code}')

      for player_name in lobby:
        # Create a private channel for each player
        new_channel = await ctx.guild.create_text_channel(f"{code}-{player_name}", category=category)

        # Set specific permissions for the channel
        await new_channel.set_permissions(ctx.guild.default_role, read_messages=False)
        await new_channel.set_permissions(ctx.guild.me, read_messages=True)
        await new_channel.set_permissions(ctx.guild.get_member_named(player_name), read_messages=True, send_messages=True)

        channels.append(new_channel)
        await ctx.send(f"Private channel created for {player_name}: {new_channel.mention}")

      await ctx.send("The game has started in the new private channels!")
  
      game = Game(bot, channels, lobby, code)
      await game.start_game()
      await game.end_game(ctx, code)
      active = False
      await asyncio.sleep(60)

      print("deleting channels")
      for channel in category.channels:
        await channel.delete()
      await category.delete()

#partybot
#bot.run('MTE2OTc1MDk4Mjc3OTk5ODMwOQ.GrqNb2.NBZ3kLYAFvUsZ605JNqDxYC3U3BqxxtmHw6URM')

#love-letter-bot
bot.run('MTE3Njk0MzAxOTM2MzE1NjAyOQ.GmrC_z.hr8KjKVKOZgp3Gsbv3JajSMOnuDNQ6RlPCm0RE')
