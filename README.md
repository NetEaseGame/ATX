![logo](images/logo.png)

# AutomatorX (atx) (中文版)
[![Build Status](https://travis-ci.org/codeskyblue/AutomatorX.svg?branch=master)](https://travis-ci.org/codeskyblue/AutomatorX)
[![Documentation Status](https://readthedocs.org/projects/atx/badge/?version=latest)](http://atx.readthedocs.org/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/atx.svg)](https://pypi.python.org/pypi/atx)
[![PyPI](https://img.shields.io/pypi/dm/atx.svg)](https://pypi.python.org/pypi/atx)
[![PyPI](https://img.shields.io/pypi/l/atx.svg)]()

## 简介
该项目是为了让手机应用的一些常规测试可以自动化起来，让测试人员摆脱那些枯燥的重复性工作。
基于OpenCV的图像识别技术，有点类似于SikuliX(这东西挺好用的，只是没说要支持手机端)

This project is to make mobile test automated, free people who are boring of repeated job. **AutomatorX** is a python library base on `python-opencv` and a lot of outstanding python libs.

ATX is short for _AutomatorX_

If you are new to atx, it better to start from _Quick start tutorial_ or just view [API documentation link](http://atx.readthedocs.org/en/latest/?badge=latest)

## Discuss (讨论群)
面向游戏行业测试人员，当然也开放给国际友人(PS：中文不知道他们看得懂不)

- Chat room [![Gitter](https://badges.gitter.im/codeskyblue/AutomatorX.svg)](https://gitter.im/codeskyblue/AutomatorX?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

PS: 并没有QQ, 因为我们公司上不了QQ

- 网易内部用户目前请直接联系 hzsunshx

## Features
1. 完全的黑盒测试框架，无需知道项目代码，非侵入式
2. 可是很好的支持安卓手机的测试，包括安卓模拟器
3. 支持Windows应用的测试
4. 对于游戏测试，可以使用图像缩放的方法适应不同分辨率的手机

## 历史起源
该项目重构于过去写过一个项目 <https://github.com/netease/airtest>，
因原有代码冗余太严重，维护成本太高，于是就用ATX取代之(Develop from 2016-02-25)。

新版有哪些新的功能呢？

### 与原版主要变化
* 简化安装方式，只需要安装opencv以及通过pip安装atx 无其他依赖
* 支持原生UI元素的查找和点击
* 截图方式从原有缓慢的adb截图，改成默认uiautomator截图，可选minicap截图(1080x1920手机截图平均耗时0.2s）
* 优化图像的自动缩放算法，以便同样的脚本可以适应不同的机器
* 支持Watch用法，可持续监控界面，当某个元素出现时执行特定操作
* 截图客户端从网页服务器变成了python-Tkinter写的客户端 使用python -matx gui启动
* 支持dir(dev) 查看元素已有的方法（-_-! 之前代码写的不好，并不支持）
* 更稳定的依赖库控制，与travis持续集成，可在代码更新后自动发布到pypi
* 移除性能监控功能(目前性能测试使用第三方工具 腾讯GT)
* 图像匹配默认使用模版匹配，将SIFT匹配改为可选

[更多More](CHANGELOG)

## Dependency
1. python2.7
2. opencv2.4
3. Android4.1+

## Installation
1. 首先安装opencv(`>=2.4 && <3.0`)到你的电脑上

	windows推荐直接通过pip安装,
	
	```
	# For Win32
	pip install http://o8oookdsx.qnssl.com/opencv_python-2.4.12-cp27-none-win32.whl
	# For AMD64
	pip install http://o8oookdsx.qnssl.com/opencv_python-2.4.12-cp27-none-win_amd64.whl
	```

	如果pip安装遇到问题，也可以把相应的numpy和opencv下载下来。然后在本地安装 [备用下载地址](https://github.com/NetEase/aircv/releases)，安装方法很简单，例如 `pip install opencv??.whl`, pip最好版本高一点(>=8.1.0)，避免出错。


	如果是Macbook，安装方法要比想象中的简单，然而耗时也比想象中的要长, 先安装`brew`, 之后

	```
	brew install python pillow opencv
	```

	Linux暂时先不写了，折腾过的人可以提个PR补充下。

2. Install atx with `pip`

	为了编码的时候能少敲一点字母, pip中软件包的名字简化成了 atx

	因为目前代码的更新比较快，如果希望使用新功能的话，推荐安装开发版（目前也**强烈推荐**使用开发版）
	For the develop version, (maybe not stable), Sync with github master code

	```
	pip install --upgrade --pre atx
	```

	稳定版的发布频率大约为2周一次. Stable version updated about every two weeks.

	```
	pip install --upgrade atx
	```

	Sometime <https://pypi.python.org> may not stable, it is also passible to install from source.

	```
	pip install -U git+https://github.com/codeskyblue/AutomatorX.git
	```


3. Install `ADB` (Android Debug Bridge)

	If already installed, just skip the part. recommend version `1.0.36`, you can download from [github release](https://github.com/codeskyblue/AutomatorX/releases/download/1.0.12/adb-1.0.36.zip)

	* Download address 1: <https://developer.android.com/studio/index.html>
	* Download address 2: <http://adbshell.com> (this site update not too fast)

	Mac can install adb use `brew` which is eaiser.

4. Show atx version

	```
	python -matx version
	```

	Remember the atx version in case if you want to rollback.

Some may still failed the installation. There are some ways which may help you.

1. Uninstall your python, and reinstall from <https://python.org>
2. Mac user may found install numpy error

    Reference: <http://blog.csdn.net/hqzxsc2006/article/details/51602654>

3. Windows user may found install pyyaml failed.

    Just download the pyyaml wheel file and install with pip. <http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyyaml>
    
## IOS Documentation
该部分记录的内容灵活性比较大，有可能会有大的改动，也有可能以后会删掉。

iOS自动化必须一台Mac，所以请准备好硬件

* [iOS需要安装的软件](README_IOS.md)

## Quick start
* [iOS Quick Start](README_IOS_QUICKSTART.md)

## Windows Quick start (Android)
1. Connect an Android phone (`sdk>=4.1`) to PC

	Open terminal, execute `adb devices`, make sure you see your device.

	```bash
	$ adb devices
	List of devices attached
	EP7333W7XB      device
	```

2. 创建一个python文件 `test.py`, 内容如下

	```python
	# coding: utf-8
	import atx

	d = atx.connect() # 如果多个手机连接电脑，则需要填入对应的设备号
	d.screenshot('screen.png') # 截图
	```

	运行 `python test.py`

3. Take screenshot

	命令行运行 `python -m atx gui`, 鼠标左键拖拽选择一个按钮或者图标, 按下`Save Cropped`截图保存退出. (按下`Refresh`可以重新刷新屏幕)

	![gui](images/atx-gui.gif)

	_PS: 这里其实有个好的IDE截图的最好了，现在是用Tkinter做的，比较简洁，但是可以跨平台，效果也还可以_

	截图后的文件另存为 `button.png`, `test.py` 最后增加一行 `d.click_image('button.png')`

	重新运行 `python test.py`, 此时差不多可以看到代码可以点击那个按钮了

4. 更多

	可以使用的接口还有很多，请接着往下看


## Examples
ATX毕竟是一个python库，给出代码的例子可能更好理解一些

接口可以参考sphinx自动生成文档
[Documentation on ReadTheDocs](http://atx.readthedocs.org/en/latest/?badge=latest)

在Github也记录了部分关键的[API接口](API.md)说明

文档可以等下在看，先看一些例子


* Initial device connect

	```py
	import atx

	d = atx.connect()
	```

	通过设置相应的环境变量也可以设置连接参数，用来方便持续集成

	目前支持4个环境变量

	```sh
	ATX_ADB_SERIALNO
	ATX_ADB_HOST
	ATX_ADB_PORT
	ATX_PLATFORM  默认是 android
	```

	```sh
	$ python -c 'import atx; atx.connect("EFF153")'

	# 等价写法
	$ export ATX_ADB_SERIALNO="EFF153"
	$ python -c 'import atx; atx.connect()'
	```

* App start and stop

	```py
	package_name = 'com.example.game'

	d.stop_app(package_name)
	# d.stop_app(package_name, clear=True) # stop and remove app data
	d.start_app(package_name)
	```

* Execute shell command
	
	```py
	d.adb_cmd(['pull', '/data/local/tmp/hi.txt'])
	d.adb_shell(['uptime'])
	
	# forward device port to localhost
	# same as 
	# adb forward tcp:$(randomPort) tcp:10080
	# Expect: (host, port)
	print d.forward(10080)

	print d.wlan_ip # 获取手机的Wlan IP
	```

* 图片查找与点击

	```py
	# find image position
	if d.exists('button.png'): # 判断截图是否在屏幕中出现, 反馈查找到的坐标
		print 'founded'

	# take screenshot
	d.screenshot('screen.1920x1080.png') # Save screenshot as file

	# click position
	d.click(50, 100) # 模拟点击 x, y

	# long click
	d.long_click(50, 100) # only works on android for now

* click_image函数

	# click image, if "button.png" not found, exception will be raise.
	d.click_image("button.png")

	# click image, if "button.png" not found, will return None
	d.click_image("button.png", safe=True)

	# click image with long click
	d.click_image("button.png", action='long_click')

	# 文件名添加截图手机的分辨率
	d.click_image("button.1920x1080.png")

	# 文件名中添加偏移量, 格式为 <L|R><number><T|B><number>.png
	# 其中 L: Left, R: Right, T: Top, B: Bottom
	# number为百分比
	# 所以 R20T50代表，点击为止从图片中心向右偏移20%并且向上偏移50%
	d.click_image("button.R20T50.png")


	# 不等待的图片点击, 如果图片不存在直接返回None
	d.click_nowait('button.1920x1080.png')

	# click offset image
	d.click_image(atx.Pattern('button.png', offset=(100, -20))) # 带有偏移量的点击
	# TODO(ssx)
	d.click_image('button.p100n20.png') # 带有偏移量的点击, offset = 100, -20
	

	# 指定截图时手机的分辨率是 1920x1080 以便脚本运行在其他分辨率的手机上时可以自动适应
	d.click_image(atx.Pattern('button.png', rsl=(1080, 1920)))

	# if image not show in 10s, ImageNotFoundError will raised
	try:
		d.click_image('button.png', timeout=10.0)
	except atx.ImageNotFoundError:
		print('Image not found')

	# 在特定的区域内查找匹配的图像(IDE暂时还不支持如此高级的操作)
	nd = d.region(atx.Bounds(50, 50, 180, 300))
	print nd.match('folder.png')
	```

* 原生UI操作

	如何点击UI元素请直接看 <https://github.com/codeskyblue/atx-uiautomator>
	里面的API是直接通过继承的方式支持的。

	```py
	# click by UI component
	d(text='Enter').click()
	d(text='Enter').sibling(className='android.widget.ImageView').click()
	```

* 文本的输入

	```py
	d.type("hello world")
	d.type("atx", enter=True) # perform enter after input
	```

* Common settings
	
	```py
	# 配置截图图片的手机分辨率
	d.resolution = (1920, 1080)
	print d.resolution
	# expect output: (1080, 1920) 实际获取到的值会把小的放在前面

	# this is default (first check minicap and then check uiautomator)
	d.screenshot_method = atx.SCREENSHOT_METHOD_AUTO # 默认
	# d.screenshot_method = atx.SCREENSHOT_METHOD_UIAUTOMATOR # 可选
	# d.screenshot_method = atx.SCREENSHOT_METHOD_MINICAP # 可选

	d.image_match_method = atx.IMAGE_MATCH_METHOD_TMPL # 模版匹配, 默认
	# d.image_match_method = atx.IMAGE_MATCH_METHOD_SIFT # 特征点匹配, 可选

	# d.image_match_threshold = 0.8 # 默认(模版匹配相似度)

	d.rotation = None # default auto detect, 这个配置一下比较好，自动识别有时候识别不出来
	# 0: home key bottom(normal)
	# 1: home key right
	# 2: home key top
	# 3: home key left

	# 图片路径查找(实验性功能)
	d.image_path = ['.'] # 默认
	
	# 主要用在希望代码和图片放在不同目录的情况, 如代码结构
	# /--
	#   |-- test.py
	#   |-- images/
	#          |- photo1.png
	#          `- photo2.png
	#
	
	# test.py 中的关键性代码
	d.image_path = ['.', 'images']
	d.click_image('photo1.png')
	d.click_image('photo2.png')
	```


* 监控事件 (这个挺好用的)

	watch是一个内部循环，对于on函数中的所有出现的图片进行监控，如果发现吻合的，就执行后续的操作，直到timeout时间到。

	下面的这个例子，效果为 当出现`notification.png`就点击`confirm.png`图片，只有检查的顺序，并没有执行的顺序。需要注意的是需要在timeout超时之前，执行`quit`函数

	```py
	# watcher, trigger when screenshot is called
	def foo(event):
		print 'It happens', event
		d.click(*event.pos)

	timeout = 50.0 # 50s
	with d.watch(timeout=timeout) as w:
		w.on('enter-game.png').click()
		w.on('notification.png').on('npc.png').click('confirm.png')
		w.on('inside.png').quit().quit()
		w.on_ui(text='Login').quit() # UI Component
		w.on('outside.png').do(foo)

	# will not raise errors(TODO: not working in latest version)
	# 'enter game' is just a name which will seen in debug log
	with d.watch('enter game', timeout, raise_errors=False) as w:
		w.on('output.png').click()
	```	

* events函数调用事件

	```py
	def my_listener(event):
		print 'out:', event

	d.add_listener(my_listener, atx.EVENT_SCREENSHOT)
	d.screenshot()

	# expect output:
	# out: HookEvent(flag=8, args=(), kwargs={})
	```

## ATX Extentions
该部分属于atx的扩展插件实现的功能

插件说明

* [HTML Report](atx/ext/report/README.md)
	
	利用此插件可以在ATX自动化跑完之后，自动生成可以HTML报告，详细记录每一步的执行情况

* Performance record (For Android)
	
	性能测试直接使用了腾讯开源的[GT](http://gt.qq.com/)

	PS: 刚写好没多久，你只能在最新的开发版中看到。有可能以后还会修改。

	使用方法

	1. 首先需要去腾讯GT的主页上，将GT安装到手机上

		<http://gt.qq.com>

	2. 代码中引入GT扩展

		```python
		import atx
		from atx.ext.gt import GT


		d = atx.connect()

		gt = GT(d)
		gt.start_test('com.netease.my') # start test
		# ... do click touch test ...
		gt.stop_and_save()
		```

	3. 运行完测试后，代码会保存到`/sdcard/GT/GW/`+`包名(com.netease.my)`目录下，直接使用`adb pull`下载下来并解析

		```
		$ adb pull /sdcard/GT/GW/com.netease.my/
		```

	该部分代码位于 [atx/ext/gt.py](atx/ext/gt.py), 这部分代码目前在我看来，易用性一般般，希望使用者能根据具体情况，进行修改，如果是修改具有通用性，欢迎提交PR，我们会负责Review代码。

## Command line tools
为了方便测试以及开发，atx封装了很多的命令行工具，功能包含端口转发，包解析，安装，截图等等。

### 针对iOS的命令行工具
需要加上前缀 `python -m atx.ios`

1. developer （因为部分链接还在内网，所以目前只能在网易内部用）

	将iOS设置成开发者模式，需要手机连接上电脑。（仅在windows测试过）

	依赖: iTunes, [iMobileDevice](http://quamotion.mobi/iMobileDevice/Download)

	```
	python -m atx.ios developer
	```

2. screencap

	截图功能（使用前设备需要设置成开发者模式）

	```
	python -m atx.ios screencap -o screen.png
	```

### 针对Android的命令行工具
运行命令行需要加上`python -m atx` 前缀，如启动gui的命令是`python -m atx gui`，命令行的帮助查看方法

```
python -m atx --help
```

1. gui

	简单版的GUI，主要用于截图

2. minicap

	用于安装minicap到手机上

3. tcpproxy

	简单的tcp转发工具，目前用在了模拟器的转发上面，对于海马玩模拟器，使用方法

	* 在一台运行这海马玩的电脑上运行 `python -matx tcpproxy`
	* 记录下机器的IP地址，比如 10.0.0.1
	* 在另外一台机器上运行 `adb connect 10.0.0.1` 来远程连接

4. apkparse

	用于解析apk的包名和activity，使用方法

	```
	$ python -matx apkparse demo.apk
	{
    	"main_activity": "com.example.demo.activity.Main",
    	"package_name": "com.example.demo"
	}
	```

6. install (仅限apk)

	支持从URL,以及本地路径安装应用，支持文件推送到手机时显示进度

	```
	$ python -matx install example.apk
	2016-04-26 16:33:52.370 INFO  [install:  93] APK package name: com.netease.example
	2016-04-26 16:33:52.370 INFO  [install:  94] APK main activity: com.netease.example.MainActivity
	2016-04-26 16:33:52.371 INFO  [install:  96] Push file to android device
	100% |===========================================| 5.88M/5.88M [4.89M/s]
	2016-04-26 16:33:57.521 INFO  [install:  99] Install ..., will take a few seconds
	2016-04-26 16:34:08.179 INFO  [install: 101] Done

	$ python -matx install --start example.apk
	# Start app after installed.
	```

	另外install支持一些默认软件的安装，目前有 utf7ime

	使用方法如 `python -matx install utf7ime`

7. screencap
	拥有超越`adb shell screencap`的速度以及兼容性，使用了PIL库，输出的格式根据文件的扩展名的自动确定

	```sh
	$ python -m atx screencap -o screen.png
	```

8. screenrecord （仅限android）

	录制视频功能，需要预先安装minicap

9. info

	显示手机重用信息，输出格式是JSON

	```sh
	$ python -m atx info
	```

## FAQ
1. 如果连接远程机器上的安卓设备

	远程机器上使用如下命令启动命令

	```
	adb kill-server
	adb -P 5037 -a nodaemon server
	# or: adb -P 5037 -a fork-server server
	```

	连接时指定远程机器的IP和端口号就好了

2. 如何一个脚本可以适应不同的机器（针对于手机游戏）

	市面上大部分的手机都是 16:9 还有一部分是 4:3,5:3,8:5 其他比例的似乎寥寥。而游戏中元素的大小，在屏幕变化的时候，也会等比例的去缩放。16:9到4:3的缩放比例似乎也有规律可循，暂时不研究啦。

	| W/H | Display |
	|-----|---------|
	|16/9 | 540x960, 720x1280, 1080x1920, 1440x2560 |
	|8/5  | 800x1280, 1200x1920, 1600x2560 |
	|5/3  | 1152x1920, 1080x1800 |
	|4/3  | 1536x2048 |


	所以通常只需要找个分辨率高点的设备，然后截个图。同样宽高比的手机就可以一次拿下。

	```
	d.resolution = (1080, 1920)
	```

	设置完后，当遇到其他分辨率的手机，就会自动去缩放。因为ATX主要针对游戏用户，横屏的时候，缩放是根据Y轴缩放的，竖排则根据X轴。可能有点抽象，理解不了也没关系

3. 是否可以在模拟器上运行自动测试

	测试后，发现是可以的。我直接用了当前市场上最流行的[海马玩 版本0.9.0 Beta](http://dl.haima.me/download/D4XU/win/0.9.0/Setup.exe) 安装完之后使用 `adb connect 127.0.0.1:26944` 连接上，之后的操作就跟普通的手机一样了。_注: 根据海马玩版本的不同，端口可能也不一定一样_

	海马玩监听的端口是本机的26944，如果需要测试脚本运行在远程，用tcp转发到0.0.0.0就好了。方法有很多，可以用自带的程序 `python -matx tcpproxy` 或者直接参考目录下的 [scripts/simple-tcp-proxy.py](scripts/simple-tcp-proxy.py) 用代码实现

	很多模拟器的引擎是VirutualBox，其实还可以通过VirtualBox的接口来截图，这种方法更快一点，不过看说明安装似乎很复杂，试验了下也没成功，若是有人搞定了，可以分享下

4. minicap是什么, 如何安装?

	minicap是[openstf](https://github.com/openstf)开源项目中的一个子项目，用于手机快速的截图. 连接手机到电脑上之后，简单的安装方法 `python -matx minicap` 
	_注意：请不要在模拟器上尝试_


5. 遇到 IOError: RPC server not started!

	卸载已有的应用，重新运行测试

	```
	adb uninstall com.github.uiautomator
	adb uninstall com.github.uiautomator.test
	```

6. 卸载

	```
	adb uninstall com.github.uiautomator
	adb uninstall com.github.uiautomator.test

	adb shell rm /data/local/tmp/minicap
	adb shell rm /data/local/tmp/minicap.so
	```

7. 解决输入法遇到的问题

	可以专门为自动化开发的Utf7Ime的输入法 [源码地址](https://github.com/macacajs/android-unicode)

	启动方法

	```sh
	python -m atx install utf7ime
	adb shell ime enable android.unicode.ime/.Utf7ImeService
	adb shell ime set android.unicode.ime/.Utf7ImeService
	```

	关闭方法

	```
	adb shell ime disable android.unicode.ime/.Utf7ImeService
	```

## 代码导读
`connect` 函数负责根据平台返回相应的类(AndroidDevice or IOSDevice)

图像识别依赖于另一个库 [aircv](https://github.com/netease/aircv), 虽然这个库还不怎么稳定，也还凑合能用吧

每个平台相关的库都放到了 目录 `atx/device`下，公用的方法在`atx/device/device_mixin.py`里实现。第三方扩展位于`atx/ext`目录下。

## 相关的项目
1. 基于opencv的图像识别库 <https://github.com/netease/aircv>
2. 感谢作者 <https://github.com/xiaocong> 提供的uiautomator的python封装，相关项目已经fork到了

	- <https://github.com/codeskyblue/android-uiautomator-server>
	- <https://github.com/codeskyblue/atx-uiautomator>
3. Android input method <https://github.com/macacajs/android-unicode>
3. SikuliX <http://sikulix-2014.readthedocs.org/en/latest/index.html>
4. Blockly <https://github.com/codeskyblue/blockly>

## Articles
1. [让adb install显示进度](https://testerhome.com/topics/4772)
2. [Android 屏幕同步和录制工具](https://testerhome.com/topics/5006)
3. [安卓手机的快速截图](https://testerhome.com/topics/5004)

## Developer dashboards
1. Platform Versions, Screen Size, Open GL Version <http://developer.android.com/intl/zh-cn/about/dashboards/index.html>

## Contribution
如何才能让软件变的更好，这其中也一定需要你的参与才行，发现问题去在github提个issue, 一定会有相应的开发人员看到并处理的。文档有错误的话，直接提Issue，或者提PR都可以。
由于我平常使用该项目的概率并不怎么高，所有不少问题即使存在我也不会发现，请养成看到问题提Issue的习惯，所有的Issue我都会去处理的，即使当时处理不了，等技术成熟了，我还是会处理。但是如果不提交Issue，说不定我真的会忘掉。

BTW: 有开发能力的也可以先跟开发者讨论下想贡献的内容，并提相应的PR由开发人员审核。

## License
This project is under the Apache 2.0 License. See the [LICENSE](LICENSE) file for the full license text.

