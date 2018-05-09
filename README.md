# ATX(AutomatorX) (中文版)
[![Build Status](https://travis-ci.org/NetEaseGame/ATX.svg?branch=master)](https://travis-ci.org/NetEaseGame/ATX)
[![Documentation Status](https://readthedocs.org/projects/atx/badge/?version=latest)](http://atx.readthedocs.org/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/atx.svg)](https://pypi.python.org/pypi/atx)
[![PyPI](https://img.shields.io/pypi/l/atx.svg)]()
[![Gitter](https://badges.gitter.im/codeskyblue/ATX.svg)](https://gitter.im/codeskyblue/ATX?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

## Introduction (简介)
ATX(AutomatorX) 是一款开源的自动化测试工具，支持测试iOS平台和Android平台的原生应用、游戏、Web应用。
使用Python来编写测试用例，混合使用图像识别，控件定位技术来完成游戏的自动化。附加专用的IDE来完成脚本的快速编写。

## Hope (愿景)
希望该项目可以让手机应用测试自动化起来，让测试人员摆脱那些枯燥的重复性工作。

## 重要说明
新版本以采用新的uiautomator2替换到原来的[atx-uiautomator](https://github.com/openatx/atx-uiautomator). 历史版本可以通过Tag查看[tag:1.1.3](https://github.com/NetEaseGame/ATX/tree/1.1.3)
测试安卓应用前，需要先进行init操作

```
python -muiautomator2 init
```

用于安卓和iOS原生应用测试的库已经分离出来，可以单独使用（强烈推荐单独使用，一来依赖少、稳定性高，二来写代码的时候还能自动补全）

1. 对于Android应用的测试，如果不需要用到图像识别，推荐使用这个项目[uiautomator2](https://github.com/openatx/uiautomator2)
1. 对于iOS应用的测试，如果不需要用到图像识别，推荐使用这个项目[facebook-wda](https://github.com/openatx/facebook-wda)

BTW: atx-webide已经不在维护

## Features
- [x] 支持iOS, Android 双平台的原生应用，Web应用和游戏
- [x] 支持通过图像识别来定位元素的位置
- [x] 内置自动生成测试报告的功能
- [x] 网页版的脚本编辑器，来帮助快速的写代码

## Discuss (讨论群)
面向游戏行业测试人员，当然也开放给国际友人(PS：中文不知道他们看得懂不)

- QQ: `499563266` PS: 因为我们公司上不了QQ, 所以不会经常上
- 网易内部用户加Popo群 `1347390` 群主 `hzsunshx`
- [Testerhome社区](https://testerhome.com/topics/node78)
- ~~[Gitter Chat Room](https://gitter.im/codeskyblue/AutomatorX?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)~~

## Limitation (限制)
- Python >= 2.7 && <= 3.6
- Android 4.1+
- iOS 9.0+ with Mac
- adb >= 1.0.36

## Installation (安装)
准备Python虚拟环境 [Virtualenv]((http://www.jianshu.com/p/08c657bd34f1))

```bash
pip install virtualenv
virtualenv venv

# Linux or Mac
. venv/bin/activate

# Windows
venv\Scripts\activate.bat 
```

安装相关的python库

```bash
# install the lastest version of atx
# If feed too slow use douban pypi mirror:  -i https://pypi.doubanio.com/simple/
pip install --upgrade --pre atx

# install opencv dependencies
pip install opencv_contrib_python
```

**Android测试依赖**

- ADB

	* [Windows adb安装指南](https://github.com/NetEase/AutomatorX/wiki/Win-Installation)
	* Mac上的adb可以通过命令行安装 `brew install android-platform-tools`

- [ATX手机助手.apk](https://o8oookdsx.qnssl.com/atx-assistant-1.0.4.apk)

	该App为自动化提供了输入法的功能，屏幕常量等功能
	命令行安装 `python -m atx install atx-assistant`

**iOS测试依赖**

- WebDriverAgent

	由于WebDriverAgent更新过快，atx的一个依赖库[facebook-wda](https://github.com/openatx/facebook-wda)还跟不上他更新的速度，下载完WDA后，请切换到这个版本

	```
	git reset --hard a8def24ca67f8a74dd709b899c8ea539c9c488ea
	```

	你的iPhone手机需要连接到Mac上，然后Mac安装[WebDriverAgent](https://github.com/facebook/WebDriverAgent)，通常对Xcode部署的人搭WDA的人会遇到不少问题，搞不定继续参考这里 <https://testerhome.com/topics/7220>

	WDA成功启动后，会生成一个用于ATX连接的http地址，比如`http://localhost:8100`

**检查安装是否成功**

```bash
# 查看atx版本号
python -m atx version
# 检查环境配置是否正常
python -m atx doctor
```

**脚本编辑器**(可选)

为了方便快速的写出脚本，提供了三个Web编辑器。

- 自带GUI

	自带的使用Tkinter写的编辑器，只提供截图功能，但是比较稳定，启动方法 `python -m atx gui -s ${SERIAL or WDA_URL}`
	使用 `python -m atx gui -h` 可以查看更多的选项

- [weditor](https://github.com/openatx/weditor) __beta__ 针对Android和iOS原生应用快速定位元素，自动生成代码

## Getting Started （必看）
* [快速入门文档](docs/QUICKSTART.md)
* [~~如何使用内置的测试报告功能~~](atx/ext/report/README.md)
* [ATX资料快速索引](https://testerhome.com/topics/9091)
* [Testerhome上的ATX有关的文章列表](https://testerhome.com/topics/node78)

内置的测试报告暂时有点问题，最近没时间去修复了。因为ATX底层使用的[uiautomator2](https://github.com/openatx/uiautomator2)，测试报告可以用底层库自带的 [SimpleHTMLReport](https://github.com/openatx/uiautomator2/tree/master/uiautomator2/ext/htmlreport)

## APIs (接口文档)
* [常用接口](docs/API.md)
* [iOS的接口文档](https://testerhome.com/topics/7204)

## Other (其他)
* ATX自带的命令行工具 <https://github.com/NetEase/AutomatorX/wiki/Command-Line-Tools>

## Known Issues (常见问题)
If you are having some issues please checkout [wiki](https://github.com/NetEase/AutomatorX/wiki/Common-Issues) first.

为了避免潜在的Python编码问题，代码文件都应该用UTF-8编码格式保存。

- 测试中出现的弹窗如何处理？

	《iOS弹窗如何自动处理》，仅供参考 https://testerhome.com/topics/9540

- 对于python2.7 字符串前应该加上u开头，例如`u'你好'`

	文件的开头可以加上下面这段代码，强制使用python3的编码体系(默认全部都是unicode)

	```python
	from __future__ import unicode_literals
	```

- 对于python3的非windows系统
	
	检查一下`sys.stdout.encoding`的编码是否是UTF-8，不然中文字符的输出通常会有问题
	解决办法通常就是在bashrc文件中加入一行

	```shell
	export PYTHONIOENCODING=UTF-8
	```

## ATX Extentions （扩展功能）
* WebView

	目前仅限安卓, 具体参考 <https://testerhome.com/topics/7232>

	例子代码

	```python
	# coding: utf-8
	import atx
	from atx.ext.chromedriver import ChromeDriver

    d = atx.connect()
    driver = ChromeDriver(d).driver() # return selenium.driver instance
    elem = driver.find_element_by_link_text(u"登录")
    elem.click()
    driver.quit()
    ```

    PS: 实现这个扩展并不复杂，简单的封装了一下selenium就搞定了

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

## 代码导读
`connect` 函数负责根据平台返回相应的类(`atx.drivers.android.AndroidDevice` or `atx.drivers.ios_webdriveragent.IOSDevice`)

图像识别依赖于另一个库 [aircv](https://github.com/netease/aircv), 虽然这个库还不怎么稳定，也还凑合能用吧

每个平台相关的库都放到了 目录 `atx/device`下，公用的方法在`atx/device/device_mixin.py`里实现。第三方扩展位于`atx/ext`目录下。

## Related projects (相关的项目)
1. 基于opencv的图像识别库 <https://github.com/netease/aircv>
2. 感谢作者 <https://github.com/xiaocong> 提供的uiautomator的python封装，相关项目已经fork到了

	- <https://github.com/codeskyblue/android-uiautomator-server>
	- <https://github.com/codeskyblue/atx-uiautomator>
3. Android input method <https://github.com/macacajs/android-unicode>
3. SikuliX <http://sikulix-2014.readthedocs.org/en/latest/index.html>
4. Blockly <https://github.com/codeskyblue/blockly>

## Contribution (参与贡献)
如何才能让软件变的更好，这其中也一定需要你的参与才行，发现问题去在github提个issue, 一定会有相应的开发人员看到并处理的。文档有错误的话，直接提Issue，或者提PR都可以。
由于我平常使用该项目的概率并不怎么高，所有不少问题即使存在我也不会发现，请养成看到问题提Issue的习惯，所有的Issue我都会去处理的，即使当时处理不了，等技术成熟了，我还是会处理。但是如果不提交Issue，说不定我真的会忘掉。

BTW: 有开发能力的也可以先跟开发者讨论下想贡献的内容，并提相应的PR由开发人员审核。

## License (协议)
This project is under the Apache 2.0 License. See the [LICENSE](LICENSE) file for the full license text.

