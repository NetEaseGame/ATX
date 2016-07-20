## iOS WebDriverAgent
Facebook出品的[WebDriverAgent](https://github.com/facebook/WebDriverAgent)为iOS的自动化开辟了一个新的空间

## How to install
Refer to <https://github.com/facebook/WebDriverAgent>

安装最困难的问题，我觉的还是签名的问题，虽然有点麻烦，细心点还是可以搞定的。

Xcode编译没有问题之后，尝试命令行看是否正常


在真机上运行的命令，不过我还是强烈推荐在**Xcode**中运行（因为可以自动修复CodeSign错误的问题）

```sh
UDID=$(idevice_id -l)
xcodebuild -project WebDriverAgent.xcodeproj \
	-scheme WebDriverAgentRunner \
	-destination "id=$UDID" test
```

## How to use
There is a python client wrap by ATX.

WebDriverAgent搞定之后，DeviceURL就拿到了，真机的话需要查看手机的WIFI的IP地址，模拟器直接就是Localhost。端口都是8100

以模拟器为例 其`DEVICE_URL`为`http://localhost:8100`

```py
import atx

deivce_url = 'http://localhost:8100'
d = atx.connect(device_url, platform='ios')

d.start_app('com.netease.demo') # 启动bundleId 为 com.netease.demo的应用
print d.status()
print d.display
print d.screenshot()

d.home()
d.click(100, 200)
```

接下来的用法基本就和README里面写的差不多了。截图速度还可以，大约0.8s, 不过点击的速度就稍微慢了那么点

## Relevant Projects
* [python-wda](https://github.com/codeskyblue/python-wda)