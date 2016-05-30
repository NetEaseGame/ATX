## API documentation
其实看ReadTheDocs上的文档更好一点，这里也不打算列出来多少接口 [Documentation on ReadTheDocs](http://atx.readthedocs.org/en/latest/?badge=latest)

### 连接设备
`connect(udid, **kwargs)`

对于安卓设备常见连接方法

```
connect() # only one device
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

Returns

PIL.Image

### 坐标点击
`click(x, y)`

image support string or pillow image

Parameters

Name      | Type      | Description
----------|-----------|------------
x, y      | int       | 坐标值

Example

```
click(20， 30）
```

### 其他接口


## 批量运行脚本
推荐用unittest, 它是python自身的一个测试框架(其他出色的也有nose, pytest) 等等，看个人喜好

	```py
	# coding: utf-8

	import unittest
	import atx

	d = atx.connect()

	class SimpleTestCase(unittest.TestCase):
	    def setUp(self):
	        name = 'com.netease.txx'
	        d.stop_app(name).start_app(name)

	    def test_login(self):
	        d.click_image("confirm.png")
	        d.click_image("enter-game.png")
	        with d.watch('Enter game', 20) as w:
	            w.on("user.png").quit()


	if __name__ == '__main__':
	    unittest.main()
	```
	