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

String.prototype.trim = function(char, type) {
  if (char) {
    if (type == 'left') {
      return this.replace(new RegExp('^\\' + char + '+', 'g'), '');
    } else if (type == 'right') {
      return this.replace(new RegExp('\\' + char + '+$', 'g'), '');
    }
    return this.replace(new RegExp('^\\' + char + '+|\\' + char + '+$', 'g'), '');
  }
  return this.replace(/^\s+|\s+$/g, '');
};

var target = UIATarget.localTarget();
var app = target.frontMostApp();

// $.debug("Hello" + JSON.stringify(target.rect()))
$.message("Instruments is ready")

while (true) {
  $.message("Wait for command")
  var result = $.cmd('./bootstrap.sh', ['get'], 50);
  if (!result.stdout.trim()) { // == 15) {
    continue;
  }
  $.debug("exitCode: " + result.exitCode);
  $.debug("stdout: " + result.stdout);
  $.debug("stderr: " + result.stderr);
  // $.message("delay 1s")
  // $.delay(1)

  if (result.exitCode !== 0) {
    continue
  }
  
  try {
    var req = JSON.parse(result.stdout);
    if (!req.id){
      $.warn("Reqest need ID");
      continue
    }
    var rawRes = eval(req.data.command);
    if (req.data.nowait) {
      continue;
    }

    var res = JSON.stringify(rawRes);
    $.debug("Result: " + res);
    var ret = $.cmd('./bootstrap.sh', ['put', req.id, res], 5);
    $.debug("Result exitCode: " + ret.exitCode);
    $.debug("Result stdout: " + ret.stdout);
    $.debug("Result stderr: " + ret.stderr);
  } catch (err) {
    $.error("Error: " + err.message);
    // $.cmd('./bootstrap.sh', ['put', req.id, JSON.stringify("error:" + err.message)], 5);
  }
}