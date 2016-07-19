## iOS WebDriverAgent
Facebook出品的[WebDriverAgent](https://github.com/facebook/WebDriverAgent)为iOS的自动化开辟了一个新的空间

## How to install
Refer to <https://github.com/facebook/WebDriverAgent>

安装最困难的问题，我觉的还是签名的问题，虽然有点麻烦，加油你可以的。

Xcode编译没有问题之后，尝试命令行看是否正常

```sh
UDID=$(idevice_id -l)
xcodebuild -project WebDriverAgent.xcodeproj \
	-scheme WebDriverAgentRunner \
	-destination "id=$UDID" test
```

## How to use
There is a python client wrap by ATX.

```py
from atx.device.ios_webdriveragent import IOSDevice
d = IOSDevice(udid=None)
```

