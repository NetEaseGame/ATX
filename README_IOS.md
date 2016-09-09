## iOS Automation
iOS因为其管理的严格以及文档的困乏，使得其自动化实施起来困难重重。然而iOS的市场占有率又这么高，所以也只能硬着头皮去读Apple网站下一堆晦涩的文档，一边摸索，一边记录。


## 相关工具安装
毕竟iPhone是苹果的产品，所以搞iOS测试还是得有台苹果电脑的好。
推荐MacMini

![macmini](images/macmini.jpg)

先安装 brew, 如何安装参考 <http://brew.sh>

## 必装项
1. Xcode
2. Numpy

	```sh
	brew install numpy
	```

	部分电脑中可以会有低版本的numpy, 但是有卸载不掉, 就需要参考这篇文章了
    <http://blog.csdn.net/hqzxsc2006/article/details/51602654>

3. OpenCV

	用brew安装其实比较简单, 时间稍微长点，喝杯茶慢慢的等就好了

	```
	brew install python pillow opencv
	```

4. AutomatorX

	ATX本身就是一个pytohn库, 所以安装起来比较简单

	```sh
	pip install --pre --upgrade atx
	```

	`--pre` 表示预览版本, `--upgrade` 表示如果已经安装过了，就更新

## iOS App test requirements
iOS的驱动靠的就是[WebDriverAgent](https://github.com/facebook/WebDriverAgent), 感谢Facebook为iOS的自动化开辟了一个新的空间

### Hot to install WebDriverAgent
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

### 限制的地方
- 除非使用第三方输入法，否则只能对开发者签名的应用有效，其他的App都会陷入长时间的等待
- 输入法只能使用系统自带的输入法
- 点击不受限制，可以将应用转移到后台，然后直接完成点击

### iOS App test optional requirements
既然是可选，就是可装可不装

```
$ brew install libmobiledevice # required
$ brew install homebrew/fuse/ifuse # optional

$ brew install node # skip if you already have node or nvm installed.
$ npm i -g ios-deploy
```


安装工具用于解析ipa包

```
$ pip install pyipa
```

### FAQ
- How to keep iPhone screen on ?

	1. 通用/自动锁定 改成**永不**
	1. 显示与亮度 调到最低

- 其他90%的问题

	1. 重启iPhone
	1. 重启Mac
	1. 更新XCode

- How to know my udid
	
	<http://whatsmyudid.com/>

## Articles
- [2012年的文章关于UIAutomation, 4年的时间也没有让它褪色](http://blog.manbolo.com/2012/04/08/ios-automated-tests-with-uiautomation)

## Authors
codeskyblue@gmail.com 2016.06