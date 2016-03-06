# Airtest (中文版)

# 代码重构中（不要着急）
另外软件的更新也需要

## 为什么要重构
很多的代码不符合pytohn编码规范, 还有一些很冗余的功能夹杂在里面，很不好维护。
为了能够重现该软件昔日的光芒，是时候擦亮代码，重出江湖了。

## Contribute
如何才能让软件变的更好，这其中也一定需要你的参与才行，发现问题去在github提个issue, 一定会有相应的开发人员看到并处理的。

有开发能力的也可以先跟开发者讨论下想贡献的内容，并提相应的PR由开发人员审核。

## 主要更新内容
* 截图方式从adb screencap转成使用uiautomator

## 安装
1. 首先安装opencv(>=2.4 && <3.0)到你的电脑上

	windows推荐直接通过pip安装, 根据

	**win32**
	
	```
	pip install https://github.com/NetEase/aircv/releases/download/cv2binary/opencv_python-2.4.12-cp27-none-win32.whl
	```

	**amd64**

	# win64
	pip install https://github.com/NetEase/aircv/releases/download/cv2binary/opencv_python-2.4.12-cp27-none-win_amd64.whl
	```

2. 安装airtest

	```
	pip install https://github.com/codeskyblue/airtest/archive/master.zip
	```

3. 安装android依赖

	下载adb安装到电脑上，可选下载地址 <http://adbshell.com/>

## 快速入门
1. 连接一台安卓手机 (4.1+)

	打开windows命令行，执行 `adb devices`, 请确保看到类似输出, 没有其他的错误

	```
	$ adb devices
	List of devices attached
	EP7333W7XB      device
	```

2. 创建一个python文件 `test.py`, 内容如下

	```
	import airtest

	d = airtest.connect(None) # 如果多个手机连接电脑，则需要将None改成对应的设备号
	d.screenshot('screen.png') # 截图
	```

	运行 `python test.py`

3. 截图

	使用windows的画图板打开 `screen.png` 这个文件, 利用其中的截图功能截取需要点击的按钮或者图标
	_PS: 这里其实有个IDE截图的最好了，因为时间精力问题还没有做_

	截图后的文件另存为 `button.png`, `test.py` 最后增加一行 `d.touch_image('button.png')`

	重新运行 `python test.py`, 此时差不多可以看到代码可以点击那个按钮了

4. 更多

	可以使用的接口还有很多，请接着往下看


## 接口
### 截图
`snapshot(filename)`

可以自动识别屏幕的旋转

Parameters

    Name | Type   | Description
---------|--------|------------
filename | string | **Required** 保存的文件名

返回值

无

### 点击图片(制作中)
`touch_image(img)`

img support two types string(file path) or TouchImage 

from airtest.types import TouchImage

Parameters

Name      | Type      | Description
----------|-----------|------------
img       |string or TouchImage  | 需要点击的图片

Example

```
touch_image('start.png')

# or
touch_image(TouchImage(file='start.png', offset=(0, 0)))
```

## 代码导读
`connect` 函数负责根据平台返回相应的类(AndroidDevice or IOSDevice)

图像识别依赖于另一个库 [aircv](https://github.com/netease/aircv), 虽然这个库还不怎么稳定，也还酬和能用吧

其他待补充

## 历史文档 (below)
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

## 相关的项目
1. 基于opencv的图像识别库 <https://github.com/netease/aircv>

## License
This project is under the MIT License. See the [LICENSE](LICENSE) file for the full license text.
