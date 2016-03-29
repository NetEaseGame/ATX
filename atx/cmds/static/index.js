/* Javascript */
$(function(){
  var blocklyDiv = document.getElementById('blocklyDiv');
  var workspace = Blockly.inject(blocklyDiv,
    {toolbox: document.getElementById('toolbox')});
  
  var M = {};
  var ws = new WebSocket('ws://'+location.host+'/ws')

  ws.onopen = function(){
    ws.send("refresh")
  };
  ws.onmessage = function(evt){
    try {
      var data = JSON.parse(evt.data)
      M.images = data.images;
      console.log(M)
    }
    catch(err){
      console.log(err, evt.data)
    }
  };
  ws.onerror = function(err){
    console.error(err)
  };

  function generateCode(workspace) {
    var xml = Blockly.Xml.workspaceToDom(workspace);
    return {
      xmlText: Blockly.Xml.domToPrettyText(xml),
      pythonText: Blockly.Python.workspaceToCode(workspace)
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
      data: {'xml_text': g.xmlText, 'python_text': g.pythonText},
      success: function(e){
        console.log(e);
        // $this.html('<span class="glyphicon glyphicon-floppy-open"></span> 已保存')
        $.notify('保存成功',
          {className: 'success', autoHideDelay: 700});
      },
      error: function(e){
        console.log(e);
        $this.notify(e.responseText, 
          {className: 'warn', elementPosition: 'left', autoHideDelay: 5000});
      },
      complete: function(){
        $this.html(originHtml)
      }
    })
  }

  function updateGenerate(workspace) {
    var g = generateCode(workspace);
    $('#pythonCode').text(g.pythonText);
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
    alert("还没写 TODO")
  })

  $('#btn-imgrefresh').click(function(event){
    ws.send('refresh');
    $(this).notify('已刷新', 'success');
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