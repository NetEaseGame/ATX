## iOS Automation
iOS因为其管理的严格以及文档的困乏，使得其自动化实施起来困难重重。然而iOS的市场占有率又这么高，所以也只能硬着头皮去读Apple网站下一堆晦涩的文档，一边摸索，一边记录。


## 相关工具安装
毕竟iPhone是苹果的产品，所以搞iOS测试还是得有台苹果电脑的好。

先安装 brew, 如何安装参考 <http://brew.sh>

```
$ brew install libmobiledevice
$ brew install homebrew/fuse/ifuse
```


安装工具用于解析ipa包

```
$ pip install pyipa
```

## Common issues
- How to keep iPhone screen on ?

	1. 显示与亮度 调到最低
	2. 通用/自动锁定 改成**永不**

- 其他90%的问题

	1. 更新XCode
	1. 重启Mac
	1. 重启iPhone都可以解决

## Articles
- [2012年的文章关于UIAutomation, 4年的时间也不会让它褪色](http://blog.manbolo.com/2012/04/08/ios-automated-tests-with-uiautomation)

## Authors
codeskyblue@gmail.com 2016.06