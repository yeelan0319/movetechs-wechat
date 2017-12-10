from enum import Enum

class MsgType(Enum):
  text = 1
  image = 2
  voice = 3
  video = 4
  location = 5
  link = 6
  shortvideo = 7
