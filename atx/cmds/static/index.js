/* Javascript */
$(function(){
  var blocklyDiv = document.getElementById('blocklyDiv');
  var workspace = Blockly.inject(blocklyDiv,
    {toolbox: document.getElementById('toolbox')});

  function updateFunction(event) {
    var code = Blockly.Python.workspaceToCode(workspace);
    console.log(code);
    $('#pythonCode').text(code);
  }
  workspace.addChangeListener(updateFunction);


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