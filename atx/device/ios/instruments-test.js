/* The usage is some like jQuery */

var mechanic = (function() {
  var target = UIATarget.localTarget();
  var app = target.frontMostApp(),
    window = app.mainWindow(),
    emptyArray = [],
    slice = emptyArray.slice;

  target.setTimeout(0);

  function $() {}

  $.extend = function(target) {
    var key;
    slice.call(arguments, 1).forEach(function(source) {
      for (key in source) target[key] = source[key];
    });
    return target;
  };

  $.inArray = function(elem, array, i) {
    return emptyArray.indexOf.call(array, elem, i);
  };

  $.map = function(elements, callback) {
    var value, values = [],
      i, key;
    if (likeArray(elements)) {
      for (i = 0; i < elements.length; i++) {
        value = callback(elements[i], i);
        if (value != null) values.push(value);
      }
    } else {
      for (key in elements) {
        value = callback(elements[key], key);
        if (value != null) values.push(value);
      }
    }
    return flatten(values);
  };

  $.each = function(elements, callback) {
    var i, key;
    if (likeArray(elements)) {
      for (i = 0; i < elements.length; i++) {
        if (callback.call(elements[i], i, elements[i]) === false) return elements;
      }
    } else {
      for (key in elements) {
        if (callback.call(elements[key], key, elements[key]) === false) return elements;
      }
    }
    return elements;
  };

  return $;
})();


var $ = $ || mechanic;

(function($) {
  var target = UIATarget.localTarget();

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
  })
})(mechanic);

// var app = target.frontMostApp();
// var window = app.mainWindow();
// //target.logElementTree();
// var host = target.host();
var target = UIATarget.localTarget();

// $.debug("Hello" + JSON.stringify(target.rect()))
$.message("Hello message")

while (true) {
  $.message("Wait for command")
  var result = $.cmd('/usr/bin/head', ['-n1', 'test.pipe'], 10);
  $.debug("exitCode: " + result.exitCode);
  $.debug("stdout: " + result.stdout);
  $.debug("stderr: " + result.stderr);
  // $.message("delay 1s")
  // $.delay(1)

  if (result.exitCode == 0) {
    var rawRes = eval(result.stdout);
    var res = JSON.stringify(rawRes);
    $.cmd('./write_pipe.sh', [res], 5);
  }
}
// $.delay(10)
// target.tap({x: 357, y: 350})
// $.delay(10)