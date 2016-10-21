# Report
利用此插件可以在ATX自动化跑完之后，自动生成HTML报告，方便查看每一步的执行情况

## Usage
```py
import atx
from atx.ext.report import Report # report lib


d = atx.connect()
rp = Report(d, save_dir='report')
rp.patch_uiautomator() # for android UI test record (optional)

rp.info("Test started") # or rp.info("Test started", screenshot=d.screenshot())
d.click(200, 200)

# keep screenshot when test fails
rp.error("Oh no.", screenshot=d.screenshot())

# assert operations
# param screenshot can be type <None|True|False|PIL.Image>
# 	set to None means only take screenshot when assert fails.
#	this is also same to other assert functions
rp.assert_equal(1, 2, desc="Hi", screenshot=True, safe=True)

# assert android ui exists
rp.assert_ui_exists(d(text='Hello'), desc='Hello UI')

# close and generate report
rp.close()
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