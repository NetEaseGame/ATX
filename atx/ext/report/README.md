# Report
利用此插件可以在ATX自动化跑完之后，自动生成HTML报告，方便查看每一步的执行情况

## Usage
```py
import atx
from atx.ext.report import Report # report lib


d = atx.connect()
rp = Report(d, save_dir='report')
rp.info("Test started")

d.click(200, 200)

# keep screenshot when test fails
rp.error("Oh no.", screenshot=d.screenshot())
```

After done, HTML report will be saved to report dir. with such directory

```
report/
  |-- index.html
  |-- result.json
  `-- images/
      |-- before_123123123123.png
      |-- ...
```

open `index.html` with browser.

![report](report.png)