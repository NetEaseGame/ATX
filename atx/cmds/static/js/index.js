/* Javascript */
var M = {};

new Vue({
  el: '#main-content',
  data: {
    landscape: false,
  },
  methods: {
    toggleLandscape: function() {
      this.landscape = !this.landscape;
    }
  },
})

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

  // Initial global value for blockly images
  window.blocklyBaseURL = 'http://127.0.0.1:10010/static_imgs/';
  window.blocklyImageList = [['haha.png', 'screenshot-0.0.6.png']]

  $.getJSON('/api/images', function(res){
    window.blocklyImageList = res.images;
    window.blocklyBaseURL = res.baseURL;
  })


  function changeRunningStatus(status, message){
    M.runStatus = status;
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
      ws.send(JSON.stringify({command: "refresh"}))
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
          $('#btn-image-refresh').notify(
            '已刷新',
            {className: 'success', position: 'right'}
          );
          break;
        case 'run':
          changeRunningStatus(data.status, data.notify);
          break;
        case 'stop':
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
          var $console = $('pre.console');
          var text = $console.html();
          $console.text($console.html() + data.output);
          $console.scrollTop($console.prop('scrollHeight'))
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
    console.log("Click play")
    M.workspace.traceOn(true); // enable step run
    var g = generateCode(workspace);
    var isPlay = M.runStatus == 'running';
    sendWebsocket({command: (isPlay ? 'stop' : 'run'), code: g.pythonDebugText})
  })

  $('#btn-image-refresh').click(function(event){
    event.preventDefault();
    sendWebsocket({command: 'refresh'})
  })

  $('.btn-clear-console').click(function(){
    $('pre.console').text('');
  })

  $('li[role=presentation]').click(function(){
    var text = $.trim($(this).text());
    M.workspace.setVisible(text === 'Blockly');
    Blockly.fireUiEvent(window, 'resize');
  })

  $('#btn-save-screen').click(function(){
    var filename = window.prompt('保存的文件名, 不需要输入.png扩展名');
    if (!filename){
      return;
    }
    filename = filename + '.png';
    $.ajax({
      url: '/images/screenshot',
      method: 'POST',
      data: {
        raw_image: M.canvas.toDataURL(), // FIXME(ssx): use server image is just ok
        filename: filename,
      },
      success: function(res){
        console.log(res)
        $.notify('图片保存成功', 'success')
      },
      error: function(err){
        console.log(err)
        $.notify('图片保存失败，打开调试窗口查看具体问题')
      },
    })
  })

  $('#btn-refresh-screen').click(function(){
    M.screenURL = '/images/screenshot?v=t' + new Date().getTime();
    var $this = $(this);
    $this.notify('Refreshing', {className: 'info', position: 'top'})
    $this.prop('disabled', true);

    loadCanvasImage(M.canvas, M.screenURL, function(err){
      if (err){
        $this.notify(err, 'error')
      }
      $this.prop('disabled', false);
    })
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
    url = url || M.screenURL;
    imageObj.crossOrigin="anonymous";
    imageObj.onload = function(){
      M.screenRatio = canvas.width/imageObj.width; // global
      var height = Math.floor(M.screenRatio*imageObj.height);
      canvas.setAttribute('height', height);
      context.drawImage(imageObj, 0, 0, canvas.width, canvas.height);
      var $wrapper = $(canvas).parent('div')
      $wrapper.height(height);
      if (callback) {
        callback()
      }
    }
    imageObj.onerror = function(){
      if (callback){
        callback("Refresh failed.")
      }
    }
    imageObj.src = url;
  }

  function writeMessage(canvas, message) {
    var context = canvas.getContext('2d');
    context.font = '18pt Calibri';
    context.fillStyle = 'black';
    context.fillText(message, 10, 25);
  }

  function onResize(){
    var blocklyDivHeight = getPageHeight() - $("#blocklyDiv").offset().top;
    console.log($("#console-left").height())
    if (!$('#console-left').is(':hidden')){
      blocklyDivHeight -= $("#console-left").height() + 20;
    }
    console.log("blockly height:", blocklyDivHeight)
    $('#blocklyDiv').height(blocklyDivHeight-5);
    Blockly.svgResize(M.workspace);
    resizeCanvas(M.canvas);
  }

  M.canvas = document.getElementById('canvas');
  M.screenURL = '/images/screenshot?v=t0';
  window.addEventListener('resize', onResize, false);
  onResize();

  function getMousePos(canvas, evt) {
    var rect = canvas.getBoundingClientRect();
    return {
      x: Math.floor((evt.clientX - rect.left) / M.screenRatio),
      y: Math.floor((evt.clientY - rect.top) / M.screenRatio),
    };
  }

  var canvas = document.getElementById('canvas');
  canvas.addEventListener('mousemove', function(evt) {
    var mousePos = getMousePos(canvas, evt);
    var message = 'Mouse position: ' + mousePos.x + ',' + mousePos.y;
    // writeMessage(canvas, message);
    $('.status-bar>span').text(message);
    // console.log(message);
  }, false);

  // $("#console-left").hide(function(){
    // console.log("HE")
    // onResize(); //Blockly.fireUiEvent(window, 'resize');
  // });

  //------------ canvas overlay parts ------------//
  function getCanvasPos(x, y) {
      var rect = canvas.getBoundingClientRect();
      var left = M.screenRatio * x + rect.left,
          top  = M.screenRatio * y + rect.top;
      return {left, top};
  }

  var overlays = {
    "atx_click" : {
      $el: $('<div>').addClass('point').hide().appendTo('body'),
      update: function(data){
        var pos = getCanvasPos(data.x, data.y);
        this.$el.css('left', pos.left+'px')
                .css('top', pos.top+'px');
      },
    },
    "atx_click_image" : {
      $el: $('<div>').addClass('image-rect').hide().appendTo('body')
          .append($('<div>').addClass('point')),
      update: function(data){
        var p1 = getCanvasPos(data.x1, data.y1),
            p2 = getCanvasPos(data.x2, data.y2),
            width = p2.left - p1.left,
            height = p2.top - p1.top;
        this.$el.css('left', p1.left+'px')
                .css('top', p1.top+'px')
                .css('width', width+'px')
                .css('height', height+'px');
        this.$el.children().css('left', (data.c.x+50)+'%').css('top', (data.c.y+50)+'%');
      },
    },
    "atx_click_ui" : {
      $el: $('<div>').addClass('ui-rect').hide().appendTo('body'),
      update: function(data){
        var p1 = getCanvasPos(data.x1, data.y1),
            p2 = getCanvasPos(data.x2, data.y2),
            width = p2.left - p1.left,
            height = p2.top - p1.top;
        this.$el.css('left', p1.left+'px')
                .css('top', p1.top+'px')
                .css('width', width+'px')
                .css('height', height+'px');
      },
    },
    "atx_swipe" : {
      $el: $('<div>').hide().appendTo('body')
          .append($('<div>').addClass('point')) // start point
          .append($('<div>').addClass('point')) // end point
          .append($('<svg>')), // line from start to end
      update: function(data){
        var p1 = getCanvasPos(data.x1, data.y1),
            p2 = getCanvasPos(data.x2, data.y2);
        this.$el.children('div:first').css('left', p1.left+'px').css('top', p1.top+'px');
        this.$el.children('div:last').css('left', p2.left+'px').css('top', p2.top+'px');
        this.$el.children('svg').html(''); // TODO line up
      },
    },
  };

  //------------ canvas do different things for different block ------------//

  // selected is atx_click
  canvas.addEventListener('click', function(evt){
    var blk = Blockly.selected;
    if (blk == null || blk.type != 'atx_click') {
      return;
    }
    // update model in blockly
    var pos = getMousePos(this, evt);
    blk.setFieldValue(pos.x, 'X');
    blk.setFieldValue(pos.y, 'Y');
    // update point position
    var $point = overlays['atx_click'].$el;
    $point.css('left', evt.pageX+'px').css('top', evt.pageY+'px');
  });

  // selected is atx_click_image
  var rect_bounds = {start: null, end: null};
  canvas.addEventListener('mousedown', function(evt){
    var blk = Blockly.selected;
    if (blk == null || blk.type != 'atx_click_image') {
      return;
    }
    rect_bounds.start = evt;
    rect_bounds.end = null;
  });
  canvas.addEventListener('mousemove', function(evt){
    // ignore fake move
    if (evt.movementX == 0 && evt.movementY == 0) {
      return;
    }
    var blk = Blockly.selected;
    if (blk == null || blk.type != 'atx_click_image' || rect_bounds.start == null) {
      return;
    }
    rect_bounds.end = evt;
    // update model in blockly
    var pat_conn = blk.getInput('ATX_PATTERN').connection.targetConnection;
    if (pat_conn == null) { return;}
    var pat_blk = pat_conn.sourceBlock_;
    if (pat_blk.type != 'atx_image_pattern') {return;}
    var img_conn = pat_blk.getInput('FILENAME').connection.targetConnection;
    if (img_conn == null) { return;}
    var img_blk = img_conn.sourceBlock_;
    if (img_blk.type != 'atx_image_crop_preview') {return; }
    var crop_conn = img_blk.getInput('IMAGE_CROP').connection.targetConnection;
    if (crop_conn == null) { return;}
    var crop_blk = crop_conn.sourceBlock_,
        start_pos = getMousePos(this, rect_bounds.start),
        end_pos = getMousePos(this, rect_bounds.end);
    crop_blk.setFieldValue(start_pos.x, 'LEFT');
    crop_blk.setFieldValue(start_pos.y, 'TOP');
    crop_blk.setFieldValue(end_pos.x - start_pos.x, 'WIDTH');
    crop_blk.setFieldValue(end_pos.y - start_pos.y, 'HEIGHT');
    pat_blk.setFieldValue(0, 'OX');
    pat_blk.setFieldValue(0, 'OY');

    // update image-rect position
    var $rect = overlays['atx_click_image'].$el,
        left = rect_bounds.start.pageX,
        top = rect_bounds.start.pageY,
        width = Math.max(rect_bounds.end.pageX - left, 10),
        height = Math.max(rect_bounds.end.pageY - top, 10);
    $rect.css('left', left+'px')
         .css('top', top+'px')
         .css('width', width+'px')
         .css('height', height+'px');
    $rect.children().css('left', '50%').css('top', '50%');
  });
  canvas.addEventListener('mouseup', function(evt){
    var blk = Blockly.selected;
    // mouseup event should only be triggered when there happened mousemove
    if (blk == null || blk.type != 'atx_click_image' || rect_bounds.end == null) {
      return;
    }
    rect_bounds.start = null;
  });
  canvas.addEventListener('mouseout', function(evt){
    var blk = Blockly.selected;
    // mouseout is same as mouseup
    if (blk == null || blk.type != 'atx_click_image' || rect_bounds.end == null) {
      return;
    }
    rect_bounds.start = null;
  });
  canvas.addEventListener('click', function(evt){
    var blk = Blockly.selected;
    // click event should only be triggered when there's no mousemove happened.
    if (blk == null || blk.type != 'atx_click_image' || rect_bounds.end != null) {
      return;
    }
    rect_bounds.start = null;
    // update model in blockly
    var pat_conn = blk.getInput('ATX_PATTERN').connection.targetConnection;
    if (pat_conn == null) { return;}
    var pat_blk = pat_conn.sourceBlock_;

    // update image-rect point position
    var $rect = overlays['atx_click_image'].$el,
        pos = $rect.position(),
        x = pos.left,
        y = pos.top,
        w = $rect.width(),
        h = $rect.height(),
        cx = x + w/2,
        cy = y + h/2,
        ox = parseInt((evt.pageX - cx)/w * 100),
        oy = parseInt((evt.pageY - cy)/h * 100),
        $point = $rect.children();
    pat_blk.setFieldValue(ox, 'OX');
    pat_blk.setFieldValue(oy, 'OY');
    $point.css('left', (50+ox)+'%').css('top', (50+oy)+'%');
  });

  // TODO selected is atx_click_ui

  // TODO selected is atx_swipe

  //------------ canvas show rect/points for special block ------------//
  function getBlockOverlayData(blk) {
    switch (blk.type) {
      // return {x, y}
      case 'atx_click':
        var x = parseInt(blk.getFieldValue('X')),
            y = parseInt(blk.getFieldValue('Y'));
        if (x != null && y != null) {
          return {x, y};
        } else {
          return null;
        }
      // return {x1, y1, x2, y2, c}
      case 'atx_click_image':
        var pat_conn = blk.getInput('ATX_PATTERN').connection.targetConnection;
        if (pat_conn == null) { return null;}
        var pat_blk = pat_conn.sourceBlock_;
        if (pat_blk.type != 'atx_image_pattern') {return null;}
        var img_conn = pat_blk.getInput('FILENAME').connection.targetConnection;
        if (img_conn == null) { return null;}
        var img_blk = img_conn.sourceBlock_;
        if (img_blk.type != 'atx_image_crop_preview') {return null;}
        var crop_conn = img_blk.getInput('IMAGE_CROP').connection.targetConnection;
        if (crop_conn == null) { return null;}
        var imagename = img_blk.getFieldValue('IMAGE'),
            crop_blk = crop_conn.sourceBlock_,
            left = parseInt(crop_blk.getFieldValue('LEFT')),
            top = parseInt(crop_blk.getFieldValue('TOP')),
            width = parseInt(crop_blk.getFieldValue('WIDTH')),
            height = parseInt(crop_blk.getFieldValue('HEIGHT')),
            ox = parseInt(pat_blk.getFieldValue('OX')),
            oy = parseInt(pat_blk.getFieldValue('OY'));
            return {x1: left, y1: top, x2: left+width, y2: top+height, c:{x:ox, y:oy}};
      // return {x1, y1, x2, y2}
      case 'atx_click_ui':
      // return {x1, y1, x2, y2}
      case 'atx_swipe':
      default:
        return null;
    }
  }

  function hideOverlayPart(type) {
    if (!overlays.hasOwnProperty(type)) {return;}
    var obj = overlays[type];
    obj.$el.hide();
  }

  function showOverlayPart(type, blk) {
    if (!overlays.hasOwnProperty(type)) {return;}
    var obj = overlays[type];
    var data = getBlockOverlayData(blk)
    if (data != null) {
      obj.update(data);
      obj.$el.show();
    }
  }

  function onSelectedChange(evt){
    if (evt.element != 'selected') {
      return;
    }
    if (evt.oldValue != null) {
      var oldblk = workspace.getBlockById(evt.oldValue);
      hideOverlayPart(oldblk.type);
    }
    if (evt.newValue != null) {
      var newblk = workspace.getBlockById(evt.newValue);
      showOverlayPart(newblk.type, newblk);
    }
  }
  workspace.addChangeListener(onSelectedChange);

})
