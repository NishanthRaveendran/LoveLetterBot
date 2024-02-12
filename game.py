import discord
from discord import File
from discord.ext import commands
import random
import string
from player import Player
import asyncio

class Game:
  def __init__(self, bot, channels, lobby, code):
      self.bot = bot
      self.channels = channels
      self.code = code
      deck = [8, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 1, 1, 1]
      random.shuffle(deck)

      self.deck = deck
      self.burn = deck.pop()
      self.active = len(lobby)
      self.players = []

      for i in range(len(lobby)):
        self.players.append(Player(lobby[i], channels[i], deck.pop()))
      random.shuffle(self.players)

  
  # Handles player turns and determines when game is over
  async def start_game(self):
      await self.send_all("The game is starting! Shuffling deck...")
      await self.send_line()
      translate = ["nil", "GUARD", "PRIEST", "BARON", "HANDMAID", "PRINCE", "KING", "COUNTESS", "PRINCESS"]

      try:
        for p in self.players:
          if p != self.players[0]:
            card_img = self.img_card(p.card)
            await p.channel.send(f"You have drawn a {translate[p.card]}", file=card_img)

        await self.send_line()
        turn = 0
        #while there are multiple active players and there are cards left in the deck
        while self.active > 1 and self.deck:
          player = self.players[turn]

          #check if player is dead or not
          if player.isDead:
              turn = (turn + 1) % len(self.players)
              continue

          await self.send_all(f"It's {player.name}'s turn")

          #check if player is protected, toggle off if true
          if player.isProtected:
              player.protect()
              await self.send_all(f"{player.name}'s protection has worn off")


          cards = [self.deck.pop(), player.card]
          await player.channel.send(f"You have (1){translate[cards[0]]} and (2){translate[cards[1]]}", files=[self.img_card(cards[0]), self.img_card(cards[1])])

          #Countess + Prince/King check
          if 7 in cards and (6 in cards or 5 in cards):
              turn = (turn + 1) % len(self.players)
              await player.channel.send("You have no choice but to discard the COUNTESS. Type 1 to continue")
              response = await self.wait_for_player_response(player)
              if response is None:
                  await self.send_all(f"{player.name} took too long. Aborting the game.")
                  return

              await player.channel.send(f"You have a COUNTESS and a PRINCE/KING so you must discard the COUNTESS")
              await self.send_allf(f"{player.name} played COUNTESS", 7)
              player.card = cards[0 if cards[1] == 7 else 1]
              continue

          #prompt player to discard one of their cards
          await player.channel.send(f"Pick a card to play? (1 or 2)")
          good = False
          while not good:
              response = await self.wait_for_player_response(player)
              if response is None:
                  await self.send_all(f"{player.name} took too long. Aborting the game.")
                  return
              if self.valid_response(response, 1, 2):
                  good = True
                  response = int(response)
              else:
                  await player.channel.send("Invalid. Please enter 1 or 2.")


          await self.send_allf(f"{player.name} played {translate[cards[response - 1]]}", cards[response - 1])
          player.card = cards[response % 2]
          valid = await self.card_action(player, cards[response-1])
          if not valid:
            await self.send_all(f"{player.name} took too long. Aborting the game.")
            return

          await self.send_line()
          turn = (turn + 1) % len(self.players)
          
      except Exception as e:
          print(f"An exception occurred: {e}")
          await self.send_all("Game Aborted")

  

  def img_card(self, card):
    card_image_path = f"card_imgs/{card}.png"
    card_image = File(card_image_path, filename=f"{card}.png")
    return card_image

  async def send_all(self, message):
      for channel in self.channels: 
          await channel.send(message)

  async def send_allf(self, message, card):
      for channel in self.channels: 
          await channel.send(message, file=self.img_card(card))

  async def send_line(self):
      for channel in self.channels:
          await channel.send("-------------------")

  def valid_response(self, message, l, r):
      if message.isdigit() and int(message) >= l and int(message) <= r:
          return True
      else:
          return False

  #kills player
  def kill(self, player):
      player.isDead = True
      player.card = 0
      self.active -= 1

  #prompts player to respond
  async def wait_for_player_response(self, player):
      def check(message):
          return message.author.name == player.name
      try:
          # Wait for a message from the specified player in the channel
          response = await self.bot.wait_for('message', check=check, timeout=60)
          return response.content
      except asyncio.TimeoutError:
          await self.send_all(f"bruh where's {player.name} at")
          return None

  # ends game
  async def end_game(self, ctx, code):
    await self.send_line()

    if self.active == 1:
      for p in self.players:
        if not p.isDead:
          await self.send_all(f"{p.name} is the only player alive.")
          await self.send_all(f"{p.name} wins!")
    elif self.deck:
      await self.send_all("Game ending...")
      await ctx.send(f"Love Letter - {code} Game aborted")
    else:
      await self.send_all("There are no more cards left in the deck. Highest card wins")
      winner = self.players[0]
      high_card = self.players[0].card
      for p in self.players:
        if p.card > 0:
          await self.send_allf(f"{p.name} has a {translate[p.card]}", p.card)
          await self.send_line()
        if p.card > high_card:
          high_card = p.card
          winner = p
      await self.send_all(f"{winner.name} wins!")
    await self.send_all("GAME OVER!")
    await self.send_line()
    await self.send_all("Channels will be deleted in 60 seconds")

  
  # provides player options for card actions
  async def player_choice(self, player, prince):
    players = []
    for p in self.players:
      if prince or p != player:
        players.append(p)

    options = []
    options_message = ""
    for i in range(len(players)):
      if players[i].isDead:
        #await player.channel.send(f"X: {players[i].name} (DEAD)")
        options_message += f"X: {players[i].name} (DEAD)\n"
      elif players[i].isProtected:
        #await player.channel.send(f"X: {players[i].name} (PROTECTED)")
        options_message += f"X: {players[i].name} (PROTECTED)\n"
      else:
        options.append(players[i])
        #await player.channel.send(f"{len(options)}: {players[i].name}")
        options_message += f"{len(options)}: {players[i].name}\n"

    await player.channel.send(options_message)
    
    if len(options) == 0:
        await self.send_all("No players to perform action. Discarding card...")
        return None
    elif len(options) == 1:
        await player.channel.send(f"Only one player to pick from, picking {options[0].name}...")
        return options[0]
    else:
        await player.channel.send(f"Pick a player to use card effect on (1-{len(options)})")
        good = False
        while not good:
            response = await self.wait_for_player_response(player)
            if response is None:
              await self.send_all(f"{player.name} took too long. Aborting the game.")
              return "broken"
            if self.valid_response(response, 1, len(options)):
              response = int(response)
              if options[response-1].isDead or options[response-1].isProtected:
                await player.channel.send("That player is dead or protected. Please pick another player.")
              else:
                good = True
                await player.channel.send(f"You picked {options[response-1].name}")
                return options[response-1]
            else:
              await player.channel.send(f"Invalid. Please enter a number between 1 and {len(options)}")
  
  #
  #  Card Action for each card
  #
  async def card_action(self, player, card):
    translate = ["nil", "GUARD", "PRIEST", "BARON", "HANDMAID", "PRINCE", "KING", "COUNTESS", "PRINCESS"]
    if card == 1:
      enemy = await self.player_choice(player, False)
      if enemy == "broken":
        await self.send_all(f"{player.name} took too long. Aborting the game.")
        return False
      if enemy:    
        guard_options_message = ""
        for i in range(1, 8):
          #await player.channel.send(f"{i+1}: {translate[i+1]}")
          guard_options_message += f"{i+1}: {translate[i+1]}\n"
          
        await player.channel.send(guard_options_message)
        await player.channel.send(f"Pick a card to guess (2-8)")
        good = False
        while not good:
          response = await self.wait_for_player_response(player)
          if response is None:
            return None
          if self.valid_response(response, 2, 8):
            good = True
            response = int(response)
            await self.send_all(f"{player.name} guessed that {enemy.name} has a {translate[response]}")
            if int(response) != enemy.card:
              await self.send_all(f"{enemy.name} does NOT have a {translate[response]}")
            else:
              await self.send_allf(f"{enemy.name} DOES have a {translate[response]}. {enemy.name} is DEAD", enemy.card)
              self.kill(enemy)
          else:
            await player.channel.send(f"Invalid. Please enter a number between 2 and 8")

      return True

    elif card == 2:
      enemy = await self.player_choice(player, False)
      if enemy == "broken":
        await self.send_all(f"{player.name} took too long. Aborting the game.")
        return False
      if enemy:
        await self.send_all(f"{player.name} is looking at {enemy.name}'s card")
        await player.channel.send(f"{enemy.name} has a {translate[enemy.card]}", file=self.img_card(enemy.card))

      return True

    elif card == 3:
      enemy = await self.player_choice(player, False)
      if enemy == "broken":
        await self.send_all(f"{player.name} took too long. Aborting the game.")
        return False
      if enemy:
        await player.channel.send(f"You have a {player.card}-{translate[player.card]} and {enemy.name} has a {enemy.card}-{translate[enemy.card]}", files=[self.img_card(player.card), self.img_card(enemy.card)])
        await enemy.channel.send(f"{player.name} have a {player.card}-{translate[player.card]} and you have a {enemy.card}-{translate[enemy.card]}", files=[self.img_card(player.card), self.img_card(enemy.card)])

        if enemy.card > player.card:
          await self.send_allf(f"{player.name} is DEAD. They had a {translate[player.card]}", player.card)
          self.kill(player)
        elif enemy.card < player.card:
          await self.send_allf(f"{enemy.name} is DEAD. They had a {translate[enemy.card]}", enemy.card)
          self.kill(enemy)
        else:
          await self.send_all("No one died...")

      return True

    elif card == 4:
      player.protect()
      await self.send_all(f"{player.name} is protected for the round")
      return True

    elif card == 5:
      enemy = await self.player_choice(player, True)
      if enemy == "broken":
        await self.send_all(f"{player.name} took too long. Aborting the game.")
        return False
      if enemy:
        await self.send_all(f"{player.name} is forcing {enemy.name} to discard")
        await self.send_allf(f"{enemy.name} discards a {translate[enemy.card]}", enemy.card)
        if enemy.card == 8:
          await self.send_all(f"{enemy.name} is DEAD")
          await self.kill(enemy)
        elif not self.deck:
          enemy.card = self.burn
        else:
          enemy.card = self.deck.pop()
        await self.send_all(f"{enemy.name} has picked up a new card")
        await enemy.channel.send(f"You have picked up a {translate[enemy.card]}", file=self.img_card(enemy.card))

      return True

    elif card == 6:
      enemy = await self.player_choice(player, False)
      if enemy == "broken":
        await self.send_all(f"{player.name} took too long. Aborting the game.")
        return False
      if enemy:
        await self.send_all(f"{player.name} is swapping cards with {enemy.name}")
        player.card, enemy.card = enemy.card, player.card
        await player.channel.send(f"You now have a {translate[player.card]} and {enemy.name} has your {translate[enemy.card]}", files=[self.img_card(player.card), self.img_card(enemy.card)])
        await enemy.channel.send(f"You now have a {translate[enemy.card]} and {player.name} has your {translate[player.card]}", files=[self.img_card(enemy.card), self.img_card(player.card)])

      return True

    #if 7, continue

    elif card == 8:
      await self.send_all(f"{player.name} is dead, lol")
      await self.kill(player)
      return True
