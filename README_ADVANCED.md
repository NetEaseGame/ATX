# Advanced
Read this doc before you read [README.md](README.md)

## How to catch click_image errors

```py
import atx

d = atx.connect()
try:
    d.click_image('button.png', timeout=1)
except atx.Error as e:
    print e.data
```

Expect result if button.png is not found, you will find matched is False

```
FindPoint(pos=(115, 1014), confidence=0.5189774632453918, method='template', matched=False)
```
