# AirtestX (中文版)
[![Build Status](https://travis-ci.org/codeskyblue/AirtestX.svg?branch=master)](https://travis-ci.org/codeskyblue/AirtestX)
[![Documentation Status](https://readthedocs.org/projects/atx/badge/?version=latest)](http://atx.readthedocs.org/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/atx.png)](https://badge.fury.io/py/atx)


改版自一个老项目 <https://github.com/netease/airtest>

该项目是为了让手机应用的一些常规测试可以自动化起来，让测试人员摆脱那些枯燥的重复性工作。基于OpenCV的图像识别技术，虽然有点类似于Sikuli, Appium

airtest已经有人用，但是这次重构，估计好多api都会变了。最好的办法还是重建一个项目比较好，感谢<https://github.com/pactera>给起的名字 AirtestX

## 为什么要重构
很多的代码不符合python编码规范, 还有一些很冗余的功能夹杂在里面，很不好维护。
为了能够重现该软件昔日的光芒，是时候擦亮代码，重出江湖了。

## Contribute
如何才能让软件变的更好，这其中也一定需要你的参与才行，发现问题去在github提个issue, 一定会有相应的开发人员看到并处理的。
由于我平常使用该项目的概率并不怎么高，所有不少问题即使存在我也不会发现，请养成看到问题提Issue的习惯，所有的Issue我都会去处理的，即使当时处理不了，等技术成熟了，我还是会处理。但是如果不提交Issue，说不定我真的会忘掉。

BTW: 有开发能力的也可以先跟开发者讨论下想贡献的内容，并提相应的PR由开发人员审核。

网易内部用户暂时请直接联系 hzsunshx

## 与原版主要变化
* 简化安装方式，只需要安装opencv以及通过pip安装atx(airtestX的简称）无其他依赖
* 支持原生UI元素的查找和点击
* 截图方式重原有缓慢的adb截图，改成默认uiautomator截图，可选minicap截图(1080x1902手机截图平均耗时0.2s）
* 优化图像的自动缩放算法，以便同样的脚本可以适应不同的机器
* 支持Watch用法，可持续监控界面，当某个元素出现时执行特定操作
* 截图客户端从网页服务器变成了python-Tkinter写的客户端 使用python -matx启动
* 支持dir(dev) 查看元素已有的方法（-_-! 之前代码写的不好，并不支持）
* 更稳定的依赖库控制，与travis持续集成，可在代码更新后自动发布到pypi
* 移除性能监控功能，暂时移除iOS支持
* 图像匹配默认使用模版匹配，将SIFT匹配改为可选

## 依赖
1. python2.7
2. opencv2.4, numpy
3. Android4.1+

## 安装
1. 首先安装opencv(`>=2.4 && <3.0`)到你的电脑上

	windows推荐直接通过pip安装, 根据你是win32还是amd64选择合适的版本，前往下载地址<https://github.com/NetEase/aircv/releases>，
	把相应的numpy和opencv下载下来。安装方法很简单

	例如 `pip install numpy-1.10.4.mkl-cp27-none-win32.whl`, pip最好版本高一点，避免出错

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
	 pip install -i https://testpypi.python.org/pypi -U --pre atx
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

## 配置项
```
#
d.screenshot_method = atx.SCREENSHOT_METHOD_UIAUTOMATOR # 默认
# d.screenshot_method = atx.SCREENSHOT_METHOD_MINICAP # 可选

d.image_match_method = atx.IMAGE_MATCH_METHOD_TMPL # 模版匹配, 默认
# d.image_match_method = atx.IMAGE_MATCH_METHOD_SIFT # 特征点匹配, 可选
```

## 接口
### 连接设备
`connect(udid, **kwargs)`

对于安卓设备常见连接方法

```
connect(None)
connect(None, host='127.0.0.1', port=5037)
connect('EFSXA124') # specify serialno
```

connect返回一个Device对象, 该对象下有很多方法可以用，使用举例

```
d = atx.connect(None)
d.screenshot('screen.png')
```

## Device下的方法
### 截图
`screenshot(filename)`

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

print d.wlan_ip
# expect 10.1.x.x
d.sleep(5) # sleep 5s
d.adb_shell('uptime') # not done yet.

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
timeout = 50 # 50s
with d.watch('enter game', timeout) as w:
	w.on('enter-game', atx.Watcher.ACTION_TOUCH)
	w.on('inside.png', atx.Watcher.ACTION_QUIT)

# click by ui component
d(text='Enter').click()

d.stop_app(package_name)
```

如何点击UI元素请直接看 <https://github.com/codeskyblue/airtest-uiautomator>
里面的API是直接通过继承的方式支持的。

TODO: Watch还需要改的再好用一点，目前的想法

```
with d.watch('enter game') as w:
	w.on('enter-game').click()
	w.on(text='Quick Game').click(text='Login')
	w.on('btn-a.png').not('btn-b.png').quit()
	w.on('accept.png').click()
	w.on(text='Login').quit()
```

## FAQ
1. 如果连接远程机器上的安卓设备(测试过，并不好使，可能跟pyuiautomator依赖`adb forword`有关)

	远程机器上使用如下命令启动命令

	```
	adb kill-server
	adb -P 5037 -a fork-server server
	```

	连接时指定远程机器的IP和端口号就好了

2. 如何一个脚本可以适应不同的机器（针对于找不到控件的游戏）

	市面上大部分的手机都是 16:9 还有一部分是 4:3 其他比例的似乎了了。而游戏中元素的大小，在屏幕变化的时候，也会等比例的去缩放。16:9到4:3的缩放比例似乎也有规律可循，暂时不研究啦。

	所以通常只需要找个分辨率高点的设备，然后截个图。同样宽高比的手机就可以一次拿下。

	```
	d.resolution = (1280, 1920)
	```

	设置完后，当遇到其他分辨率的手机，就会自动去缩放。

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

