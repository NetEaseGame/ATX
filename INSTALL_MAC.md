# Dependencies for Mac
iOS因为其管理的严格以及文档的困乏，使得其自动化实施起来困难重重。然而iOS的市场占有率又这么高，所以也只能硬着头皮去读Apple网站下一堆晦涩的文档，一边摸索，一边记录。

## Android - ADB安装 (主要用于Android的测试, 这个也可以没有)
命令行输入adb, 然后命令行会提示你怎么安装，按照提示来就好了

```
---------------------------
```
后面的就全是关于iOS自动化的了

## iOS测试 - 硬件的准备
毕竟iPhone是苹果的产品，所以搞iOS测试还是需要有台苹果电脑。
推荐MacMini

![macmini](images/macmini.jpg)

先安装 brew, 如何安装参考 <http://brew.sh>

```
$ brew install libmobiledevice # required
$ brew install homebrew/fuse/ifuse # optional

$ brew install node # skip if you already have node or nvm installed.
$ npm i -g ios-deploy
```

## 安装工具用于解析ipa包

```
$ pip install pyipa
```

## WebDriverAgent的安装 (For iOS test)
Facebook出品的[WebDriverAgent](https://github.com/facebook/WebDriverAgent)为iOS的自动化开辟了一个新的空间

为了方便表达，一般都会用WDA来简称WebDriverAgent，其安装方法请参考 <https://github.com/facebook/WebDriverAgent>

PS：安装最困难的问题，我觉的还是签名的问题，虽然有点麻烦，细心点还是可以搞定的。

Xcode编译没有问题之后，可以尝试命令行看是否正常

```sh
UDID=$(idevice_id -l)
xcodebuild -project WebDriverAgent.xcodeproj \
	-scheme WebDriverAgentRunner \
	-destination "id=$UDID" test
```

不过我还是强烈推荐在**Xcode**中运行（因为可以自动修复CodeSign错误的问题）

成功跑起来之后，会发现iOS上多了一个名叫WebDriverAgent的App, App实际上启动了一个服务器，监听的端口是8100

模拟器的ip是127.0.0.1, 所以其`DEVICE_URL`就是`http://127.0.0.1:8100`, 真机的需要查看手机Wifi的IP地址

## 测试WDA
现在可以直接上代码了

```py
import atx

device_url = 'http://localhost:8100'
d = atx.connect(device_url, platform='ios')

d.start_app('com.apple.Health') # 启动bundleId 为 com.apple.Health的应用
print d.status()
print d.display
print d.screenshot()

d.home()
d.click(100, 200)
```

接下来的用法基本就和README里面写的差不多了。截图速度还可以，大约0.8s, 不过点击的速度就稍微慢了那么点，也许以后会改善的

## FAQ
- How to keep iPhone screen on ?

	1. 通用/自动锁定 改成**永不**
	1. 显示与亮度 调到最低

- 其他90%的问题

	1. 重启iPhone
	1. 重启Mac
	1. 更新XCode

- How to know my udid
	
	<http://whatsmyudid.com/>

- 稳定性

	因为WDA的代码也经常变动，所以atx代码也会跟着变动，有时间运行不了也正常，发现了记得提issue

## 限制的地方
- 除非使用第三方输入法，否则只能对开发者签名的应用有效，其他的App都会陷入长时间的等待
- 输入法只能使用系统自带的输入法
- 点击不受限制，可以将应用转移到后台，然后直接完成点击

## Articles and Projects
- [2012年的文章关于UIAutomation, 4年的时间也没有让它褪色](http://blog.manbolo.com/2012/04/08/ios-automated-tests-with-uiautomation)
- [Apple Provisioning Profile 图文介绍](http://ryantang.me/blog/2013/11/28/apple-account-3/)
- [iOS Provisioning Profile(Certificate)与Code Signing详解](http://blog.csdn.net/phunxm/article/details/42685597)
- Relevant Projects [python-wda](https://github.com/codeskyblue/python-wda)

## Authors
codeskyblue@gmail.com 2016.06, modified 2016.07