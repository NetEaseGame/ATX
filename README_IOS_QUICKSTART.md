# Quick Start for iOS
## 准备条件

1. 准备一个App，该App需要开发者证书签名(理论上越狱的iPhone也可以)
1. 准备一台Mac，因为自动化依赖instruments，而instruments只有mac上才有

## Step by step
1. 连接一台iPhone手机

	打开命令行输入 `idevice_id -l` 看到有长串无规律的字符串即可

	```
	$ idevice_id -l
	72739e3823481a651d71e3d9a89bd6f63d253486
	```

2. 打开iPhone的开发者模式

	```
	$ python -m atx.ios developer
	```

3. 打开atx自带的截图工具

	```
	$ python -m atx gui --platform ios
	```

	截张图, 命名为 `button.png`

	注：该GUI对iOS只能截图，不能执行代码，需要执行代码的话（哎，以后在搞，UIAutomation就是反应太慢了）

4. 创建一个文件

	命令为 `runtest.py`, 内容

	```py
	import atx

	bundle_id = 'com.netease.demo'
	udid = None
	d = atx.connect(bundle_id, udid=udid, platform='ios') # need wait for nearly 10s
	d.click('button.png')
	```

	运行 `python runtest.py`

到此如果问题不大，入门教程完成，更多接口，需要查看README.md

## How it works
The iOS automation is very like appium, which use *UIAutomation* for test. Create a unix socket for communication between python and UIAutomation.

## 其他资料
- [Apple Provisioning Profile 图文介绍](http://ryantang.me/blog/2013/11/28/apple-account-3/)
- [iOS Provisioning Profile(Certificate)与Code Signing详解](http://blog.csdn.net/phunxm/article/details/42685597)