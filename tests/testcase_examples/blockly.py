# coding: utf-8
import os
import atx


__basename = os.path.basename(os.path.splitext(__file__)[0])
d = atx.connect(platform="android")
d.image_path = [".", "images", os.path.join("images", __basename)]

d.screenshot('screen.png')
if 0 == 0:
  print('你好')
  for count in range(1):
    print('Hello world')
print('Hello world')