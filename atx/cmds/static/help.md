# 备忘

## FAQ

1. 如何使用代码添加组件到Canvas

```
var xml = Blockly.Xml.textToDom('<xml><block type="text" x="100" y="50"><field name="TEXT">123</field></block></xml>');
Blockly.Xml.domToWorkspace(xml, workspace);
```