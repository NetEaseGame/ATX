/* Javascript */
$(function(){
  var blocklyDiv = document.getElementById('blocklyDiv');
  var workspace = Blockly.inject(blocklyDiv,
    {toolbox: document.getElementById('toolbox')});

  $('.fancybox').fancybox()
})

// var workspace = Blockly.inject('blocklyDiv',
//       {toolbox: document.getElementById('toolbox')});