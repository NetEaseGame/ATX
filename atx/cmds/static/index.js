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
    'running': '<span class="glyphicon glyphicon-stop"></span> 停止</a>',
  }

  function changeRunningStatus(status, message){
    var $play = $('a[href=#play]');
    if (message) {
      $play.notify(message, {className: 'success', position: 'top'});
    }
    if (status){
      $play.html(RUN_BUTTON_TEXT[status]);
    }
  }

  function connectWebsocket(){
    var ws = new WebSocket('ws://'+location.host+'/ws')
    M.ws = ws;

    ws.onopen = function(){
      // ws.send(JSON.stringify({command: "refresh"}))
      $.notify(
        '与后台通信连接成功!!!', 
        {position: 'top center', className: 'success'})
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
          changeRunningStatus(data.status, data.notify);
          break;
        case 'traceback':
          alert(data.output);
          break;
        case 'highlight':
          var id = data.id;
          workspace.highlightBlock(id)
          break;
        case 'console':
          // var text = $('pre.console').text();
          // var newText = text + data.output;
          var $console = $('pre.console');
          $console.text($console.text() + data.output);
          $console.scrollTop($console.height())
        default:
          console.log("No match data type: ", data.type)
        }
      }
      catch(err){
        console.log(err, evt.data)
      }
    };
    ws.onerror = function(err){
      // $.notify(err);
      // console.error(err)
    };
    ws.onclose = function(){
      console.log("Closed");
      $.notify(
        '与后台通信连接断开, 2s钟后重新连接 !!!', 
        {position: 'top center', className: 'error'})
      setTimeout(function(){
        connectWebsocket()
      }, 2000)
    };
  }
  connectWebsocket()

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

  function saveWorkspace(callback) {
    var $this = $('a[href=#save]');
    var originHtml = $this.html();
    $this.html('<span class="glyphicon glyphicon-floppy-open"></span> 保存')
    
    var g = generateCode(workspace);
    $.ajax({
      url: '/workspace',
      method: 'POST',
      data: {'xml_text': g.xmlText, 'python_text': g.pythonText},
      success: function(e){
        // console.log(e);
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
        if (callback){
          callback(g)
        }
      }
    })
  }

  function updateGenerate(workspace) {
    var g = generateCode(workspace);
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

  function sendWebsocket(message){
    var data = JSON.stringify(message);
    M.ws.send(data);
  }

  $('a[href=#save]').click(function(event){
    event.preventDefault();
    saveWorkspace()
  })

  $('a[href=#play]').click(function(event){
    event.preventDefault();
    M.workspace.traceOn(true); // enable step run
    var g = generateCode(workspace);
    sendWebsocket({command: 'run', code: g.pythonDebugText})
    // saveWorkspace(function(g){
      // sendWebsocket({command: 'run', code: g.pythonDebugText})
    // });
  })

  $('#btn-imgrefresh').click(function(event){
    event.preventDefault();
    sendWebsocket({command: 'refresh'})
  })

  $('#btn-clearconsole').click(function(){
    $('pre.console').text('');
  })

  $('li[role=presentation]').click(function(){
    var text = $.trim($(this).text());
    M.workspace.setVisible(text === 'Blockly');
    Blockly.fireUiEvent(window, 'resize');
  })


  $('.fancybox').fancybox()

  function getPageHeight(){
    return document.documentElement.clientHeight;
  }

  function resizeCanvas(canvas){
    var width = $('#screen-wrapper').width();
    canvas.setAttribute('width', width);
    loadCanvasImage(canvas, M.screenURL);
  }

  function loadCanvasImage(canvas, url, callback){
    var context = canvas.getContext('2d')
    var imageObj = new Image();
    imageObj.onload = function(){
      M.screenRatio = canvas.width/imageObj.width; // global
      var height = Math.floor(M.screenRatio*imageObj.height);
      canvas.setAttribute('height', height);
      context.drawImage(imageObj, 0, 0, canvas.width, canvas.height);
      var $wrapper = $(canvas).parent('div')
      $wrapper.height(height);
    }
    imageObj.src = url;
  }

  function getMousePos(canvas, evt) {
    var rect = canvas.getBoundingClientRect();
    return {
      x: Math.floor((evt.clientX - rect.left) / M.screenRatio),
      y: Math.floor((evt.clientY - rect.top) / M.screenRatio),
    };
  }
  function writeMessage(canvas, message) {
    var context = canvas.getContext('2d');
    // context.clearRect(0, 0, canvas.width, canvas.height);
    context.font = '18pt Calibri';
    context.fillStyle = 'black';
    context.fillText(message, 10, 25);
  }

  function onResize(){
    var blocklyDivHeight = getPageHeight() - $("#blocklyDiv").offset().top;
    $('#blocklyDiv').height(blocklyDivHeight-5);

    var canvas = document.getElementById('canvas');
    resizeCanvas(canvas);
  }

  M.screenURL = 'http://www.html5canvastutorials.com/demos/assets/darth-vader.jpg';
  window.addEventListener('resize', onResize, false);
  onResize();

  var canvas = document.getElementById('canvas');
  canvas.addEventListener('mousemove', function(evt) {
    var mousePos = getMousePos(canvas, evt);
    var message = 'Mouse position: ' + mousePos.x + ',' + mousePos.y;
    // writeMessage(canvas, message);
    $('.status-bar>span').text(message);
    // console.log(message);
  }, false);

})

// var workspace = Blockly.inject('blocklyDiv',
//       {toolbox: document.getElementById('toolbox')});