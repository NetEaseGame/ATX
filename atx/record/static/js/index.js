Vue.filter('capitalize', function(s) {
  if (s == undefined || s == null) {return "";}
  return s.charAt(0).toUpperCase() + s.slice(1);
})

Vue.filter('camel', function(s) {
  if (s == undefined || s == null) {return "";}
  var str='', arr = s.split(/_/g);
  for (var i=0; i<arr.length; i++) {
    str += arr[i].charAt(0).toUpperCase() + arr[i].slice(1);
  }
  return str;
})

var FrameComponent = Vue.extend({
  props: {
    idx: {
      required: true,
      coerce : function (val) {return parseInt(val);}
    },
    scale: {},
  },
  computed: {
    options: function() {
      var d = {};
      for (var i = 0, n; i < this.uinodes.length; i++) {
        n = this.uinodes[i];
        d[i] = n.$xml.attr("class") + "-" + n.$xml.attr("index");
      }
      return d;
    },
    frameclass: function(){
      return {
        "highlight": this.idx == this.$parent.current,
        "skipped" : this.skipped,
      };
    },
    chopstyle: function(){
      var height = 50.0,
          scale = height / this.imgbound.height,
          width = this.imgbound.width * scale,
          left = this.imgbound.left * scale,
          top = this.imgbound.top * scale,
          $canvas = $("#canvas");
      return {
        "height": height + "px",
        "width" : width + "px",
        "background-image": "url(frames/" + this.data.status.screen + ")",
        "background-position" : "-" + left +"px -" + top + "px",
        "background-size" : $canvas.width()*scale/this.scale + "px " +
                            $canvas.height()*scale/this.scale + "px",
      };
    },
    overlapstyle: function(){
      return {
        "display" : (this.idx == this.$parent.current) ? "block" : "none",
        "position": "absolute",
        "left": this.uilayer.left + "px",
        "top": this.uilayer.top + "px",
        "width": this.uilayer.width + "px",
        "height": this.uilayer.height + "px",
      };
    },
    pointstyle: function(){
      var dia = 18;
      return {
        "width": dia + "px",
        "height": dia + "px",
        "border-radius" : dia + "px",
        "position": "absolute",
        "left": this.point.left * this.scale - dia*0.5 + "px",
        "top": this.point.top * this.scale - dia*0.5 + "px",
      };
    },
    rectstyle: function(){
      return {
        "width": this.imgbound.width * this.scale + "px",
        "height": this.imgbound.height * this.scale + "px",
        "left": this.imgbound.left* this.scale + "px",
        "top": this.imgbound.top* this.scale + "px",
      };
    },
    uiboxstyle: function() {
      var obj = this.uinodes[this.selected];
      if (undefined == obj) { return {};}
      return {
        "top": obj.top * this.scale + "px",
        "left": obj.left * this.scale + "px",
        "width": obj.width * this.scale + "px",
        "height": obj.height * this.scale + "px",
      };
    },
  },
  data: function(){
    var d = this.$parent.frames[this.idx];
    return {
      data: d,
      action: d.event.action,
      icon: "imgs/" + d.event.action + ".png",
      skipped: d.skip,
      uilayer: {left:0, top:0, width:0, height:0},
      // keyevent
      key: null,
      // click_ui
      uinodes: [],
      has_select: false,
      selected: null,
      // click
      has_point: 0,
      point: {left:100, top:200},
      // click_image
      has_image: false,
      imgbound: {left:100, top:100, width:100, height:100},
      imgdragging: false,
      imgresizing: false,
    }
  },
  template: "#frame-template",
  ready: function() {
    var self = this;

    console.log(self.data.event);
    // setup for different events.
    switch (self.data.event.action) {
      case "keyevent":
        self.key = self.data.event.args[0];
        break;
      case "touch":
      case "click":
        self.has_point= 1;
        var obj = self.data.event.args;
        self.point.left = obj[0];
        self.point.top = obj[1];
        break
      case "click_image":
        self.has_image = true;
        break;
      case "click_ui":
        self.has_select = true;
        self.selected = 0;
        break;
      default:
    }

    // load uixml for click_ui
    if (self.data.event.action == "click_ui") {
      $.ajax({
        url: 'frames/' + self.data['status']['uixml'],
        type: 'GET',
        dataType: 'xml',
        success: function(xmldata){
          $(xmldata).find('node').each(function(){
            var $xml = $(this);
            if ($xml.attr("clickable") != "true") {
              return;
            }
            var bounds = $xml.attr("bounds").match(/\d+/g),
                left = parseInt(bounds[0]),
                top = parseInt(bounds[1]),
                right = parseInt(bounds[2]),
                bottom = parseInt(bounds[3]),
                width = right - left,
                height = bottom - top;
            // skip fullscreen rects
            if (width == self.$parent.device.width && height == self.$parent.device.height){
              return;
            }
            var obj = {left:left, top:top, right:right, bottom:bottom,
              width:width, height:height, $xml:$xml};
            self.uinodes.push(obj);
          });
        },
        error: function(){
          console.log('Get uixml failed', self.data['status']['uixml']);
          self.uinodes = [];
        }
      });
    }

    // check skip
    if (self.data.skip) {
      self.skip();
    }
  },
  methods: {
    update: function(v){
      if (v == this.idx) {
        var canvas = document.getElementById("canvas");
        this.uilayer.left = $("#canvas").position().left;
        this.uilayer.top = $("#canvas").position().top;
        this.uilayer.width = canvas.width;
        this.uilayer.height = canvas.height;
      }
    },
    skip: function(event){
      if (event) {
        event.stopPropagation();
      }
      this.$parent.skipFrame(this.idx);
      this.skipped = true;
    },
    showMe: function(event) {
      // undo skip first
      this.$parent.unSkipFrame(this.idx);
      this.skipped = false;
      // change to this frame.
      this.$parent.current = this.idx;
    },
    selectUi: function(event) {
      console.log('onclick', this.data.event);
      var i = 0, n, left, right, top, bottom;
      for (; i < this.uinodes.length; i++) {
        n = this.uinodes[i];
        left = this.uilayer.left + n.left * this.scale;
        right = this.uilayer.left + n.right * this.scale;
        top = this.uilayer.top + n.top* this.scale;
        bottom = this.uilayer.top + n.bottom* this.scale;
        if ((event.pageX > left) && (event.pageX < right)
           && (event.pageY > top) && (event.pageY < bottom))
        {
          this.selected = i;
          break;
        }
      }
    },
    changePoint: function(event) {
      this.point.left = parseInt((event.pageX - this.uilayer.left) / this.scale);
      this.point.top = parseInt((event.pageY - this.uilayer.top) / this.scale);
    },
    startRect: function(event){
      this.imgdragging = true;
      this.imgbound.left = parseInt((event.pageX - this.uilayer.left) / this.scale);
      this.imgbound.top = parseInt((event.pageY - this.uilayer.top) / this.scale);
    },
    drawRect: function(event){
      if (this.imgdragging || this.imgresizing) {
        var right = parseInt((event.pageX - this.uilayer.left) / this.scale),
            bottom = parseInt((event.pageY - this.uilayer.top) / this.scale);
        this.imgbound.width = Math.min(600, Math.max(60, right - this.imgbound.left));
        this.imgbound.height = Math.min(600, Math.max(60, bottom - this.imgbound.top));
      }
    },
    stopRect: function(event){
      if (this.imgdragging) {
        this.imgdragging = false;
      }
      if (this.imgresizing) {
        this.imgresizing = false;
      }
    },
    outRect: function(event) {
      if (this.imgdragging || this.imgresizing) {
        if (event.pageX < this.uilayer.left ||
            event.pageX > this.uilayer.left + this.uilayer.width ||
            event.pageY < this.uilayer.top ||
            event.pageY > this.uilayer.top + this.uilayer.height)
        {
          this.imgdragging = false;
          this.imgresizing = false;
        }
      }
    },
    startResize: function(event) {
      event.stopPropagation();
      this.imgresizing = true;
    },
  },
});

Vue.component("frame", FrameComponent);

var SliderComponent = Vue.extend({
  props: {
    min : {
      default: 0,
      coerce : function (val) {return parseInt(val);}
    },
    max : {
      default: 100,
      coerce : function (val) {return parseInt(val);}
    },
    value:{
      default: 0,
      twoWay: true,
      coerce : function (val) {return parseInt(val);}
    }
  },
  template: "#v-slider-template",
  data : function() {
    return {
      dragging: false,
      left: 0,
      length: 1,
      barsize: 16,
    };
  },
  computed: {
    sliderbarstyle: function() {
      var h = this.barsize / 4,
          s = (this.barsize - h) / 2;
      return {
        "width" : "100%",
        "height" : h + "px",
        "margin-top": s + "px",
        "margin-bottom": s + "px",
      };
    },
    sliderpointstyle: function(){
      var width = 16, pos;
      if (this.max == this.min) {
        pos = 0;
      } else {
        pos = this.length * this.value/ (this.max - this.min);
      }
      return {
        "width": this.barsize + "px",
        "height": this.barsize + "px",
        "border-radius": this.barsize + "px",
        "left" : pos - 0.5*width + "px",
      };
    },
  },
  ready: function(){
    var $obj = $(this.$el);
    this.left = $obj.position().left;
    this.length = $obj.width();
  },
  methods: {
    startDrag: function(event) {
      this.dragging = true;
      this.setPos(event.pageX-this.left);
    },
    onDrag: function(event) {
      if (this.dragging) {
        this.setPos(event.pageX-this.left);
      }
    },
    stopDrag: function(){
      this.dragging = false;
    },
    setPos: function(pos) {
      console.log("setPos");
      pos = Math.max(0, Math.min(pos, this.length));
      this.value = Math.floor((this.max - this.min) * pos / this.length + 0.5);
    },
    update: function(v){
      var $obj = $(this.$el);
      this.left = $obj.position().left;
      this.length = $obj.width();
    }
  },
  watch: {
    'value' : function(v) {
      if (null == this.$point) {
        return;
      }
      this.update(v);
    }
  },
});

Vue.component("slider", SliderComponent);

var vm = new Vue({
  el : "#container",
  data : {
    device : {},
    // screen: {left: 0, top: 0, width:0, height: 0},
    frames : [],
    total_frames : 0,
    current: null,
    scale: 0.4,
    actions : {},
    showtoolbar: false,
  },
  created : function(){
    var self = this;
    self.image = new Image();
    self.image.addEventListener("load", function(){
      var canvas = document.getElementById("canvas");
      var ctx = canvas.getContext("2d");
      canvas.width = this.width * self.scale;
      canvas.height = this.height * self.scale;
      ctx.drawImage(self.image, 0, 0, canvas.width, canvas.height);
      self.updateChildren();
    })

    $.getJSON("frames/frames.json", function(data){
      self.device = data["device"];
      self.frames = data["frames"];
      self.total_frames = self.frames.length;
      if (self.total_frames > 0) {
        self.current = 0;
      }
    });
  },
  methods: {
    updateChildren: function() {
      for (var i=0; i<this.$children.length; i++){
        var child = this.$children[i];
        if (child.update != null) {
          child.update(this.current);
        }
      }
    },
    nextFrame: function() {
      var i = this.current+1, found = false;
      for (; i < this.total_frames; i++) {
        if (! this.frames[i].skip) {
          found = true;
          break
        }
      }
      if (found) {
        this.current = i;
      }
    },
    prevFrame: function() {
      var i = this.current-1, found = false;
      for (; i >= 0; i--) {
        if (! this.frames[i].skip) {
          found = true;
          break
        }
      }
      if (found) {
        this.current = i;
      }
    },
    skipFrame: function(idx) {
      this.frames[idx].skip = true;
    },
    unSkipFrame: function(idx) {
      delete this.frames[idx].skip;
    },
    toggleToolbar: function(){
      toolbar.toggle();
    },
  },
  watch: {
    "current" : function(newval, oldval){
      var self = this;
      var frame = this.frames[newval];
      self.image.src = "frames/" + frame["status"]["screen"];
    }
  },
});

var toolbar = new Vue({
  el: "#toolbar",
  data: {
    visible: false,
    tools : {
      "newClick" : {icon:"imgs/1_touch.png", },
      "newClickUi" : {icon:"imgs/1_touch.png",},
      "newClickImage" : {icon:"imgs/1_touch.png"},
      "newSwipe": {icon:"imgs/2_swipe.png"},
      "newText": {icon:"imgs/5_text.png"},
      "newKeyEvent": {icon:"imgs/6_keyboard.png"},
      "newServerCall": {icon:"imgs/7_command.png"},
      "newAssertExists": {icon:"imgs/4_exists.png"},
      "newWait": {icon:"imgs/3_wait.png"},
      "newIfElse": {icon:"imgs/9_what.png"},
      "newForLoop": {icon:"imgs/9_what.png"},
      "newWhileLoop": {icon:"imgs/9_what.png"},
    },
  },
  methods: {
    toggle : function(){
      this.visible = !this.visible;
    },
    click: function(what){
      var func = this[what];
      if (func) {func.call(this, what);}
    },
    newClick: function(what){console.log(what);},
    newClickUi: function(what){console.log(what);},
    newClickImage: function(what){console.log(what);},
    newSwipe: function(what){console.log(what);},
    newText: function(what){console.log(what);},
    newKeyEvent: function(what){console.log(what);},
    newServerCall: function(what){console.log(what);},
    newAssertExists: function(what){console.log(what);},
    newWait: function(what){console.log(what);},
    newIfElse: function(what){console.log(what);},
    newForLoop: function(what){console.log(what);},
    newWhileLoop: function(what){console.log(what);},
  },
});
