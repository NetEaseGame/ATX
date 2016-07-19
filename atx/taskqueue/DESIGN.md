# taskqueue
instruments与外部的交互

## 需要实现的功能
1. get
2. done
3. put

创建任务 http method POST

```
python -m atx.taskqueue --room ${UDID} post '{"command": "target.rect().size"}'
# Expect output
# {"id": "59004fb5-3858-11e6-be42-985aebd521c0"}
```

接收任务 http method GET

```
python -m atx.taskqueue --room ${UDID} get --timeout 10
# Expect output
# {"data": {"command": "target.rect().size"}, "id": "5a20c5b0-3858-11e6-9c09-985aebd521c0"}
```

完成任务, http method PUT

```
python -m atx.taskqueue --room ${UDID} put '{"id": "5a20c5b0-3858-11e6-9c09-985aebd521c0", "result": "1024x968"}'
# Expect output
# Success
```

获取结果, http method PATCH

20s钟后如果没有结果，就超时

```
python -m atx.taskqueue --room ${UDID} retr --timeout 10.0 "5a20c5b0-3858-11e6-9c09-985aebd521c0"
# Expect output
# "1024x968"
```


清空队列, http method DELETE

```
python -m atx.taskqueue --room ${UDID} clean
```