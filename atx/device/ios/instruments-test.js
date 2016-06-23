#import "mechanic.js"

var $ = $ || mechanic;

(function($) {
  var target = UIATarget.localTarget();
  var app = target.frontMostApp();

  $.extend($, {
    debug: UIALogger.logMessage,
    cmd: function(path, args, timeout) {
      return target.host().performTaskWithPathArgumentsTimeout(path, args, timeout);
    },
    delay: function(seconds) {
      target.delay(seconds);
    },
    orientation: function(orientation) {
      if (orientation === undefined || orientation === null) return target.deviceOrientation();
      else target.setDeviceOrientation(orientation);
    },
  })


  $.extend($, {
    error: function(s) {
      UIALogger.logError(s);
    },
    warn: function(s) {
      UIALogger.logWarning(s);
    },
    debug: function(s) {
      UIALogger.logDebug(s);
    },
    message: function(s) {
      UIALogger.logMessage(s);
    },
    rotate: function(options) {
      target.rotateWithOptions(options);
    },
    typeString: function(str){
      target.frontMostApp().keyboard().typeString(str);
    }
  })
})(mechanic);

// var window = app.mainWindow();
// //target.logElementTree();
// var host = target.host();
var target = UIATarget.localTarget();
var app = target.frontMostApp();

// $.debug("Hello" + JSON.stringify(target.rect()))
$.message("Hello message")

while (true) {
  $.message("Wait for command")
  var result = $.cmd('./bootstrap.sh', ['get'], 50);
  if (! result.stdout) { // == 15) {
    continue;
  }
  $.debug("exitCode: " + result.exitCode);
  $.debug("stdout: " + result.stdout);
  $.debug("stderr: " + result.stderr);
  // $.message("delay 1s")
  // $.delay(1)

  if (result.exitCode == 0) {
    try {
      var req = JSON.parse(result.stdout);
      var rawRes = eval(req.data.command);
      var res = JSON.stringify(rawRes);
      $.debug("Result: " + res);
      $.cmd('./bootstrap.sh', ['put', req.id, res], 5);
    } catch (err) {
      $.debug("Error: " + err.message);
      $.cmd('./bootstrap.sh', ['put', req.id, JSON.stringify("error:" + err.message)], 5);
    }
  }
}