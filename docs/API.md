# API
接口也可以参考sphinx自动生成文档
[Documentation on ReadTheDocs](http://atx.readthedocs.org/en/latest/?badge=latest)


## Initial android device connect (Only Android)

```python
import atx

d = atx.connect()
```

通过设置相应的环境变量也可以设置连接参数，用来方便持续集成

目前支持4个环境变量

```bash
ATX_PLATFORM  # 默认是 android
ATX_CONNECT_URL # 设备连接地址，可以是serialno或者wdaUrl
ATX_ADB_HOST
ATX_ADB_PORT
ATX_ADB_SERIALNO # 建议使用 ATX_CONNECT_URL 代替
```

假设手机序列号是 `EFF153`, 连接命令

```bash
$ python -c 'import atx; atx.connect("EFF153")'
```

等价写法

```bash
# linux
$ export ATX_CONNECT_URL="EFF153"
# windows
C:\> set ATX_CONNECT_URL=EFF153

$ python -c 'import atx; atx.connect()'
```

## App start and stop

```python
package_name = 'com.example.game'

d.stop_app(package_name)
# d.stop_app(package_name, clear=True) # stop and remove app data (only Android)

# recommend way
d.start_app(package_name, main_activity)

# force stop the target app before starting the activity
d.start_app(package_name, main_activity, stop=True)

# use adb shell monkey to start app (not recommend)
d.start_app(package_name)
```

## Execute shell command (Only Android)
	
```py
d.adb_cmd(['pull', '/data/local/tmp/hi.txt']) # default timeout 30s, use timeout=None to set unlimited time
d.adb_shell(['uptime'])

# forward device port to localhost
# same as 
# adb forward tcp:$(randomPort) tcp:10080
# Expect: (host, port)
print d.forward(10080)

print d.wlan_ip # 获取手机的Wlan IP

print d.current_app() # 获取当前运行应用的package name和activity以及运行的pid
# Expect: AppInfo(package='com.miui.mihome2', activity='com.android.launcher2.Launcher', pid=634)
```

可以使用`atx.adb_client`变量, 更方便的操作adb， 暂时没写文档，具体参考代码[adbkit/client.py](https://github.com/NetEaseGame/ATX/blob/master/atx/adbkit/client.py)

先给几个例子

```python
c = atx.adb_client
c.version() # adb version
c.devices() # list of devices
```

## 图片查找与点击

```py
# find image position
if d.exists('button.png'): # 判断截图是否在屏幕中出现, 反馈查找到的坐标
	print 'founded'

# take screenshot
d.screenshot('screen.1920x1080.png') # Save screenshot as file

# click position
d.click(50, 100) # 模拟点击 x, y

# click percentage of screen (when pos.x and pox.y < 0)
d.click(0.5, 0.5) # click center of screen

# long click
d.long_click(50, 100) # only works on android for now
```

## 滑动与拖动
```py
d.swipe(fromX, fromY, toX, toY, steps=100)
# steps 默认100, 一个step执行大约5ms，所有100的steps相当于0.5s

# 接口跟swipe很类似, 效果相当于先长按一下然后swipe
d.drag(fromX, fromY, toX, toY, steps=100)
```

## click_image函数

```py
# click image, if "button.png" not found, exception will be raise.
d.click_image("button.png")

# add description (also used for report generate)
d.click_image("button.png", desc="I love click")

# click image, if "button.png" not found, will return None
d.click_image("button.png", safe=True)

# click image with long click
d.click_image("button.png", action='long_click')

# 不等待的图片点击, 如果图片不存在直接返回None
d.click_exists('button.png')

# 文件名添加截图手机的分辨率, 脚本运行在其他分辨率的手机上时可以自动适应
d.click_image("button.1920x1080.png")
```

## 多分辨率适配
```
# 下面这种方法会自动根据当前测试手机的分辨率选择合适的文件
# 比如手机分辨率1920x1080,代码会自动寻找文件4中文件之一，找到就返回
# - button@1920x1080.png
# - button@1080x1920.png
# - button.1920x1080.png
# - button.1080x1920.png
d.click_image("button@auto.png")
```

比如下面这张图
![gionee-close-ad](multisize-button.png)

点击这个按钮用这种方法就好 `d.click_image("gionee-close-ad@auto.png")`

关于为什么同时出现用`@`和`.`分隔，一开始用的是pytk写的编辑器，那个tkFileDialog对`@`支持的不好，所以只能用`.`

## 偏移量以及范围限制

```
# 文件名中添加偏移量, 格式为 <L|R><number><T|B><number>.png
# 其中 L: Left, R: Right, T: Top, B: Bottom
# number为百分比
# 所以 R20T50代表，点击为止从图片中心向右偏移20%并且向上偏移50%
d.click_image("button.R20T50.png")
# same as
d.click_image("button.png", offset=(0.2, -0.5))

# Full example
# param: delay is when image found wait for a moment then click
d.click_image("button.png", 
	offset=(0.2, 0.5), 
	action="long_click", 
	safe=True, 
	desc="I love click", 
	method='template', 
	threshold=0.8,
	delay=2.0)

# if image not show in 10s, ImageNotFoundError will raised
try:
	d.click_image('button.png', timeout=10.0)
except atx.ImageNotFoundError:
	print('Image not found')

# 在特定的区域内查找匹配的图像(IDE暂时还不支持如此高级的操作)
nd = d.region(atx.Bounds(50, 50, 180, 300))
print nd.match('folder.png')
```

## 锁定当前屏幕（主要用于提高查询效率）
```
d.keep_screen()
d.click_exists("button1.png")
d.click_exists("button2.png")
d.free_screen()
```

这种操作，执行第二次`click_exists`时，就不会再次截图。另外上面的代码也可以这样写

```
with d.keep_screen():
	d.click_exists("button1.png")
	d.click_exists("button2.png")
```

## 图片等待操作
```
d.wait("button.png") # 等待一个按钮出现
d.wait_gone("button.png") # 等待一个按钮消失
```

## 原生UI操作
下面给的例子并不完全，更多的接口需要看下面这两个链接

- Android 如何点击UI元素请直接看 <https://github.com/codeskyblue/atx-uiautomator>
- iOS如何点击UI元素参考 <https://github.com/codeskyblue/python-wda>

里面的API是直接通过继承的方式支持的。

```py
# click by UI component
d(text='Enter').click()
d(text='Enter').sibling(className='android.widget.ImageView').click() # only android

# swipe from (sx, sy) to (ex, ey)
d.swipe(sx, sy, ex, ey)
# swipe from (sx, sy) to (ex, ey) with 10 steps
d.swipe(sx, sy, ex, ey, steps=10)

## 文本的输入
```py
d.type("hello world")
d.type("atx", enter=True) # perform enter after input
d.type("atx", next=True) # jump to next after input
d.clear_text() # clear input
```

为了更简化代码，现提供如下操作

```python
d.type("www.baidu.com", clear=True, resourceId="com.android.browser:id/url_bar")
# 一行代码等价于下面4行代码
d(resourceId="com.android.browser:id/url_bar").click()
d.clear_text()
d.type("www.baidu.com")
d.keyevent("ENTER")
```

安卓手机因为输入法的众多，接口不统一，所以为了方便我们的自动化，就专门做了一个输入法。下载安装ATX助手即可

```
python -matx install atx-assistant
```

通常直接调用 `d.type`是不会出问题的，但也不是绝对的。最好在测试之前调用 `d.prepare_ime()` 将输入法切换到我们定制的**ATX助手输入法**

## Common settings
	
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
```

## events函数调用事件

```py
def my_listener(event):
	print 'out:', event

d.add_listener(my_listener, atx.EVENT_SCREENSHOT)
d.screenshot()

# expect output:
# out: HookEvent(flag=8, args=(), kwargs={})
```

## Other methods 其他的方法
ATX对安卓手机的所有操作(eg: click, swipe) 都是通过这个库 <https://github.com/openatx/atx-uiautomator> 实现的
通过 `d.uiautomator` 可以获取到该库的实例，使用该库上提到的所有方法。

iOS的所有的操作则是通过<https://github.com/openatx/facebook-wda>这个库与WDA交互完成的。
其中 `d.session` 对应 `wda.Session` 对象

比如想获取屏幕的大小，库中提到的方法是`Session.window_size()`,换到ATX中是`d.session.window_size()`