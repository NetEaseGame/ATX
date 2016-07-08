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
