# DESIGN
## Watch
循环检测，当某事件发生时，执行特定操作

```
from atx import script_utils as wu
```

只触发一次效果
```
btn_login = d(text=u'登陆', className='Button')
if scu.once_exists(btn_login):
	btn_login.click()

# same sa
trigged = False
if not trigged and btn_login.exists:
	trigged = True
	btn_login.click()
```

存在并点击效果
```
scu.safe_click(d(text='Update'))

# same as
btn_update = d(text='Update')
if btn_update.exists:
	btn_update.click()
```

Timeout效果

```
with scu.while_timeout(50, safe=True):
	pass
	# raise scu.Continue()
	# raise scu.Break()

# same as
safe = True
deadline = time.time() + 50
while time.time() < deadline:
	pass
	# continue
	# break
else:
	if not safe:
		raise RuntimeError("while timeout')
```

