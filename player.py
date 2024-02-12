class Player:
  def __init__(self, name, channel, card):
      self.name = name
      self.channel = channel
      self.isDead = False
      self.card = card
      self.isProtected = False

  def __str__(self):
    return self.name
    
  def draw(self, card):
    self.card = card

  def protect(self):
    #toggle protection
    if self.isProtected:
      self.isProtected = False
    else:
      self.isProtected = True

