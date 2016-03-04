# Airtest

# 代码重构中（不要着急）

## 为什么要重构
很多的代码不符合pytohn编码规范, 还有一些很冗余的功能夹杂在里面，很不好维护。
为了能够重现该软件昔日的光芒，是时候擦亮代码，重出江湖了。

## 主要更新内容
* 截图方式从adb screencap转成使用uiautomator

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
