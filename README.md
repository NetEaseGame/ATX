# AirtestX (中文版)
[![Build Status](https://travis-ci.org/codeskyblue/airtestx.svg?branch=master)](https://travis-ci.org/codeskyblue/airtestx)
[![Documentation Status](https://readthedocs.org/projects/airtestx/badge/?version=latest)](http://airtest.readthedocs.org/en/latest/?badge=latest)


改版自一个老项目 <https://github.com/netease/airtest>

该项目是为了让手机应用的一些常规测试可以自动化起来，让测试人员摆脱那些枯燥的重复性工作。基于OpenCV的图像识别技术，虽然有点类似于Sikuli, 但其实很多都不一样

# 代码重构中（不要着急）
airtest已经有人用，这次重构，估计好多api都会变了。最好的办法还是重建一个项目比较好，感谢<https://github.com/pactera>给起的名字 AirtestX

## 为什么要重构
很多的代码不符合pytohn编码规范, 还有一些很冗余的功能夹杂在里面，很不好维护。
为了能够重现该软件昔日的光芒，是时候擦亮代码，重出江湖了。

## Contribute
如何才能让软件变的更好，这其中也一定需要你的参与才行，发现问题去在github提个issue, 一定会有相应的开发人员看到并处理的。
由于我平常使用该项目的概率并不怎么高，所有不少问题即使存在我也不会发现，请养成看到问题提Issue的习惯，所有的Issue我都会去处理的，即使当时处理不了，等技术成熟了，我还是会处理。

BTW: 有开发能力的也可以先跟开发者讨论下想贡献的内容，并提相应的PR由开发人员审核。

网易内部用户暂时请直接联系 hzsunshx

## 主要更新内容
* 截图方式从adb screencap转成使用uiautomator

## 依赖
1. python2.7
2. opencv2.4+
3. Android4.1+

## 安装
1. 首先安装opencv(`>=2.4 && <3.0`)到你的电脑上

	windows推荐直接通过pip安装, 根据你是win32还是amd64选择合适的版本

	**win32**
	
	```
	pip install https://github.com/NetEase/aircv/releases/download/cv2binary/opencv_python-2.4.12-cp27-none-win32.whl
	```

	**amd64**

	```
	pip install https://github.com/NetEase/aircv/releases/download/cv2binary/opencv_python-2.4.12-cp27-none-win_amd64.whl
	```

	如果是Macbook，安装方法要比想象中的简单，然而耗时也比想象中的要长, 先安装`brew`, 之后

	```
	brew install python
	brew install opencv
	```

2. 安装airtest

	为了编码的时候能少敲一点字母, pip中软件包的名字简化成了 atx

	```
	pip install --upgrade atx
	```

	For the develop version, (maybe not stable), Sync with github master code

	```
	 pip -i https://testpypi.python.org/pypi -U --pre atx
	 ```


3. 安装android依赖

	下载adb安装到电脑上，推荐下载地址 <http://adbshell.com/>

## 快速入门
1. 连接一台安卓手机 (4.1+)

	打开windows命令行，执行 `adb devices`, 请确保看到类似输出, 没有其他的错误

	```bash
	$ adb devices
	List of devices attached
	EP7333W7XB      device
	```

2. 创建一个python文件 `test.py`, 内容如下

	```python
	# coding: utf-8
	import atx

	d = atx.connect(None) # 如果多个手机连接电脑，则需要将None改成对应的设备号
	d.screenshot('screen.png') # 截图
	```

	运行 `python test.py`

3. 截图

	命令行运行 `python -matx`, 鼠标左键拖拽选择一个按钮或者图标, 按下`c`截图保存推出. (按下r重新刷新屏幕, q推出)
	_PS: 这里其实有个好的IDE截图的最好了，因为时间精力问题还没有做_

	截图后的文件另存为 `button.png`, `test.py` 最后增加一行 `d.touch_image('button.png')`

	重新运行 `python test.py`, 此时差不多可以看到代码可以点击那个按钮了

4. 更多

	可以使用的接口还有很多，请接着往下看


## 接口
### 连接设备
`connect(udid, **kwargs)`

对于安卓设备常见连接方法

```
connect(None)
connect(None, host='127.0.0.1', port=5037)
connect('EFSXA124') # specify serialno
```

目前没有别的设备

### 截图
`snapshot(filename)`

可以自动识别屏幕的旋转

Parameters

    Name | Type   | Description
---------|--------|------------
filename | string | **Optional** 保存的文件名

返回值

opencv image

### 点击图片(制作中)
`touch_image(img)`

img support two types string(file path) or TouchImage 

from airtest.types import TouchImage

Parameters

Name      | Type      | Description
----------|-----------|------------
img       |string     | 需要点击的图片

Example

```
touch_image('start.png')

# or (todo)
touch_image(TouchImage(file='start.png', offset=(0, 0)))
```

### 其他接口
本来想着用sphinx自动生成文档来着，没想到竟然学了几个小时没学会. 我先写一些常用的方法吧

```python
import atx


d = atx.connect(None)
package_name = 'com.example.game'
d.start_app(package_name)

d.sleep(5) # sleep 5s
d.shell('uptime') # not done yet.

# this is default
d.screenshot_method = atx.SCREENSHOT_METHOD_UIAUTOMATOR
# alternative
# d.screenshot_method = atx.SCREENSHOT_METHOD_MINICAP

# if image not show in 10s, ImageNotFoundError will raised
try:
	d.touch_image('button.png', timeout=10.0)
except atx.ImageNotFoundError:
	print('Image not found')

# watcher, trigger when screenshot is called
w = atx.Watcher()
w.on('enter-game.png', atx.Watcher.ACTION_TOUCH)
w.on('inside.png', atx.Watcher.ACTION_QUIT)
d.add_watcher(w)
d.watch_all()

# d.del_watcher(wid) # remove watcher

d.stop_app(package_name)
```

## 代码导读
`connect` 函数负责根据平台返回相应的类(AndroidDevice or IOSDevice)

图像识别依赖于另一个库 [aircv](https://github.com/netease/aircv), 虽然这个库还不怎么稳定，也还酬和能用吧

其他待补充

## 相关的项目
1. 基于opencv的图像识别库 <https://github.com/netease/aircv>
2. 感谢作者 <https://github.com/xiaocong> 提供的uiautomator的python封装，相关项目已经fork到了

	- <https://github.com/codeskyblue/android-uiautomator-server>
	- <https://github.com/codeskyblue/airtest-uiautomator>

## License
This project is under the MIT License. See the [LICENSE](LICENSE) file for the full license text.

## 历史文档 (below, 下面就不要看了)
Python lib for **android** app test. (Not for ios)

## 更新说明
### 0.10.0
经过慎重的考虑，airtest如果处理的事情太多的的话，整个库就不能很好的维护，也不符合开源的哲学（做一件事，并把它做好），所以去除了监控功能, 去除的iOS支持，windows支持，只保留下安卓的自动化支持。

## 文档

在线文档 <http://netease.github.io/airtest>

作为在线文档的一个补充，有个pydoc生成的API列表可以作为参考
 <http://netease.github.io/airtest/airtest.devsuit.html>

离线文档使用方法：

	git clone https://github.com/netease/airtest && cd airtest
	gem install jekyll
	git checkout gh-pages
	jekyll serve --baseurl=''

## 如何给给该项目贡献
因为刚项目常常更新，所以可能会有一些没有测试到的bug。

可以在发现了问题后，提个issue给作者。 另外一些新的思路也可以提到issue中。

