# taskqueue
instruments与外部的交互

## 需要实现的功能
1. get
2. done
3. put

```
$ python -matx.taskqueue --room ${UDID} put '{id: "12", result: true, action: "target.click(10, 20)"}'
Success

$ python -matx.taskqueue --room ${UDID} get
{id: "12", result: true, action: "target.click(10, 20)"}

$ python -matx.taskqueue --room ${UDID} done '{id: "12", result: "1234551"}'
Success
```

Or use api to call

```
import atx.taskqueue as tqueue


result = tqueue.put(udid, action='target.click(10, 10)', result=True)
print result
```

expect

"ok"
