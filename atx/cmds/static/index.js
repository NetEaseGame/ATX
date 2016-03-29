/* Javascript */
var M = {};

$(function(){
  var blocklyDiv = document.getElementById('blocklyDiv');
  var workspace = Blockly.inject(blocklyDiv,
    {toolbox: document.getElementById('toolbox')});
  Blockly.Python.STATEMENT_PREFIX = 'highlight_block(%1);\n';
  Blockly.Python.addReservedWords('highlight_block');
  M.workspace = workspace;

  var RUN_BUTTON_TEXT = {
    'ready': '<span class="glyphicon glyphicon-play"></span> 运行</a>',
    'running': '<span class="glyphicon glyphicon-stop"></span> 运行中</a>',
  }

  function changeRunningStatus(status){
    var $play = $('a[href=#play]');
    if (status === 'ready'){
      $play.notify('运行结束', {className: 'success', position: 'top'});
    }
    $play.html(RUN_BUTTON_TEXT[status]);
  }

  (function(){
    var ws = new WebSocket('ws://'+location.host+'/ws')
    M.ws = ws;

    ws.onopen = function(){
      ws.send("refresh")
    };
    ws.onmessage = function(evt){
      try {
        var data = JSON.parse(evt.data)
        console.log(evt.data);
        switch(data.type){
        case 'image_list':
          M.images = data.data;
          $('#btn-imgrefresh').notify(
            '已刷新',
            {className: 'success', position: 'right'}
          );
          break;
        case 'run':
          changeRunningStatus(data.status);
          break;
        case 'highlight':
          console.log(data.id)
          var id = data.id;
          workspace.highlightBlock(id)
          break;
        default:
          console.log("No match")
        }
      }
      catch(err){
        console.log(err, evt.data)
      }
    };
    ws.onerror = function(err){
      $.notify(err);
      console.error(err)
    };
    ws.onclose = function(){
      console.log("Closed");
      $.notify(
        '与后台通信连接断开 !!!', 
        {position: 'top center', className: 'error'})
    };

  })()

  function generateCode(workspace) {
    var xml = Blockly.Xml.workspaceToDom(workspace);
    Blockly.Python.STATEMENT_PREFIX = '';
    var pythonText = Blockly.Python.workspaceToCode(workspace);

    Blockly.Python.STATEMENT_PREFIX = 'highlight_block(%1);\n';
    var pythonDebugText = Blockly.Python.workspaceToCode(workspace);

    return {
      xmlText: Blockly.Xml.domToPrettyText(xml),
      pythonText: pythonText,
      pythonDebugText: pythonDebugText,
    }
  }

  function saveWorkspace() {
    var $this = $('a[href=#save]');
    var originHtml = $this.html();
    $this.html('<span class="glyphicon glyphicon-floppy-open"></span> 保存中')
    
    var g = generateCode(workspace);
    $.ajax({
      url: '/workspace',
      method: 'POST',
      data: {'xml_text': g.xmlText, 'python_text': g.pythonDebugText},
      success: function(e){
        console.log(e);
        // $this.html('<span class="glyphicon glyphicon-floppy-open"></span> 已保存')
        $('a[href=#save]').notify('保存成功',
          {className: 'success', position: 'left', autoHideDelay: 700});
      },
      error: function(e){
        console.log(e);
        $this.notify(e.responseText || '保存失败，请检查服务器连接是否正常', 
          {className: 'warn', elementPosition: 'left', autoHideDelay: 5000});
      },
      complete: function(){
        $this.html(originHtml)
      }
    })
  }

  function updateGenerate(workspace) {
    var g = generateCode(workspace);
    console.log(g.pythonText);
    $('.code-python').text(g.pythonText);
  }

  function updateFunction(event) {
    updateGenerate(workspace)
    if (updateFunction.timeoutKey) {
      clearTimeout(updateFunction.timeoutKey);
    }
    updateFunction.timeoutKey = setTimeout(saveWorkspace, 1400);
  }

  function restoreWorkspace() {
    $.get('/workspace')
      .success(function(res){
        var xml = Blockly.Xml.textToDom(res.xml_text);
        Blockly.Xml.domToWorkspace(workspace, xml);
        updateGenerate(workspace)
      })
      .error(function(res){
        alert(res.responseText);
      })
      .complete(function(){
        setTimeout(function(){
          workspace.addChangeListener(updateFunction);
        }, 700)
      })
  }

  restoreWorkspace();

  $('a[href=#save]').click(function(event){
    event.preventDefault();
    saveWorkspace()
  })

  $('a[href=#play]').click(function(event){
    event.preventDefault();
    M.workspace.traceOn(true); // enable step run
    M.ws.send('run');
  })

  $('#btn-imgrefresh').click(function(event){
    event.preventDefault();
    M.ws.send('refresh');
  })


  $('.fancybox').fancybox()

  function getPageHeight(){
    return document.documentElement.clientHeight;
  }

  function onResize(){
    var blocklyDivHeight = getPageHeight() - $("#blocklyDiv").offset().top;
    $('#blocklyDiv').height(blocklyDivHeight-5);
  }
  window.addEventListener('resize', onResize, false);
  onResize();
})

// var workspace = Blockly.inject('blocklyDiv',
//       {toolbox: document.getElementById('toolbox')});