;(function(global) {
var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

var _slicedToArray = function () { function sliceIterator(arr, i) { var _arr = []; var _n = true; var _d = false; var _e = undefined; try { for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"]) _i["return"](); } finally { if (_d) throw _e; } } return _arr; } return function (arr, i) { if (Array.isArray(arr)) { return arr; } else if (Symbol.iterator in Object(arr)) { return sliceIterator(arr, i); } else { throw new TypeError("Invalid attempt to destructure non-iterable instance"); } }; }();

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _toConsumableArray(arr) { if (Array.isArray(arr)) { for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) { arr2[i] = arr[i]; } return arr2; } else { return Array.from(arr); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var QmlWeb = {};

global.QmlWeb = QmlWeb;

var objectIds = 0;

var QObject = function () {
  function QObject(parent) {
    _classCallCheck(this, QObject);

    this.$parent = parent;
    if (parent && parent.$tidyupList) {
      parent.$tidyupList.push(this);
    }

    // List of things to tidy up when deleting this object.
    this.$tidyupList = [];
    this.$properties = {};

    this.objectId = objectIds++;
  }

  _createClass(QObject, [{
    key: "$delete",
    value: function $delete() {
      if (this.$Component) {
        this.$Component.destruction();
      }

      while (this.$tidyupList.length > 0) {
        var item = this.$tidyupList[0];
        if (item.$delete) {
          // It's a QObject
          item.$delete();
        } else {
          // It must be a signal
          item.disconnect(this);
        }
      }

      for (var i in this.$properties) {
        var prop = this.$properties[i];
        while (prop.$tidyupList.length > 0) {
          prop.$tidyupList[0].disconnect(prop);
        }
      }

      if (this.$parent && this.$parent.$tidyupList) {
        var index = this.$parent.$tidyupList.indexOf(this);
        this.$parent.$tidyupList.splice(index, 1);
      }

      // must do this:
      // 1) parent will be notified and erase object from it's children.
      // 2) DOM node will be removed.
      this.parent = undefined;
    }

    // must have a `destroy` method
    // http://doc.qt.io/qt-5/qtqml-javascript-dynamicobjectcreation.html

  }, {
    key: "destroy",
    value: function destroy() {
      this.$delete();
    }
  }]);

  return QObject;
}();

QmlWeb.QObject = QObject;

var JSItemModel = function () {
  function JSItemModel() {
    _classCallCheck(this, JSItemModel);

    this.roleNames = [];

    var Signal = QmlWeb.Signal;
    this.dataChanged = Signal.signal([{ type: "int", name: "startIndex" }, { type: "int", name: "endIndex" }]);
    this.rowsInserted = Signal.signal([{ type: "int", name: "startIndex" }, { type: "int", name: "endIndex" }]);
    this.rowsMoved = Signal.signal([{ type: "int", name: "sourceStartIndex" }, { type: "int", name: "sourceEndIndex" }, { type: "int", name: "destinationIndex" }]);
    this.rowsRemoved = Signal.signal([{ type: "int", name: "startIndex" }, { type: "int", name: "endIndex" }]);
    this.modelReset = Signal.signal();
  }

  _createClass(JSItemModel, [{
    key: "setRoleNames",
    value: function setRoleNames(names) {
      this.roleNames = names;
    }
  }]);

  return JSItemModel;
}();

var ItemModel = function (_JSItemModel) {
  _inherits(ItemModel, _JSItemModel);

  function ItemModel(items) {
    _classCallCheck(this, ItemModel);

    var _this = _possibleConstructorReturn(this, (ItemModel.__proto__ || Object.getPrototypeOf(ItemModel)).call(this));

    _this.items = items;
    return _this;
  }

  _createClass(ItemModel, [{
    key: "data",
    value: function data(index, role) {
      if (index > this.items.length) return undefined;
      return this.items[index][role];
    }
  }, {
    key: "get",
    value: function get(index) {
      if (index > this.items.length) return undefined;
      return this.items[index];
    }
  }, {
    key: "push",
    value: function push(item) {
      this.items.push(item);
      var roleNames = [];
      for (var i in item) {
        if (i !== "index") {
          roleNames.push(i);
        }
      }
      this.setRoleNames(roleNames);
      this.rowsInserted(this.items.length - 1, this.items.length);
    }
  }, {
    key: "remove",
    value: function remove(index) {
      if (index < 0) return;
      this.items.splice(index, 1);
      this.rowsRemoved(index, index + 1);
    }
  }, {
    key: "rowCount",
    value: function rowCount() {
      return this.items.length;
    }
  }]);

  return ItemModel;
}(JSItemModel);

QmlWeb.JSItemModel = JSItemModel;
QmlWeb.ItemModel = ItemModel;

// TODO complete implementation (with attributes `r`,`g` and `b`).

var QColor = function () {
  function QColor(val) {
    _classCallCheck(this, QColor);

    this.$value = "black";
    if (val instanceof QColor) {
      // Copy constructor
      this.$value = val.$value;
    } else if (typeof val === "string") {
      this.$value = val.toLowerCase();
    } else if (typeof val === "number") {
      // we assume it is int value and must be converted to css hex with padding
      var rgb = (Math.round(val) + 0x1000000).toString(16).substr(-6);
      this.$value = "#" + rgb;
    }
  }

  _createClass(QColor, [{
    key: "toString",
    value: function toString() {
      return this.$value;
    }
  }, {
    key: "$get",
    value: function $get() {
      // Returns the same instance for all equivalent colors.
      // NOTE: the returned value should not be changed using method calls, if
      // those would be added in the future, the returned value should be wrapped.
      if (!QColor.$colors[this.$value]) {
        if (QColor.$colorsCount >= QColor.comparableColorsLimit) {
          // Too many colors created, bail out to avoid memory hit
          return this;
        }
        QColor.$colors[this.$value] = this;
        QColor.$colorsCount++;
        if (QColor.$colorsCount === QColor.comparableColorsLimit) {
          console.warn("QmlWeb: the number of QColor instances reached the limit set in", "QmlWeb.QColor.comparableColorsLimit. Further created colors would", "not be comparable to avoid memory hit.");
        }
      }
      return QColor.$colors[this.$value];
    }
  }]);

  return QColor;
}();

QColor.$colors = {};
QColor.$colorsCount = 0;
QColor.comparableColorsLimit = 10000;
QmlWeb.QColor = QColor;

var QSizeF = function (_QmlWeb$QObject) {
  _inherits(QSizeF, _QmlWeb$QObject);

  function QSizeF(width, height) {
    _classCallCheck(this, QSizeF);

    var _this2 = _possibleConstructorReturn(this, (QSizeF.__proto__ || Object.getPrototypeOf(QSizeF)).call(this));

    var createProperty = QmlWeb.createProperty;
    createProperty("real", _this2, "width", { initialValue: width });
    createProperty("real", _this2, "height", { initialValue: height });
    return _this2;
  }

  return QSizeF;
}(QmlWeb.QObject);

QmlWeb.QSizeF = QSizeF;

var Signal = function () {
  function Signal() {
    var _this3 = this;

    var params = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : [];
    var options = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};

    _classCallCheck(this, Signal);

    this.connectedSlots = [];
    this.obj = options.obj;
    this.options = options;

    this.signal = function () {
      return _this3.execute.apply(_this3, arguments);
    };
    this.signal.parameters = params;
    this.signal.connect = this.connect.bind(this);
    this.signal.disconnect = this.disconnect.bind(this);
    this.signal.isConnected = this.isConnected.bind(this);
  }

  _createClass(Signal, [{
    key: "execute",
    value: function execute() {
      QmlWeb.QMLProperty.pushEvalStack();

      for (var _len = arguments.length, args = Array(_len), _key = 0; _key < _len; _key++) {
        args[_key] = arguments[_key];
      }

      for (var i in this.connectedSlots) {
        var desc = this.connectedSlots[i];
        if (desc.type & Signal.QueuedConnection) {
          Signal.$addQueued(desc, args);
        } else {
          Signal.$execute(desc, args);
        }
      }
      QmlWeb.QMLProperty.popEvalStack();
    }
  }, {
    key: "connect",
    value: function connect() {
      var type = Signal.AutoConnection;

      for (var _len2 = arguments.length, args = Array(_len2), _key2 = 0; _key2 < _len2; _key2++) {
        args[_key2] = arguments[_key2];
      }

      if (typeof args[args.length - 1] === "number") {
        type = args.pop();
      }
      if (type & Signal.UniqueConnection) {
        if (this.isConnected.apply(this, args)) {
          return;
        }
      }
      if (args.length === 1) {
        this.connectedSlots.push({ thisObj: global, slot: args[0], type: type });
      } else if (typeof args[1] === "string" || args[1] instanceof String) {
        if (args[0].$tidyupList && args[0] !== this.obj) {
          args[0].$tidyupList.push(this.signal);
        }
        var slot = args[0][args[1]];
        this.connectedSlots.push({ thisObj: args[0], slot: slot, type: type });
      } else {
        if (args[0].$tidyupList && (!this.obj || args[0] !== this.obj && args[0] !== this.obj.$parent)) {
          args[0].$tidyupList.push(this.signal);
        }
        this.connectedSlots.push({ thisObj: args[0], slot: args[1], type: type });
      }

      // Notify object of connect
      if (this.options.obj && this.options.obj.$connectNotify) {
        this.options.obj.$connectNotify(this.options);
      }
    }
  }, {
    key: "disconnect",
    value: function disconnect() {
      for (var _len3 = arguments.length, args = Array(_len3), _key3 = 0; _key3 < _len3; _key3++) {
        args[_key3] = arguments[_key3];
      }

      // type meaning:
      //  1 = function, 2 = string
      //  3 = object with string method,  4 = object with function
      var callType = args.length === 1 ? args[0] instanceof Function ? 1 : 2 : typeof args[1] === "string" || args[1] instanceof String ? 3 : 4;
      for (var i = 0; i < this.connectedSlots.length; i++) {
        var _connectedSlots$i = this.connectedSlots[i],
            slot = _connectedSlots$i.slot,
            thisObj = _connectedSlots$i.thisObj;

        if (callType === 1 && slot === args[0] || callType === 2 && thisObj === args[0] || callType === 3 && thisObj === args[0] && slot === args[0][args[1]] || thisObj === args[0] && slot === args[1]) {
          if (thisObj) {
            var index = thisObj.$tidyupList.indexOf(this.signal);
            thisObj.$tidyupList.splice(index, 1);
          }
          this.connectedSlots.splice(i, 1);
          // We have removed an item from the list so the indexes shifted one
          // backwards
          i--;
        }
      }

      // Notify object of disconnect
      if (this.options.obj && this.options.obj.$disconnectNotify) {
        this.options.obj.$disconnectNotify(this.options);
      }
    }
  }, {
    key: "isConnected",
    value: function isConnected() {
      for (var _len4 = arguments.length, args = Array(_len4), _key4 = 0; _key4 < _len4; _key4++) {
        args[_key4] = arguments[_key4];
      }

      var callType = args.length === 1 ? 1 : typeof args[1] === "string" || args[1] instanceof String ? 2 : 3;
      for (var i in this.connectedSlots) {
        var _connectedSlots$i2 = this.connectedSlots[i],
            slot = _connectedSlots$i2.slot,
            thisObj = _connectedSlots$i2.thisObj;

        if (callType === 1 && slot === args[0] || callType === 2 && thisObj === args[0] && slot === args[0][args[1]] || thisObj === args[0] && slot === args[1]) {
          return true;
        }
      }
      return false;
    }
  }], [{
    key: "signal",
    value: function signal() {
      for (var _len5 = arguments.length, args = Array(_len5), _key5 = 0; _key5 < _len5; _key5++) {
        args[_key5] = arguments[_key5];
      }

      return new (Function.prototype.bind.apply(Signal, [null].concat(args)))().signal;
    }
  }, {
    key: "$execute",
    value: function $execute(desc, args) {
      try {
        desc.slot.apply(desc.thisObj, args);
      } catch (err) {
        console.error("Signal slot error:", err.message, err, Function.prototype.toString.call(desc.slot));
      }
    }
  }, {
    key: "$addQueued",
    value: function $addQueued(desc, args) {
      if (Signal.$queued.length === 0) {
        if (global.setImmediate) {
          global.setImmediate(Signal.$executeQueued);
        } else {
          global.setTimeout(Signal.$executeQueued, 0);
        }
      }
      Signal.$queued.push([desc, args]);
    }
  }, {
    key: "$executeQueued",
    value: function $executeQueued() {
      // New queued signals should be executed on next tick of the event loop
      var queued = Signal.$queued;
      Signal.$queued = [];

      QmlWeb.QMLProperty.pushEvalStack();
      for (var i in queued) {
        Signal.$execute.apply(Signal, _toConsumableArray(queued[i]));
      }
      QmlWeb.QMLProperty.popEvalStack();
    }
  }]);

  return Signal;
}();

Signal.$queued = [];

Signal.AutoConnection = 0;
Signal.DirectConnection = 1;
Signal.QueuedConnection = 2;
Signal.UniqueConnection = 128;

QmlWeb.Signal = Signal;

var Qt = {
  rgba: function rgba(r, g, b, a) {
    var intr = Math.round(r * 255);
    var intg = Math.round(g * 255);
    var intb = Math.round(b * 255);
    return "rgba(" + intr + "," + intg + "," + intb + "," + a + ")";
  },
  hsla: function hsla(h, s, l, a) {
    var inth = Math.round(h * 360);
    var ints = Math.round(s * 100);
    var intl = Math.round(l * 100);
    return "hsla(" + inth + "," + ints + "%," + intl + "%," + a + ")";
  },
  openUrlExternally: function openUrlExternally(url) {
    var page = window.open(url, "_blank");
    page.focus();
  },
  // Load file, parse and construct as Component (.qml)
  createComponent: function createComponent(name) {
    var engine = QmlWeb.engine;

    var file = engine.$resolvePath(name);

    // If "name" was a full URL, "file" will be equivalent to name and this
    // will try and load the Component from the full URL, otherwise, this
    // doubles as checking for the file in the current directory.
    var tree = engine.loadComponent(file);

    // If the Component is not found, and it is not a URL, look for "name" in
    // this context's importSearchPaths
    if (!tree) {
      var nameIsUrl = engine.$parseURI(name) !== undefined;
      if (!nameIsUrl) {
        var moreDirs = engine.importSearchPaths(QmlWeb.executionContext.importContextId);
        for (var i = 0; i < moreDirs.length; i++) {
          file = "" + moreDirs[i] + name;
          tree = engine.loadComponent(file);
          if (tree) break;
        }
      }
    }

    if (!tree) {
      return undefined;
    }

    var QMLComponent = QmlWeb.getConstructor("QtQml", "2.0", "Component");
    var component = new QMLComponent({
      object: tree,
      context: QmlWeb.executionContext
    });
    component.$basePath = engine.extractBasePath(file);
    component.$imports = tree.$imports;
    component.$file = file; // just for debugging

    engine.loadImports(tree.$imports, component.$basePath, component.importContextId);

    return component;
  },

  createQmlObject: function createQmlObject(src, parent, file) {
    var tree = QmlWeb.parseQML(src, file);

    // Create and initialize objects

    var QMLComponent = QmlWeb.getConstructor("QtQml", "2.0", "Component");
    var component = new QMLComponent({
      object: tree,
      parent: parent,
      context: QmlWeb.executionContext
    });

    var engine = QmlWeb.engine;
    engine.loadImports(tree.$imports, undefined, component.importContextId);

    var resolvedFile = file || Qt.resolvedUrl("createQmlObject_function");
    component.$basePath = engine.extractBasePath(resolvedFile);
    component.$imports = tree.$imports; // for later use
    // not just for debugging, but for basepath too, see above
    component.$file = resolvedFile;

    var obj = component.createObject(parent);

    var QMLOperationState = QmlWeb.QMLOperationState;
    if (engine.operationState !== QMLOperationState.Init && engine.operationState !== QMLOperationState.Idle) {
      // We don't call those on first creation, as they will be called
      // by the regular creation-procedures at the right time.
      engine.$initializePropertyBindings();

      engine.callCompletedSignals();
    }

    return obj;
  },

  // Returns url resolved relative to the URL of the caller.
  // http://doc.qt.io/qt-5/qml-qtqml-qt.html#resolvedUrl-method
  resolvedUrl: function resolvedUrl(url) {
    return QmlWeb.qmlUrl(url);
  },

  size: function size(width, height) {
    return new QmlWeb.QSizeF(width, height);
  },

  // Buttons masks
  LeftButton: 1,
  RightButton: 2,
  MiddleButton: 4,
  // Modifiers masks
  NoModifier: 0,
  ShiftModifier: 1,
  ControlModifier: 2,
  AltModifier: 4,
  MetaModifier: 8,
  KeypadModifier: 16, // Note: Not available in web
  // Layout directions
  LeftToRight: 0,
  RightToLeft: 1,
  // Orientations
  Vertical: 0,
  Horizontal: 1,
  // Keys
  Key_Escape: 27,
  Key_Tab: 9,
  Key_Backtab: 245,
  Key_Backspace: 8,
  Key_Return: 13,
  Key_Enter: 13,
  Key_Insert: 45,
  Key_Delete: 46,
  Key_Pause: 19,
  Key_Print: 42,
  Key_SysReq: 0,
  Key_Clear: 12,
  Key_Home: 36,
  Key_End: 35,
  Key_Left: 37,
  Key_Up: 38,
  Key_Right: 39,
  Key_Down: 40,
  Key_PageUp: 33,
  Key_PageDown: 34,
  Key_Shift: 16,
  Key_Control: 17,
  Key_Meta: 91,
  Key_Alt: 18,
  Key_AltGr: 0,
  Key_CapsLock: 20,
  Key_NumLock: 144,
  Key_ScrollLock: 145,
  Key_F1: 112, Key_F2: 113, Key_F3: 114, Key_F4: 115, Key_F5: 116, Key_F6: 117,
  Key_F7: 118, Key_F8: 119, Key_F9: 120, Key_F10: 121, Key_F11: 122,
  Key_F12: 123, Key_F13: 124, Key_F14: 125, Key_F15: 126, Key_F16: 127,
  Key_F17: 128, Key_F18: 129, Key_F19: 130, Key_F20: 131, Key_F21: 132,
  Key_F22: 133, Key_F23: 134, Key_F24: 135,
  Key_F25: 0, Key_F26: 0, Key_F27: 0, Key_F28: 0, Key_F29: 0, Key_F30: 0,
  Key_F31: 0, Key_F32: 0, Key_F33: 0, Key_F34: 0, Key_F35: 0,
  Key_Super_L: 0,
  Key_Super_R: 0,
  Key_Menu: 0,
  Key_Hyper_L: 0,
  Key_Hyper_R: 0,
  Key_Help: 6,
  Key_Direction_L: 0,
  Key_Direction_R: 0,
  Key_Space: 32,
  Key_Any: 32,
  Key_Exclam: 161,
  Key_QuoteDbl: 162,
  Key_NumberSign: 163,
  Key_Dollar: 164,
  Key_Percent: 165,
  Key_Ampersant: 166,
  Key_Apostrophe: 222,
  Key_ParenLeft: 168,
  Key_ParenRight: 169,
  Key_Asterisk: 170,
  Key_Plus: 171,
  Key_Comma: 188,
  Key_Minus: 173,
  Key_Period: 190,
  Key_Slash: 191,
  Key_0: 48, Key_1: 49, Key_2: 50, Key_3: 51, Key_4: 52,
  Key_5: 53, Key_6: 54, Key_7: 55, Key_8: 56, Key_9: 57,
  Key_Colon: 58,
  Key_Semicolon: 59,
  Key_Less: 60,
  Key_Equal: 61,
  Key_Greater: 62,
  Key_Question: 63,
  Key_At: 64,
  Key_A: 65, Key_B: 66, Key_C: 67, Key_D: 68, Key_E: 69, Key_F: 70, Key_G: 71,
  Key_H: 72, Key_I: 73, Key_J: 74, Key_K: 75, Key_L: 76, Key_M: 77, Key_N: 78,
  Key_O: 79, Key_P: 80, Key_Q: 81, Key_R: 82, Key_S: 83, Key_T: 84, Key_U: 85,
  Key_V: 86, Key_W: 87, Key_X: 88, Key_Y: 89, Key_Z: 90,
  Key_BracketLeft: 219,
  Key_Backslash: 220,
  Key_BracketRight: 221,
  Key_AsciiCircum: 160,
  Key_Underscore: 167,
  Key_QuoteLeft: 0,
  Key_BraceLeft: 174,
  Key_Bar: 172,
  Key_BraceRight: 175,
  Key_AsciiTilde: 176,
  Key_Back: 0,
  Key_Forward: 0,
  Key_Stop: 0,
  Key_VolumeDown: 182,
  Key_VolumeUp: 183,
  Key_VolumeMute: 181,
  Key_multiply: 106,
  Key_add: 107,
  Key_substract: 109,
  Key_divide: 111,
  Key_News: 0,
  Key_OfficeHome: 0,
  Key_Option: 0,
  Key_Paste: 0,
  Key_Phone: 0,
  Key_Calendar: 0,
  Key_Reply: 0,
  Key_Reload: 0,
  Key_RotateWindows: 0,
  Key_RotationPB: 0,
  Key_RotationKB: 0,
  Key_Save: 0,
  Key_Send: 0,
  Key_Spell: 0,
  Key_SplitScreen: 0,
  Key_Support: 0,
  Key_TaskPane: 0,
  Key_Terminal: 0,
  Key_Tools: 0,
  Key_Travel: 0,
  Key_Video: 0,
  Key_Word: 0,
  Key_Xfer: 0,
  Key_ZoomIn: 0,
  Key_ZoomOut: 0,
  Key_Away: 0,
  Key_Messenger: 0,
  Key_WebCam: 0,
  Key_MailForward: 0,
  Key_Pictures: 0,
  Key_Music: 0,
  Key_Battery: 0,
  Key_Bluetooth: 0,
  Key_WLAN: 0,
  Key_UWB: 0,
  Key_AudioForward: 0,
  Key_AudioRepeat: 0,
  Key_AudioRandomPlay: 0,
  Key_Subtitle: 0,
  Key_AudioCycleTrack: 0,
  Key_Time: 0,
  Key_Hibernate: 0,
  Key_View: 0,
  Key_TopMenu: 0,
  Key_PowerDown: 0,
  Key_Suspend: 0,
  Key_ContrastAdjust: 0,
  Key_MediaLast: 0,
  Key_unknown: -1,
  Key_Call: 0,
  Key_Camera: 0,
  Key_CameraFocus: 0,
  Key_Context1: 0,
  Key_Context2: 0,
  Key_Context3: 0,
  Key_Context4: 0,
  Key_Flip: 0,
  Key_Hangup: 0,
  Key_No: 0,
  Key_Select: 93,
  Key_Yes: 0,
  Key_ToggleCallHangup: 0,
  Key_VoiceDial: 0,
  Key_LastNumberRedial: 0,
  Key_Execute: 43,
  Key_Printer: 42,
  Key_Play: 250,
  Key_Sleep: 95,
  Key_Zoom: 251,
  Key_Cancel: 3,
  // Align
  AlignLeft: 0x0001,
  AlignRight: 0x0002,
  AlignHCenter: 0x0004,
  AlignJustify: 0x0008,
  AlignTop: 0x0020,
  AlignBottom: 0x0040,
  AlignVCenter: 0x0080,
  AlignCenter: 0x0084,
  AlignBaseline: 0x0100,
  AlignAbsolute: 0x0010,
  AlignLeading: 0x0001,
  AlignTrailing: 0x0002,
  AlignHorizontal_Mask: 0x001f,
  AlignVertical_Mask: 0x01e0,
  // Screen
  PrimaryOrientation: 0,
  PortraitOrientation: 1,
  LandscapeOrientation: 2,
  InvertedPortraitOrientation: 4,
  InvertedLandscapeOrientation: 8,
  // CursorShape
  ArrowCursor: 0,
  UpArrowCursor: 1,
  CrossCursor: 2,
  WaitCursor: 3,
  IBeamCursor: 4,
  SizeVerCursor: 5,
  SizeHorCursor: 6,
  SizeBDiagCursor: 7,
  SizeFDiagCursor: 8,
  SizeAllCursor: 9,
  BlankCursor: 10,
  SplitVCursor: 11,
  SplitHCursor: 12,
  PointingHandCursor: 13,
  ForbiddenCursor: 14,
  WhatsThisCursor: 15,
  BusyCursor: 16,
  OpenHandCursor: 17,
  ClosedHandCursor: 18,
  DragCopyCursor: 19,
  DragMoveCursor: 20,
  DragLinkCursor: 21,
  LastCursor: 21, //DragLinkCursor,
  BitmapCursor: 24,
  CustomCursor: 25,
  // ScrollBar Policy
  ScrollBarAsNeeded: 0,
  ScrollBarAlwaysOff: 1,
  ScrollBarAlwaysOn: 2
};

QmlWeb.Qt = Qt;

var QMLBinding = function () {
  /**
   * Create QML binding.
   * @param {Variant} val Sourcecode or function representing the binding
   * @param {Array} tree Parser tree of the binding
   * @return {Object} Object representing the binding
   */
  function QMLBinding(val, tree) {
    _classCallCheck(this, QMLBinding);

    // this.isFunction states whether the binding is a simple js statement or a
    // function containing a return statement. We decide this on whether it is a
    // code block or not. If it is, we require a return statement. If it is a
    // code block it could though also be a object definition, so we need to
    // check that as well (it is, if the content is labels).
    this.isFunction = tree && tree[0] === "block" && tree[1][0] && tree[1][0][0] !== "label";
    this.src = val;
    this.compiled = false;
  }

  _createClass(QMLBinding, [{
    key: "toJSON",
    value: function toJSON() {
      return {
        src: this.src,
        deps: JSON.stringify(this.deps),
        tree: JSON.stringify(this.tree)
      };
    }
  }, {
    key: "eval",
    value: function _eval(object, context, basePath) {
      // .call is needed for `this` support
      return this.impl.call(object, object, context, basePath);
    }

    /**
     * Compile binding. Afterwards you may call binding.eval to evaluate.
     */

  }, {
    key: "compile",
    value: function compile() {
      this.src = this.src.trim();
      this.impl = QMLBinding.bindSrc(this.src, this.isFunction);
      this.compiled = true;
    }
  }], [{
    key: "bindSrc",
    value: function bindSrc(src, isFunction) {
      return new Function("__executionObject", "__executionContext", "__basePath", "\n      QmlWeb.executionContext = __executionContext;\n      if (__basePath) {\n        QmlWeb.engine.$basePath = __basePath;\n      }\n      with(QmlWeb) with(__executionContext) with(__executionObject) {\n        " + (isFunction ? "" : "return") + " " + src + "\n      }\n    ");
    }
  }]);

  return QMLBinding;
}();

QmlWeb.QMLBinding = QMLBinding;

function QMLBoolean(val) {
  return !!val;
}
QMLBoolean.plainType = true;
QmlWeb.qmlBoolean = QMLBoolean;

// There can only be one running QMLEngine.
// This variable points to the currently running engine.
QmlWeb.engine = null;

var geometryProperties = ["width", "height", "fill", "x", "y", "left", "right", "top", "bottom"];

// QML engine. EXPORTED.

var QMLEngine = function () {
  function QMLEngine(element) {
    _classCallCheck(this, QMLEngine);

    //----------Public Members----------

    this.fps = 60;
    // Math.floor, causes bugs to timing?
    this.$interval = Math.floor(1000 / this.fps);
    this.running = false;
    this.rootElement = element;

    // Cached component trees (post-QmlWeb.convertToEngine)
    this.components = {};

    // Cached parsed JS files (post-QmlWeb.jsparse)
    this.js = {};

    // List of Component.completed signals
    this.completedSignals = [];

    // Current operation state of the engine (Idle, init, etc.)
    this.operationState = 1;

    // List of properties whose values are bindings. For internal use only.
    this.bindedProperties = [];

    // List of operations to perform later after init. For internal use only.
    this.pendingOperations = [];

    // Root object of the engine
    this.rootObject = null;

    // Base path of qml engine (used for resource loading)
    this.$basePath = "";

    // Module import paths overrides
    this.userAddedModulePaths = {};

    // Stores data for setImportPathList(), importPathList(), and addImportPath
    this.userAddedImportPaths = [];

    //----------Private Members---------

    // Ticker resource id and ticker callbacks
    this._tickers = [];
    this._lastTick = Date.now();

    // Callbacks for stopping or starting the engine
    this._whenStop = [];
    this._whenStart = [];

    // Keyboard management
    this.$initKeyboard();

    //----------Construct----------

    // TODO: Move to module initialization
    var QMLBaseObject = QmlWeb.getConstructor("QtQml", "2.0", "QtObject");
    var constructors = QmlWeb.constructors;
    for (var i in constructors) {
      if (constructors[i].getAttachedObject) {
        QmlWeb.setupGetter(QMLBaseObject.prototype, i, constructors[i].getAttachedObject);
      }
    }
  }

  //---------- Public Methods ----------

  // Start the engine


  _createClass(QMLEngine, [{
    key: "start",
    value: function start() {
      QmlWeb.engine = this;
      var QMLOperationState = QmlWeb.QMLOperationState;
      if (this.operationState !== QMLOperationState.Running) {
        this.operationState = QMLOperationState.Running;
        this._tickerId = setInterval(this._tick.bind(this), this.$interval);
        this._whenStart.forEach(function (callback) {
          return callback();
        });
      }
    }

    // Stop the engine

  }, {
    key: "stop",
    value: function stop() {
      var QMLOperationState = QmlWeb.QMLOperationState;
      if (this.operationState === QMLOperationState.Running) {
        clearInterval(this._tickerId);
        this.operationState = QMLOperationState.Idle;
        this._whenStop.forEach(function (callback) {
          return callback();
        });
      }
    }

    // eslint-disable-next-line max-len
    /** from http://docs.closure-library.googlecode.com/git/local_closure_goog_uri_uri.js.source.html
     *
     * Removes dot segments in given path component, as described in
     * RFC 3986, section 5.2.4.
     *
     * @param {string} path A non-empty path component.
     * @return {string} Path component with removed dot segments.
     */

  }, {
    key: "removeDotSegments",
    value: function removeDotSegments(path) {
      // path.startsWith("/") is not supported in some browsers
      var leadingSlash = path && path[0] === "/";
      var segments = path.split("/");
      var out = [];

      for (var pos = 0; pos < segments.length;) {
        var segment = segments[pos++];

        if (segment === ".") {
          if (leadingSlash && pos === segments.length) {
            out.push("");
          }
        } else if (segment === "..") {
          if (out.length > 1 || out.length === 1 && out[0] !== "") {
            out.pop();
          }
          if (leadingSlash && pos === segments.length) {
            out.push("");
          }
        } else {
          out.push(segment);
          leadingSlash = true;
        }
      }

      return out.join("/");
    }
  }, {
    key: "extractBasePath",
    value: function extractBasePath(file) {
      // work both in url ("/") and windows ("\", from file://d:\test\) notation
      var basePath = file.split(/[/\\]/);
      basePath[basePath.length - 1] = "";
      return basePath.join("/");
    }
  }, {
    key: "extractFileName",
    value: function extractFileName(file) {
      return file.split(/[/\\]/).pop();
    }

    // Load file, parse and construct (.qml or .qml.js)

  }, {
    key: "loadFile",
    value: function loadFile(file) {
      var parentComponent = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;

      // Create an anchor element to get the absolute path from the DOM
      if (!this.$basePathA) {
        this.$basePathA = document.createElement("a");
      }
      this.$basePathA.href = this.extractBasePath(file);
      this.$basePath = this.$basePathA.href;
      var fileName = this.extractFileName(file);
      var tree = this.loadComponent(this.$resolvePath(fileName));
      return this.loadQMLTree(tree, parentComponent, file);
    }

    // parse and construct qml
    // file is not required; only for debug purposes
    // This function is only used by the QmlWeb tests

  }, {
    key: "loadQML",
    value: function loadQML(src) {
      var parentComponent = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;
      var file = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : undefined;

      return this.loadQMLTree(QmlWeb.parseQML(src, file), parentComponent, file);
    }
  }, {
    key: "loadQMLTree",
    value: function loadQMLTree(tree) {
      var parentComponent = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;
      var file = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : undefined;

      QmlWeb.engine = this;

      // Create and initialize objects
      var QMLComponent = QmlWeb.getConstructor("QtQml", "2.0", "Component");
      var component = new QMLComponent({
        object: tree,
        parent: parentComponent
      });

      this.loadImports(tree.$imports, undefined, component.importContextId);
      component.$basePath = this.$basePath;
      component.$imports = tree.$imports; // for later use
      component.$file = file; // just for debugging

      this.rootObject = component.$createObject(parentComponent);
      component.finalizeImports(this.rootContext());
      this.$initializePropertyBindings();

      this.start();

      this.callCompletedSignals();

      return component;
    }
  }, {
    key: "rootContext",
    value: function rootContext() {
      return this.rootObject.$context;
    }

    // next 3 methods used in Qt.createComponent for qml files lookup
    // http://doc.qt.io/qt-5/qqmlengine.html#addImportPath

  }, {
    key: "addImportPath",
    value: function addImportPath(dirpath) {
      this.userAddedImportPaths.push(dirpath);
    }

    /* Add this dirpath to be checked for components. This is the result of
     * something like:
     *
     * import "SomeDir/AnotherDirectory"
     *
     * The importContextId ensures it is only accessible from the file in which
     * it was imported. */

  }, {
    key: "addComponentImportPath",
    value: function addComponentImportPath(importContextId, dirpath, qualifier) {
      if (!this.componentImportPaths) {
        this.componentImportPaths = {};
      }
      if (!this.componentImportPaths[importContextId]) {
        this.componentImportPaths[importContextId] = {};
      }

      var paths = this.componentImportPaths[importContextId];

      if (qualifier) {
        if (!paths.qualified) {
          paths.qualified = {};
        }
        paths.qualified[qualifier] = dirpath;
      } else {
        if (!paths.unqualified) {
          paths.unqualified = [];
        }
        paths.unqualified.push(dirpath);
      }
    }
  }, {
    key: "importSearchPaths",
    value: function importSearchPaths(importContextId) {
      if (!this.componentImportPaths) {
        return [];
      }
      var paths = this.componentImportPaths[importContextId];
      if (!paths) {
        return [];
      }
      return paths.unqualified || [];
    }
  }, {
    key: "qualifiedImportPath",
    value: function qualifiedImportPath(importContextId, qualifier) {
      if (!this.componentImportPaths) {
        return "";
      }
      var paths = this.componentImportPaths[importContextId];
      if (!paths || !paths.qualified) {
        return "";
      }
      return paths.qualified[qualifier] || "";
    }
  }, {
    key: "setImportPathList",
    value: function setImportPathList(arrayOfDirs) {
      this.userAddedImportPaths = arrayOfDirs;
    }
  }, {
    key: "importPathList",
    value: function importPathList() {
      return this.userAddedImportPaths;
    }

    // `addModulePath` defines conrete path for module lookup
    // e.g. addModulePath("QtQuick.Controls", "http://example.com/controls")
    // will force system to `import QtQuick.Controls` module from
    // `http://example.com/controls/qmldir`

  }, {
    key: "addModulePath",
    value: function addModulePath(moduleName, dirPath) {
      // Keep the mapping. It will be used in loadImports() function.
      // Remove trailing slash as it required for `readQmlDir`.
      this.userAddedModulePaths[moduleName] = dirPath.replace(/\/$/, "");
    }
  }, {
    key: "registerProperty",
    value: function registerProperty(obj, propName) {
      var dependantProperties = [];
      var value = obj[propName];

      var getter = function getter() {
        var QMLProperty = QmlWeb.QMLProperty;
        if (QMLProperty.evaluatingProperty && dependantProperties.indexOf(QMLProperty.evaluatingProperty) === -1) {
          dependantProperties.push(QMLProperty.evaluatingProperty);
        }
        return value;
      };

      var setter = function setter(newVal) {
        value = newVal;
        for (var i in dependantProperties) {
          dependantProperties[i].update();
        }
      };

      QmlWeb.setupGetterSetter(obj, propName, getter, setter);
    }
  }, {
    key: "loadImports",
    value: function loadImports(importsArray) {
      var currentFileDir = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : this.$basePath;
      var importContextId = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : -1;

      if (!this.qmldirsContents) {
        this.qmldirsContents = {}; // cache

        // putting initial keys in qmldirsContents - is a hack. We should find a
        // way to explain to qmlweb, is this built-in module or qmldir-style
        // module.
        for (var module in QmlWeb.modules) {
          if (module !== "Main") {
            this.qmldirsContents[module] = {};
          }
        }
      }

      if (!this.qmldirs) {
        this.qmldirs = {}; // resulting components lookup table
      }

      if (!importsArray || importsArray.length === 0) {
        return;
      }

      for (var i = 0; i < importsArray.length; i++) {
        this.loadImport(importsArray[i], currentFileDir, importContextId);
      }
    }
  }, {
    key: "loadImport",
    value: function loadImport(entry, currentFileDir, importContextId) {
      var name = entry[1];
      var alias = entry[3];

      // is it url to remote resource
      var nameIsUrl = name.indexOf("//") === 0 || name.indexOf("://") >= 0;
      // is it a module name, e.g. QtQuick, QtQuick.Controls, etc
      var nameIsQualifiedModuleName = entry[4];
      // local [relative] dir
      var nameIsDir = !nameIsQualifiedModuleName && !nameIsUrl;

      if (nameIsDir) {
        name = this.$resolvePath(name, currentFileDir);
        if (name[name.length - 1] === "/") {
          // remove trailing slash as it required for `readQmlDir`
          name = name.substr(0, name.length - 1);
        }
      }

      var content = this.qmldirsContents[name];
      // check if we have already loaded that qmldir file
      if (!content) {
        if (nameIsQualifiedModuleName && this.userAddedModulePaths[name]) {
          // 1. we have qualified module and user had configured path for that
          // module with this.addModulePath
          content = QmlWeb.readQmlDir(this.userAddedModulePaths[name]);
        } else if (nameIsUrl || nameIsDir) {
          // 2. direct load
          // nameIsUrl => url do not need dirs
          // nameIsDir => already computed full path above
          content = QmlWeb.readQmlDir(name);
        } else {
          // 3. qt-style lookup for qualified module
          var probableDirs = [currentFileDir].concat(this.importPathList());
          var diredName = name.replace(/\./g, "/");

          for (var k = 0; k < probableDirs.length; k++) {
            var file = probableDirs[k] + diredName;
            content = QmlWeb.readQmlDir(file);
            if (content) {
              break;
            }
          }
        }
        this.qmldirsContents[name] = content;
      }

      /* If there is no qmldir, add these directories to the list of places to
        * search for components (within this import scope). "noqmldir" is
        * inserted into the qmldir cache to avoid future attempts at fetching
        * the qmldir file, but we always need to the call to
        * "addComponentImportPath" for these sorts of directories. */
      if (!content || content === "noqmldir") {
        if (nameIsDir) {
          if (alias) {
            /* Use entry[1] directly, as we don't want to include the
              * basePath, otherwise it gets prepended twice in
              * createComponent. */
            this.addComponentImportPath(importContextId, entry[1] + "/", alias);
          } else {
            this.addComponentImportPath(importContextId, name + "/");
          }
        }

        this.qmldirsContents[name] = "noqmldir";
        return;
      }

      // copy founded externals to global var
      // TODO actually we have to copy it to current component
      for (var attrname in content.externals) {
        var prefix = void 0;
        if (alias) {
          prefix = alias + ".";
        } else {
          prefix = "";
        }
        this.qmldirs[prefix + attrname] = content.externals[attrname];
      }

      // keep already loaded qmldir files
      this.qmldirsContents[name] = content;
    }
  }, {
    key: "size",
    value: function size() {
      return {
        width: this.rootObject.getWidth(),
        height: this.rootObject.getHeight()
      };
    }
  }, {
    key: "focusedElement",
    value: function focusedElement() {
      return this.rootContext().activeFocus;
    }

    //---------- Private Methods ----------

  }, {
    key: "$initKeyboard",
    value: function $initKeyboard() {
      var _this4 = this;

      document.onkeypress = function (e) {
        var focusedElement = _this4.focusedElement();
        var event = QmlWeb.eventToKeyboard(e || window.event);
        var eventName = QmlWeb.keyboardSignals[event.key];

        while (focusedElement && !event.accepted) {
          var backup = focusedElement.$context.event;
          focusedElement.$context.event = event;
          focusedElement.Keys.pressed(event);
          if (eventName) {
            focusedElement.Keys[eventName](event);
          }
          focusedElement.$context.event = backup;
          if (event.accepted) {
            e.preventDefault();
          } else {
            focusedElement = focusedElement.$parent;
          }
        }
      };

      document.onkeyup = function (e) {
        var focusedElement = _this4.focusedElement();
        var event = QmlWeb.eventToKeyboard(e || window.event);

        while (focusedElement && !event.accepted) {
          var backup = focusedElement.$context.event;
          focusedElement.$context.event = event;
          focusedElement.Keys.released(event);
          focusedElement.$context.event = backup;
          if (event.accepted) {
            e.preventDefault();
          } else {
            focusedElement = focusedElement.$parent;
          }
        }
      };
    }
  }, {
    key: "_tick",
    value: function _tick() {
      var now = Date.now();
      var elapsed = now - this._lastTick;
      this._lastTick = now;
      this._tickers.forEach(function (ticker) {
        return ticker(now, elapsed);
      });
    }

    // Load resolved file, parse and construct as Component (.qml)

  }, {
    key: "loadComponent",
    value: function loadComponent(file) {
      if (file in this.components) {
        return this.components[file];
      }

      var uri = this.$parseURI(file);
      if (!uri) {
        return undefined;
      }

      var tree = void 0;
      if (uri.scheme === "qrc://") {
        tree = QmlWeb.qrc[uri.path];
        if (!tree) {
          return undefined;
        }
        // QmlWeb.qrc contains pre-parsed Component objects, but they still need
        // convertToEngine called on them.
        tree = QmlWeb.convertToEngine(tree);
      } else {
        var src = QmlWeb.getUrlContents(file, true);
        if (!src) {
          console.error("QMLEngine.loadComponent: Failed to load:", file);
          return undefined;
        }

        console.log("QMLEngine.loadComponent: Loading file:", file);
        tree = QmlWeb.parseQML(src, file);
      }

      if (!tree) {
        return undefined;
      }

      if (tree.$children.length !== 1) {
        console.error("QMLEngine.loadComponent: Failed to load:", file, ": A QML component must only contain one root element!");
        return undefined;
      }

      tree.$file = file;
      this.components[file] = tree;
      return tree;
    }

    // Load resolved file and parse as JavaScript

  }, {
    key: "loadJS",
    value: function loadJS(file) {
      if (file in this.js) {
        return this.js[file];
      }

      var uri = this.$parseURI(file);
      if (!uri) {
        return undefined;
      }

      if (uri.scheme === "qrc://") {
        return QmlWeb.qrc[uri.path];
      }

      QmlWeb.loadParser();
      return QmlWeb.jsparse(QmlWeb.getUrlContents(file));
    }
  }, {
    key: "$registerStart",
    value: function $registerStart(f) {
      this._whenStart.push(f);
    }
  }, {
    key: "$registerStop",
    value: function $registerStop(f) {
      this._whenStop.push(f);
    }
  }, {
    key: "$addTicker",
    value: function $addTicker(t) {
      this._tickers.push(t);
    }
  }, {
    key: "$removeTicker",
    value: function $removeTicker(t) {
      var index = this._tickers.indexOf(t);
      if (index !== -1) {
        this._tickers.splice(index, 1);
      }
    }
  }, {
    key: "$initializePropertyBindings",
    value: function $initializePropertyBindings() {
      // Initialize property bindings
      // we use `while`, because $initializePropertyBindings may be called
      // recursive (because of Loader and/or createQmlObject )
      while (this.bindedProperties.length > 0) {
        var property = this.bindedProperties.shift();

        if (!property.binding) {
          // Probably, the binding was overwritten by an explicit value. Ignore.
          continue;
        }

        if (property.needsUpdate) {
          property.update();
        } else if (geometryProperties.indexOf(property.name) >= 0) {
          // It is possible that bindings with these names was already evaluated
          // during eval of other bindings but in that case $updateHGeometry and
          // $updateVGeometry could be blocked during their eval.
          // So we call them explicitly, just in case.
          var obj = property.obj,
              changed = property.changed;

          if (obj.$updateHGeometry && changed.isConnected(obj, obj.$updateHGeometry)) {
            obj.$updateHGeometry(property.val, property.val, property.name);
          }
          if (obj.$updateVGeometry && changed.isConnected(obj, obj.$updateVGeometry)) {
            obj.$updateVGeometry(property.val, property.val, property.name);
          }
        }
      }

      this.$initializeAliasSignals();
    }

    // This parses the full URL into scheme, authority and path

  }, {
    key: "$parseURI",
    value: function $parseURI(uri) {
      var match = uri.match(/^([^/]*?:\/\/)(.*?)(\/.*)$/);
      if (match) {
        return {
          scheme: match[1],
          authority: match[2],
          path: match[3]
        };
      }
      return undefined;
    }

    // Return a path to load the file

  }, {
    key: "$resolvePath",
    value: function $resolvePath(file) {
      var basePath = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : this.$basePath;

      // probably, replace :// with :/ ?
      if (file.indexOf("://") !== -1 || file.indexOf("data:") === 0 || file.indexOf("blob:") === 0) {
        return file;
      }

      var basePathURI = this.$parseURI(basePath);
      if (!basePathURI) {
        return file;
      }

      var path = basePathURI.path;
      if (file.indexOf("/") === 0) {
        path = file;
      } else {
        path = "" + path + file;
      }

      // Remove duplicate slashes and dot segments in the path
      path = this.removeDotSegments(path.replace(/([^:]\/)\/+/g, "$1"));

      return "" + basePathURI.scheme + basePathURI.authority + path;
    }

    // Return a DOM-valid path to load the image (fileURL is an already-resolved
    // URL)

  }, {
    key: "$resolveImageURL",
    value: function $resolveImageURL(fileURL) {
      var uri = this.$parseURI(fileURL);
      // If we are within the resource system, look up a "real" path that can be
      // used by the DOM. If not found, return the path itself without the
      // "qrc://" scheme.
      if (uri && uri.scheme === "qrc://") {
        return QmlWeb.qrc[uri.path] || uri.path;
      }

      // Something we can't parse, just pass it through
      return fileURL;
    }
  }, {
    key: "$initializeAliasSignals",
    value: function $initializeAliasSignals() {
      // Perform pending operations. Now we use it only to init alias's "changed"
      // handlers, that's why we have such strange function name.
      while (this.pendingOperations.length > 0) {
        var op = this.pendingOperations.shift();
        op[0](op[1], op[2], op[3]);
      }
      this.pendingOperations = [];
    }
  }, {
    key: "callCompletedSignals",
    value: function callCompletedSignals() {
      // the while loop is better than for..in loop, because completedSignals
      // array might change dynamically when some completed signal handlers will
      // create objects dynamically via createQmlObject or Loader
      while (this.completedSignals.length > 0) {
        var handler = this.completedSignals.shift();
        handler();
      }
    }
  }]);

  return QMLEngine;
}();

QmlWeb.QMLEngine = QMLEngine;

function QMLInteger(val) {
  return val | 0;
}
QMLInteger.plainType = true;
QmlWeb.qmlInteger = QMLInteger;

function QMLList(meta) {
  var list = [];
  if (meta.object instanceof Array) {
    for (var i in meta.object) {
      list.push(QmlWeb.construct({
        object: meta.object[i],
        parent: meta.parent,
        context: meta.context
      }));
    }
  } else if (meta.object instanceof QmlWeb.QMLMetaElement) {
    list.push(QmlWeb.construct({
      object: meta.object,
      parent: meta.parent,
      context: meta.context
    }));
  }

  return list;
}
QMLList.plainType = true;
QmlWeb.qmlList = QMLList;

function QMLNumber(val) {
  return +val;
}
QMLNumber.plainType = true;
QmlWeb.qmlNumber = QMLNumber;

var QMLOperationState = {
  Idle: 1,
  Init: 2,
  Running: 3
};

QmlWeb.QMLOperationState = QMLOperationState;

var QMLProperty = function () {
  function QMLProperty(type, obj, name) {
    _classCallCheck(this, QMLProperty);

    this.obj = obj;
    this.name = name;
    this.changed = QmlWeb.Signal.signal([], { obj: obj });
    this.binding = null;
    this.objectScope = null;
    this.componentScope = null;
    this.value = undefined;
    this.type = type;
    this.animation = null;
    this.needsUpdate = true;

    // This list contains all signals that hold references to this object.
    // It is needed when deleting, as we need to tidy up all references to this
    // object.
    this.$tidyupList = [];
  }

  // Called by update and set to actually set this.val, performing any type
  // conversion required.


  _createClass(QMLProperty, [{
    key: "$setVal",
    value: function $setVal(val, componentScope) {
      var constructors = QmlWeb.constructors;
      if (constructors[this.type] === QmlWeb.qmlList) {
        this.val = QmlWeb.qmlList({
          object: val,
          parent: this.obj,
          context: componentScope
        });
      } else if (val instanceof QmlWeb.QMLMetaElement) {
        var _QMLComponent = QmlWeb.getConstructor("QtQml", "2.0", "Component");
        if (constructors[val.$class] === _QMLComponent || constructors[this.type] === _QMLComponent) {
          this.val = new _QMLComponent({
            object: val,
            parent: this.obj,
            context: componentScope
          });
          /* $basePath must be set here so that Components that are assigned to
           * properties (e.g. Repeater delegates) can properly resolve child
           * Components that live in the same directory in
           * Component.createObject. */
          this.val.$basePath = componentScope.$basePath;
        } else {
          this.val = QmlWeb.construct({
            object: val,
            parent: this.obj,
            context: componentScope
          });
        }
      } else if (val instanceof Object || val === undefined || val === null) {
        this.val = val;
      } else if (constructors[this.type].plainType) {
        this.val = constructors[this.type](val);
      } else {
        this.val = new constructors[this.type](val);
      }
    }

    // Updater recalculates the value of a property if one of the dependencies
    // changed

  }, {
    key: "update",
    value: function update() {
      this.needsUpdate = false;

      if (!this.binding) {
        return;
      }

      var oldVal = this.val;

      try {
        QMLProperty.pushEvaluatingProperty(this);
        if (!this.binding.compiled) {
          this.binding.compile();
        }
        this.$setVal(this.binding.eval(this.objectScope, this.componentScope, this.componentScopeBasePath), this.componentScope);
      } catch (e) {
        console.log("QMLProperty.update binding error:", e, Function.prototype.toString.call(this.binding.eval));
      } finally {
        QMLProperty.popEvaluatingProperty();
      }

      if (this.animation) {
        this.animation.$actions = [{
          target: this.animation.target || this.obj,
          property: this.animation.property || this.name,
          from: this.animation.from || oldVal,
          to: this.animation.to || this.val
        }];
        this.animation.restart();
      }

      if (this.val !== oldVal) {
        this.changed(this.val, oldVal, this.name);
      }
    }

    // Define getter

  }, {
    key: "get",
    value: function get() {
      //if (this.needsUpdate && !QMLProperty.evaluatingPropertyPaused) {
      if (this.needsUpdate && QmlWeb.engine.operationState !== QmlWeb.QMLOperationState.Init) {
        this.update();
      }

      // If this call to the getter is due to a property that is dependant on this
      // one, we need it to take track of changes
      if (QMLProperty.evaluatingProperty) {
        //console.log(this,QMLProperty.evaluatingPropertyStack.slice(0),this.val);
        this.changed.connect(QMLProperty.evaluatingProperty, QMLProperty.prototype.update, QmlWeb.Signal.UniqueConnection);
      }

      if (this.val && this.val.$get) {
        return this.val.$get();
      }

      return this.val;
    }
    // Define setter

  }, {
    key: "set",
    value: function set(newVal, reason, objectScope, componentScope) {
      var oldVal = this.val;

      var val = newVal;
      if (val instanceof QmlWeb.QMLBinding) {
        if (!objectScope || !componentScope) {
          throw new Error("Internal error: binding assigned without scope");
        }
        this.binding = val;
        this.objectScope = objectScope;
        this.componentScope = componentScope;
        this.componentScopeBasePath = componentScope.$basePath;

        if (QmlWeb.engine.operationState !== QmlWeb.QMLOperationState.Init) {
          if (!val.compiled) {
            val.compile();
          }
          try {
            QMLProperty.pushEvaluatingProperty(this);
            this.needsUpdate = false;
            val = this.binding.eval(objectScope, componentScope, this.componentScopeBasePath);
          } finally {
            QMLProperty.popEvaluatingProperty();
          }
        } else {
          QmlWeb.engine.bindedProperties.push(this);
          return;
        }
      } else {
        if (reason !== QMLProperty.ReasonAnimation) {
          this.binding = null;
        }
        if (val instanceof Array) {
          val = val.slice(); // Copies the array
        }
      }

      if (reason === QMLProperty.ReasonInit && typeof val === "undefined") {
        if (QMLProperty.typeInitialValues.hasOwnProperty(this.type)) {
          val = QMLProperty.typeInitialValues[this.type];
        }
      }

      this.$setVal(val, componentScope);

      if (this.val !== oldVal) {
        if (this.animation && reason === QMLProperty.ReasonUser) {
          this.animation.running = false;
          this.animation.$actions = [{
            target: this.animation.target || this.obj,
            property: this.animation.property || this.name,
            from: this.animation.from || oldVal,
            to: this.animation.to || this.val
          }];
          this.animation.running = true;
        }
        if (this.obj.$syncPropertyToRemote instanceof Function && reason === QMLProperty.ReasonUser) {
          // is a remote object from e.g. a QWebChannel
          this.obj.$syncPropertyToRemote(this.name, val);
        } else {
          this.changed(this.val, oldVal, this.name);
        }
      }
    }
  }], [{
    key: "pushEvalStack",
    value: function pushEvalStack() {
      QMLProperty.evaluatingPropertyStackOfStacks.push(QMLProperty.evaluatingPropertyStack);
      QMLProperty.evaluatingPropertyStack = [];
      QMLProperty.evaluatingProperty = undefined;
      //  console.log("evaluatingProperty=>undefined due to push stck ");
    }
  }, {
    key: "popEvalStack",
    value: function popEvalStack() {
      QMLProperty.evaluatingPropertyStack = QMLProperty.evaluatingPropertyStackOfStacks.pop() || [];
      QMLProperty.evaluatingProperty = QMLProperty.evaluatingPropertyStack[QMLProperty.evaluatingPropertyStack.length - 1];
    }
  }, {
    key: "pushEvaluatingProperty",
    value: function pushEvaluatingProperty(prop) {
      // TODO say warnings if already on stack. This means binding loop.
      // BTW actually we do not loop because needsUpdate flag is reset before
      // entering update again.
      if (QMLProperty.evaluatingPropertyStack.indexOf(prop) >= 0) {
        console.error("Property binding loop detected for property", prop.name, [prop].slice(0));
      }
      QMLProperty.evaluatingProperty = prop;
      QMLProperty.evaluatingPropertyStack.push(prop); //keep stack of props
    }
  }, {
    key: "popEvaluatingProperty",
    value: function popEvaluatingProperty() {
      QMLProperty.evaluatingPropertyStack.pop();
      QMLProperty.evaluatingProperty = QMLProperty.evaluatingPropertyStack[QMLProperty.evaluatingPropertyStack.length - 1];
    }
  }]);

  return QMLProperty;
}();

// Property that is currently beeing evaluated. Used to get the information
// which property called the getter of a certain other property for
// evaluation and is thus dependant on it.


QMLProperty.evaluatingProperty = undefined;
QMLProperty.evaluatingPropertyPaused = false;
QMLProperty.evaluatingPropertyStack = [];
QMLProperty.evaluatingPropertyStackOfStacks = [];

QMLProperty.typeInitialValues = {
  int: 0,
  real: 0,
  double: 0,
  string: "",
  bool: false,
  list: [],
  enum: 0,
  url: ""
};

QMLProperty.ReasonUser = 0;
QMLProperty.ReasonInit = 1;
QMLProperty.ReasonAnimation = 2;

QmlWeb.QMLProperty = QMLProperty;

function QMLString(val) {
  return "" + val;
}
QMLString.plainType = true;
QmlWeb.qmlString = QMLString;

function QMLUrl(val) {
  return QmlWeb.engine.$resolvePath("" + val);
}
QMLUrl.plainType = true;
QmlWeb.qmlUrl = QMLUrl;

function QMLVariant(val) {
  return val;
}
QMLVariant.plainType = true;
QmlWeb.qmlVariant = QMLVariant;

window.addEventListener("load", function () {
  var metaTags = document.getElementsByTagName("body");
  for (var i = 0; i < metaTags.length; ++i) {
    var metaTag = metaTags[i];
    var source = metaTag.getAttribute("data-qml");
    if (source) {
      QmlWeb.qmlEngine = new QmlWeb.QMLEngine();
      QmlWeb.qmlEngine.loadFile(source);
      QmlWeb.qmlEngine.start();
      break;
    }
  }
});

var Easing = {
  Linear: 1,
  InQuad: 2, OutQuad: 3, InOutQuad: 4, OutInQuad: 5,
  InCubic: 6, OutCubic: 7, InOutCubic: 8, OutInCubic: 9,
  InQuart: 10, OutQuart: 11, InOutQuart: 12, OutInQuart: 13,
  InQuint: 14, OutQuint: 15, InOutQuint: 16, OutInQuint: 17,
  InSine: 18, OutSine: 19, InOutSine: 20, OutInSine: 21,
  InExpo: 22, OutExpo: 23, InOutExpo: 24, OutInExpo: 25,
  InCirc: 26, OutCirc: 27, InOutCirc: 28, OutInCirc: 29,
  InElastic: 30, OutElastic: 31, InOutElastic: 32, OutInElastic: 33,
  InBack: 34, OutBack: 35, InOutBack: 36, OutInBack: 37,
  InBounce: 38, OutBounce: 39, InOutBounce: 40, OutInBounce: 41
};

// eslint-disable-next-line complexity
QmlWeb.$ease = function (type, period, amplitude, overshoot, t) {
  switch (type) {
    // Linear
    case Easing.Linear:
      return t;

    // Quad
    case Easing.InQuad:
      return Math.pow(t, 2);
    case Easing.OutQuad:
      return -Math.pow(t - 1, 2) + 1;
    case Easing.InOutQuad:
      if (t < 0.5) {
        return 2 * Math.pow(t, 2);
      }
      return -2 * Math.pow(t - 1, 2) + 1;
    case Easing.OutInQuad:
      if (t < 0.5) {
        return -2 * Math.pow(t - 0.5, 2) + 0.5;
      }
      return 2 * Math.pow(t - 0.5, 2) + 0.5;

    // Cubic
    case Easing.InCubic:
      return Math.pow(t, 3);
    case Easing.OutCubic:
      return Math.pow(t - 1, 3) + 1;
    case Easing.InOutCubic:
      if (t < 0.5) {
        return 4 * Math.pow(t, 3);
      }
      return 4 * Math.pow(t - 1, 3) + 1;
    case Easing.OutInCubic:
      return 4 * Math.pow(t - 0.5, 3) + 0.5;

    // Quart
    case Easing.InQuart:
      return Math.pow(t, 4);
    case Easing.OutQuart:
      return -Math.pow(t - 1, 4) + 1;
    case Easing.InOutQuart:
      if (t < 0.5) {
        return 8 * Math.pow(t, 4);
      }
      return -8 * Math.pow(t - 1, 4) + 1;
    case Easing.OutInQuart:
      if (t < 0.5) {
        return -8 * Math.pow(t - 0.5, 4) + 0.5;
      }
      return 8 * Math.pow(t - 0.5, 4) + 0.5;

    // Quint
    case Easing.InQuint:
      return Math.pow(t, 5);
    case Easing.OutQuint:
      return Math.pow(t - 1, 5) + 1;
    case Easing.InOutQuint:
      if (t < 0.5) {
        return 16 * Math.pow(t, 5);
      }
      return 16 * Math.pow(t - 1, 5) + 1;
    case Easing.OutInQuint:
      if (t < 0.5) {
        return 16 * Math.pow(t - 0.5, 5) + 0.5;
      }
      return 16 * Math.pow(t - 0.5, 5) + 0.5;

    // Sine
    case Easing.InSine:
      return -Math.cos(0.5 * Math.PI * t) + 1;
    case Easing.OutSine:
      return Math.sin(0.5 * Math.PI * t);
    case Easing.InOutSine:
      return -0.5 * Math.cos(Math.PI * t) + 0.5;
    case Easing.OutInSine:
      if (t < 0.5) {
        return 0.5 * Math.sin(Math.PI * t);
      }
      return -0.5 * Math.sin(Math.PI * t) + 1;

    // Expo
    case Easing.InExpo:
      return 1 / 1023 * (Math.pow(2, 10 * t) - 1);
    case Easing.OutExpo:
      return -1024 / 1023 * (Math.pow(2, -10 * t) - 1);
    case Easing.InOutExpo:
      if (t < 0.5) {
        return 1 / 62 * (Math.pow(2, 10 * t) - 1);
      }
      return -512 / 31 * Math.pow(2, -10 * t) + 63 / 62;
    case Easing.OutInExpo:
      if (t < 0.5) {
        return -16 / 31 * (Math.pow(2, -10 * t) - 1);
      }
      return 1 / 1984 * Math.pow(2, 10 * t) + 15 / 31;

    // Circ
    case Easing.InCirc:
      return 1 - Math.sqrt(1 - t * t);
    case Easing.OutCirc:
      return Math.sqrt(1 - Math.pow(t - 1, 2));
    case Easing.InOutCirc:
      if (t < 0.5) {
        return 0.5 * (1 - Math.sqrt(1 - 4 * t * t));
      }
      return 0.5 * (Math.sqrt(1 - 4 * Math.pow(t - 1, 2)) + 1);
    case Easing.OutInCirc:
      if (t < 0.5) {
        return 0.5 * Math.sqrt(1 - Math.pow(2 * t - 1, 2));
      }
      return 0.5 * (2 - Math.sqrt(1 - Math.pow(2 * t - 1, 2)));

    // Elastic
    case Easing.InElastic:
      return -amplitude * Math.pow(2, 10 * t - 10) * Math.sin(2 * t * Math.PI / period - Math.asin(1 / amplitude));
    case Easing.OutElastic:
      return amplitude * Math.pow(2, -10 * t) * Math.sin(2 * t * Math.PI / period - Math.asin(1 / amplitude)) + 1;
    case Easing.InOutElastic:
      if (t < 0.5) {
        return -0.5 * amplitude * Math.pow(2, 20 * t - 10) * Math.sin(4 * t * Math.PI / period - Math.asin(1 / amplitude));
      }
      return -0.5 * amplitude * Math.pow(2, -20 * t + 10) * Math.sin(4 * t * Math.PI / period + Math.asin(1 / amplitude)) + 1;
    case Easing.OutInElastic:
      if (t < 0.5) {
        return 0.5 * amplitude * Math.pow(2, -20 * t) * Math.sin(4 * t * Math.PI / period - Math.asin(1 / amplitude)) + 0.5;
      }
      return -0.5 * amplitude * Math.pow(2, 20 * t - 20) * Math.sin(4 * t * Math.PI / period - Math.asin(1 / amplitude)) + 0.5;

    // Back
    case Easing.InBack:
      return (overshoot + 1) * Math.pow(t, 3) - overshoot * Math.pow(t, 2);
    case Easing.OutBack:
      return (overshoot + 1) * Math.pow(t - 1, 3) + overshoot * Math.pow(t - 1, 2) + 1;
    case Easing.InOutBack:
      if (t < 0.5) {
        return 4 * (overshoot + 1) * Math.pow(t, 3) - 2 * overshoot * Math.pow(t, 2);
      }
      return 0.5 * (overshoot + 1) * Math.pow(2 * t - 2, 3) + overshoot / 2 * Math.pow(2 * t - 2, 2) + 1;
    case Easing.OutInBack:
      if (t < 0.5) {
        return 0.5 * ((overshoot + 1) * Math.pow(2 * t - 1, 3) + overshoot * Math.pow(2 * t - 1, 2) + 1);
      }
      return 4 * (overshoot + 1) * Math.pow(t - 0.5, 3) - 2 * overshoot * Math.pow(t - 0.5, 2) + 0.5;
    // Bounce
    case Easing.InBounce:
      if (t < 1 / 11) {
        return -amplitude * 121 / 16 * (t * t - 1 / 11 * t);
      } else if (t < 3 / 11) {
        return -amplitude * 121 / 16 * (t * t - 4 / 11 * t + 3 / 121);
      } else if (t < 7 / 11) {
        return -amplitude * 121 / 16 * (t * t - 10 / 11 * t + 21 / 121);
      }
      return -(121 / 16) * (t * t - 2 * t + 1) + 1;
    case Easing.OutBounce:
      if (t < 4 / 11) {
        return 121 / 16 * t * t;
      } else if (t < 8 / 11) {
        return amplitude * (121 / 16) * (t * t - 12 / 11 * t + 32 / 121) + 1;
      } else if (t < 10 / 11) {
        return amplitude * (121 / 16) * (t * t - 18 / 11 * t + 80 / 121) + 1;
      }
      return amplitude * (121 / 16) * (t * t - 21 / 11 * t + 10 / 11) + 1;
    case Easing.InOutBounce:
      if (t < 1 / 22) {
        return -amplitude * 121 / 8 * (t * t - 1 / 22 * t);
      } else if (t < 3 / 22) {
        return -amplitude * 121 / 8 * (t * t - 2 / 11 * t + 3 / 484);
      } else if (t < 7 / 22) {
        return -amplitude * 121 / 8 * (t * t - 5 / 11 * t + 21 / 484);
      } else if (t < 11 / 22) {
        return -121 / 8 * (t * t - t + 0.25) + 0.5;
      } else if (t < 15 / 22) {
        return 121 / 8 * (t * t - t) + 137 / 32;
      } else if (t < 19 / 22) {
        return amplitude * 121 / 8 * (t * t - 17 / 11 * t + 285 / 484) + 1;
      } else if (t < 21 / 22) {
        return amplitude * 121 / 8 * (t * t - 20 / 11 * t + 399 / 484) + 1;
      }
      return amplitude * 121 / 8 * (t * t - 43 / 22 * t + 21 / 22) + 1;
    case Easing.OutInBounce:
      if (t < 4 / 22) {
        return 121 / 8 * t * t;
      } else if (t < 8 / 22) {
        return -amplitude * 121 / 8 * (t * t - 6 / 11 * t + 8 / 121) + 0.5;
      } else if (t < 10 / 22) {
        return -amplitude * 121 / 8 * (t * t - 9 / 11 * t + 20 / 121) + 0.5;
      } else if (t < 11 / 22) {
        return -amplitude * 121 / 8 * (t * t - 21 / 22 * t + 5 / 22) + 0.5;
      } else if (t < 12 / 22) {
        return amplitude * 121 / 8 * (t * t - 23 / 22 * t + 3 / 11) + 0.5;
      } else if (t < 14 / 22) {
        return amplitude * 121 / 8 * (t * t - 13 / 11 * t + 42 / 121) + 0.5;
      } else if (t < 18 / 22) {
        return amplitude * 121 / 8 * (t * t - 16 / 11 * t + 63 / 121) + 0.5;
      }
      return -121 / 8 * (t * t - 2 * t + 117 / 121) + 0.5;

    // Default
    default:
      console.error("Unsupported animation type: ", type);
      return t;
  }
};

QmlWeb.Easing = Easing;

/* eslint accessor-pairs: 0 */

function setupGetter(obj, propName, func) {
  Object.defineProperty(obj, propName, {
    get: func,
    configurable: true,
    enumerable: true
  });
}

function setupSetter(obj, propName, func) {
  Object.defineProperty(obj, propName, {
    set: func,
    configurable: true,
    enumerable: false
  });
}

function setupGetterSetter(obj, propName, getter, setter) {
  Object.defineProperty(obj, propName, {
    get: getter,
    set: setter,
    configurable: true,
    enumerable: false
  });
}

QmlWeb.setupGetter = setupGetter;
QmlWeb.setupSetter = setupSetter;
QmlWeb.setupGetterSetter = setupGetterSetter;

var QmlWebHelpers = function () {
  function QmlWebHelpers() {
    _classCallCheck(this, QmlWebHelpers);
  }

  _createClass(QmlWebHelpers, null, [{
    key: "arrayFindIndex",
    value: function arrayFindIndex(array, callback) {
      // Note: does not support thisArg, we don't need that
      if (!Array.prototype.findIndex) {
        for (var key in array) {
          if (callback(array[key], key, array)) {
            return key;
          }
        }
        return -1;
      }
      return Array.prototype.findIndex.call(array, callback);
    }
  }, {
    key: "mergeObjects",
    value: function mergeObjects() {
      var merged = {};

      for (var _len6 = arguments.length, args = Array(_len6), _key6 = 0; _key6 < _len6; _key6++) {
        args[_key6] = arguments[_key6];
      }

      for (var i in args) {
        var arg = args[i];
        if (!arg) {
          continue;
        }
        for (var key in arg) {
          merged[key] = arg[key];
        }
      }
      return merged;
    }
  }]);

  return QmlWebHelpers;
}();

QmlWeb.helpers = QmlWebHelpers;

/* @license

MIT License

Copyright (c) 2011 Lauri Paimen <lauri@paimen.info>
Copyright (c) 2015 Pavel Vasev <pavel.vasev@gmail.com> - initial and working
                                                         import implementation.
Copyright (c) 2016 QmlWeb contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

/**
 * Get URL contents.
 * @param url {String} Url to fetch.
 * @param skipExceptions {bool} when turned on, ignore exeptions and return
 *        false. This feature is used by readQmlDir.
 * @private
 * @return {mixed} String of contents or false in errors.
 */
function getUrlContents(url, skipExceptions) {
  if (typeof QmlWeb.urlContentCache[url] === "undefined") {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, false);

    if (skipExceptions) {
      try {
        xhr.send(null);
      } catch (e) {
        return false;
      }
      // it is OK to not have logging here, because DeveloperTools already will
      // have red log record
    } else {
      xhr.send(null);
    }

    if (xhr.status !== 200 && xhr.status !== 0) {
      // 0 if accessing with file://
      console.log("Retrieving " + url + " failed: " + xhr.responseText, xhr);
      return false;
    }
    QmlWeb.urlContentCache[url] = xhr.responseText;
  }
  return QmlWeb.urlContentCache[url];
}
if (typeof QmlWeb.urlContentCache === "undefined") {
  QmlWeb.urlContentCache = {};
}

/**
 * Read qmldir spec file at directory.
 * @param url Url of the directory
 * @return {Object} Object, where .internals lists qmldir internal references
 *                          and .externals lists qmldir external references.
 */

/*  Note on how importing works.

parseQML gives us `tree.$imports` variable, which contains information from
`import` statements.

After each call to parseQML, we call engine.loadImports(tree.$imports).
It in turn invokes readQmlDir() calls for each import, with respect to current
component base path and engine.importPathList().

We keep all component names from all qmldir files in global variable
`engine.qmldir`.

In construct() function, we use `engine.qmldir` for component url lookup.

Reference import info: http://doc.qt.io/qt-5/qtqml-syntax-imports.html
Also please look at notes and TODO's in qtcore.js::loadImports() and
qtcore.js::construct() methods.
*/

function readQmlDir(url) {
  // in case 'url' is empty, do not attach "/"
  // Q1: when this happen?
  var qmldirFileUrl = url.length > 0 ? url + "/qmldir" : "qmldir";

  var parsedUrl = QmlWeb.engine.$parseURI(qmldirFileUrl);

  var qmldir = void 0;
  if (parsedUrl.scheme === "qrc://") {
    qmldir = QmlWeb.qrc[parsedUrl.path];
  } else {
    qmldir = getUrlContents(qmldirFileUrl, true) || undefined;
  }

  var internals = {};
  var externals = {};

  if (qmldir === undefined) {
    return false;
  }

  // we have to check for "://"
  // In that case, item path is meant to be absolute, and we have no need to
  // prefix it with base url
  function makeurl(path) {
    if (path.indexOf("://") > 0) {
      return path;
    }
    return url + "/" + path;
  }

  var lines = qmldir.split(/\r?\n/);
  for (var i = 0; i < lines.length; i++) {
    // trim
    var line = lines[i].replace(/^\s+|\s+$/g, "");
    if (!line.length || line[0] === "#") {
      // Empty line or comment
      continue;
    }
    var match = line.split(/\s+/);
    if (match.length === 2 || match.length === 3) {
      if (match[0] === "plugin") {
        console.log(url + ": qmldir plugins are not supported!");
      } else if (match[0] === "internal") {
        internals[match[1]] = { url: makeurl(match[2]) };
      } else if (match.length === 2) {
        externals[match[0]] = { url: makeurl(match[1]) };
      } else {
        externals[match[0]] = { url: makeurl(match[2]), version: match[1] };
      }
    } else {
      console.log(url + ": unmatched: " + line);
    }
  }
  return { internals: internals, externals: externals };
}

QmlWeb.getUrlContents = getUrlContents;
QmlWeb.readQmlDir = readQmlDir;

function importJavascriptInContext(jsData, $context) {
  /* Remove any ".pragma" statements, as they are not valid JavaScript */
  var source = jsData.source.replace(/\.pragma.*(?:\r\n|\r|\n)/, "\n");
  // TODO: pass more objects to the scope?
  new Function("jsData", "$context", "\n    with(QmlWeb) with ($context) {\n      " + source + "\n    }\n    " + jsData.exports.map(function (sym) {
    return "$context." + sym + " = " + sym + ";";
  }).join("") + "\n  ")(jsData, $context);
}

QmlWeb.importJavascriptInContext = importJavascriptInContext;

QmlWeb.keyCodeToQt = function (e) {
  var Qt = QmlWeb.Qt;
  e.keypad = e.keyCode >= 96 && e.keyCode <= 111;
  if (e.keyCode === Qt.Key_Tab && e.shiftKey) {
    return Qt.Key_Backtab;
  }
  if (e.keyCode >= 97 && e.keyCode <= 122) {
    return e.keyCode - (97 - Qt.Key_A);
  }
  return e.keyCode;
};

QmlWeb.eventToKeyboard = function (e) {
  return {
    accepted: false,
    count: 1,
    isAutoRepeat: false,
    key: QmlWeb.keyCodeToQt(e),
    modifiers: e.ctrlKey * QmlWeb.Qt.CtrlModifier | e.altKey * QmlWeb.Qt.AltModifier | e.shiftKey * QmlWeb.Qt.ShiftModifier | e.metaKey * QmlWeb.Qt.MetaModifier | e.keypad * QmlWeb.Qt.KeypadModifier,
    text: String.fromCharCode(e.charCode)
  };
};

QmlWeb.keyboardSignals = {};
["asterisk", "back", "backtab", "call", "cancel", "delete", "escape", "flip", 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, "hangup", "menu", "no", "return", "select", "space", "tab", "volumeDown", "volumeUp", "yes", "up", "right", "down", "left"].forEach(function (key) {
  var name = key.toString();
  var qtName = "Key_" + name[0].toUpperCase() + name.slice(1);
  var prefix = typeof key === "number" ? "digit" : "";
  QmlWeb.keyboardSignals[QmlWeb.Qt[qtName]] = "" + prefix + name + "Pressed";
});

QmlWeb.executionContext = null;

var modules = {
  Main: {
    int: QmlWeb.qmlInteger,
    real: QmlWeb.qmlNumber,
    double: QmlWeb.qmlNumber,
    string: QmlWeb.qmlString,
    bool: QmlWeb.qmlBoolean,
    list: QmlWeb.qmlList,
    color: QmlWeb.QColor,
    enum: QmlWeb.qmlNumber,
    url: QmlWeb.qmlUrl,
    variant: QmlWeb.qmlVariant,
    var: QmlWeb.qmlVariant
  }
};

// All object constructors
QmlWeb.constructors = modules.Main;

var dependants = {};

var perImportContextConstructors = {};
var importContextIds = 0;

// Helper. Adds a type to the constructor list
function registerGlobalQmlType(name, type) {
  QmlWeb[type.name] = type;
  QmlWeb.constructors[name] = type;
  modules.Main[name] = type;
}

// Helper. Register a type to a module
function registerQmlType(options, constructor) {
  if (constructor !== undefined) {
    options.constructor = constructor;
  }

  if (typeof options.baseClass === "string") {
    // TODO: Does not support version specification (yet?)
    var baseModule = void 0;
    var baseName = void 0;
    var dot = options.baseClass.lastIndexOf(".");
    if (dot === -1) {
      baseModule = options.module;
      baseName = options.baseClass;
    } else {
      baseModule = options.baseClass.substring(0, dot);
      baseName = options.baseClass.substring(dot + 1);
    }
    var found = (modules[baseModule] || []).filter(function (descr) {
      return descr.name === baseName;
    });
    if (found.length > 0) {
      // Ok, we found our base class
      options.baseClass = found[0].constructor;
    } else {
      // Base class not found, delay the loading
      var baseId = [baseModule, baseName].join(".");
      if (!dependants.hasOwnProperty(baseId)) {
        dependants[baseId] = [];
      }
      dependants[baseId].push(options);
      return;
    }
  }

  var descriptor = typeof options === "function" ? {
    module: options.module,
    name: options.element,
    versions: options.versions,
    baseClass: options.baseClass,
    enums: options.enums,
    signals: options.signals,
    defaultProperty: options.defaultProperty,
    properties: options.properties,
    constructor: options
  } : options;

  descriptor.constructor.$qmlTypeInfo = {
    enums: descriptor.enums,
    signals: descriptor.signals,
    defaultProperty: descriptor.defaultProperty,
    properties: descriptor.properties
  };

  if (descriptor.global) {
    registerGlobalQmlType(descriptor.name, descriptor.constructor);
  }

  var moduleDescriptor = {
    name: descriptor.name,
    versions: descriptor.versions,
    constructor: descriptor.constructor
  };

  if (typeof modules[descriptor.module] === "undefined") {
    modules[descriptor.module] = [];
  }
  modules[descriptor.module].push(moduleDescriptor);

  if (typeof descriptor.baseClass !== "undefined") {
    inherit(descriptor.constructor, descriptor.baseClass);
  }

  var id = [descriptor.module, descriptor.name].join(".");
  if (dependants.hasOwnProperty(id)) {
    dependants[id].forEach(function (opt) {
      return registerQmlType(opt);
    });
    dependants[id].length = 0;
  }
}

function getConstructor(moduleName, version, name) {
  if (typeof modules[moduleName] !== "undefined") {
    for (var i = 0; i < modules[moduleName].length; ++i) {
      var type = modules[moduleName][i];
      if (type.name === name && type.versions.test(version)) {
        return type.constructor;
      }
    }
  }
  return null;
}

function getModuleConstructors(moduleName, version) {
  var constructors = {};
  if (typeof modules[moduleName] === "undefined") {
    console.warn("module \"" + moduleName + "\" not found");
    return constructors;
  }
  for (var i = 0; i < modules[moduleName].length; ++i) {
    var module = modules[moduleName][i];
    if (module.versions.test(version)) {
      constructors[module.name] = module.constructor;
    }
  }
  return constructors;
}

function loadImports(self, imports) {
  var mergeObjects = QmlWeb.helpers.mergeObjects;
  var constructors = mergeObjects(modules.Main);
  if (imports.filter(function (row) {
    return row[1] === "QtQml";
  }).length === 0 && imports.filter(function (row) {
    return row[1] === "QtQuick";
  }).length === 1) {
    imports.push(["qmlimport", "QtQml", 2, "", true]);
  }
  for (var i = 0; i < imports.length; ++i) {
    var _imports$i = _slicedToArray(imports[i], 4),
        moduleName = _imports$i[1],
        moduleVersion = _imports$i[2],
        moduleAlias = _imports$i[3];

    var moduleConstructors = getModuleConstructors(moduleName, moduleVersion);

    if (moduleAlias !== "") {
      constructors[moduleAlias] = mergeObjects(constructors[moduleAlias], moduleConstructors);
    } else {
      constructors = mergeObjects(constructors, moduleConstructors);
    }
  }
  self.importContextId = importContextIds++;
  perImportContextConstructors[self.importContextId] = constructors;
  QmlWeb.constructors = constructors; // TODO: why do we need this?
}

function inherit(constructor, baseClass) {
  var oldProto = constructor.prototype;
  constructor.prototype = Object.create(baseClass.prototype);
  Object.getOwnPropertyNames(oldProto).forEach(function (prop) {
    constructor.prototype[prop] = oldProto[prop];
  });
  constructor.prototype.constructor = baseClass;
}

function callSuper(self, meta) {
  var info = meta.super.$qmlTypeInfo || {};
  meta.super = meta.super.prototype.constructor;
  meta.super.call(self, meta);

  if (info.enums) {
    // TODO: not exported to the whole file scope yet
    Object.keys(info.enums).forEach(function (name) {
      self[name] = info.enums[name];

      if (!global[name]) {
        global[name] = self[name]; // HACK
      }
    });
  }
  if (info.properties) {
    Object.keys(info.properties).forEach(function (name) {
      var desc = info.properties[name];
      if (typeof desc === "string") {
        desc = { type: desc };
      }
      QmlWeb.createProperty(desc.type, self, name, desc);
    });
  }
  if (info.signals) {
    Object.keys(info.signals).forEach(function (name) {
      var params = info.signals[name];
      self[name] = QmlWeb.Signal.signal(params);
    });
  }
  if (info.defaultProperty) {
    self.$defaultProperty = info.defaultProperty;
  }
}

/**
 * QML Object constructor.
 * @param {Object} meta Meta information about the object and the creation
 *                      context
 * @return {Object} New qml object
 */
function construct(meta) {
  var item = void 0;

  var constructors = perImportContextConstructors[meta.context.importContextId];

  var classComponents = meta.object.$class.split(".");
  for (var ci = 0; ci < classComponents.length; ++ci) {
    var c = classComponents[ci];
    constructors = constructors[c];
    if (constructors === undefined) {
      break;
    }
  }

  if (constructors !== undefined) {
    var _constructor = constructors;
    meta.super = _constructor;
    item = new _constructor(meta);
    meta.super = undefined;
  } else {
    // Load component from file. Please look at import.js for main notes.
    // Actually, we have to use that order:
    // 1) try to load component from current basePath
    // 2) from importPathList
    // 3) from directories in imports statements and then
    // 4) from qmldir files
    // Currently we support only 1,2 and 4 and use order: 4,1,2
    // TODO: engine.qmldirs is global for all loaded components.
    //       That's not qml's original behaviour.
    var qdirInfo = QmlWeb.engine.qmldirs[meta.object.$class];
    // Are we have info on that component in some imported qmldir files?

    /* This will also be set in applyProperties, but needs to be set here
     * for Qt.createComponent to have the correct context. */
    QmlWeb.executionContext = meta.context;

    var filePath = void 0;
    if (qdirInfo) {
      filePath = qdirInfo.url;
    } else if (classComponents.length === 2) {
      var qualified = QmlWeb.engine.qualifiedImportPath(meta.context.importContextId, classComponents[0]);
      filePath = "" + qualified + classComponents[1] + ".qml";
    } else {
      filePath = classComponents[0] + ".qml";
    }

    var component = QmlWeb.Qt.createComponent(filePath);

    if (!component) {
      throw new Error("No constructor found for " + meta.object.$class);
    }

    item = component.$createObject(meta.parent);
    if (typeof item.dom !== "undefined") {
      item.dom.className += " " + classComponents[classComponents.length - 1];
      if (meta.object.id) {
        item.dom.className += "  " + meta.object.id;
      }
    }
    // Handle default properties
  }

  // id
  if (meta.object.id) {
    QmlWeb.setupGetterSetter(meta.context, meta.object.id, function () {
      return item;
    }, function () {});
  }

  // keep path in item for probale use it later in Qt.resolvedUrl
  item.$context.$basePath = QmlWeb.engine.$basePath; //gut

  // We want to use the item's scope, but this Component's imports
  item.$context.importContextId = meta.context.importContextId;

  // Apply properties (Bindings won't get evaluated, yet)
  QmlWeb.applyProperties(meta.object, item, item, item.$context);

  return item;
}

QmlWeb.modules = modules;
QmlWeb.registerGlobalQmlType = registerGlobalQmlType;
QmlWeb.registerQmlType = registerQmlType;
QmlWeb.getConstructor = getConstructor;
QmlWeb.loadImports = loadImports;
QmlWeb.callSuper = callSuper;
QmlWeb.construct = construct;

/**
 * Create property getters and setters for object.
 * @param {Object} obj Object for which gsetters will be set
 * @param {String} propName Property name
 * @param {Object} [options] Options that allow finetuning of the property
 */
function createProperty(type, obj, propName) {
  var options = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : {};

  var QMLProperty = QmlWeb.QMLProperty;
  var prop = new QMLProperty(type, obj, propName);
  obj[propName + "Changed"] = prop.changed;
  obj.$properties[propName] = prop;
  obj.$properties[propName].set(options.initialValue, QMLProperty.ReasonInit);

  var getter = function getter() {
    return obj.$properties[propName].get();
  };
  var setter = void 0;
  if (options.readOnly) {
    setter = function setter(newVal) {
      if (!obj.$canEditReadOnlyProperties) {
        throw new Error("property '" + propName + "' has read only access");
      }
      obj.$properties[propName].set(newVal, QMLProperty.ReasonUser);
    };
  } else {
    setter = function setter(newVal) {
      obj.$properties[propName].set(newVal, QMLProperty.ReasonUser);
    };
  }
  QmlWeb.setupGetterSetter(obj, propName, getter, setter);
  if (obj.$isComponentRoot) {
    QmlWeb.setupGetterSetter(obj.$context, propName, getter, setter);
  }
}

/**
 * Apply properties from metaObject to item.
 * @param {Object} metaObject Source of properties
 * @param {Object} item Target of property apply
 * @param {Object} objectScope Scope in which properties should be evaluated
 * @param {Object} componentScope Component scope in which properties should be
 *                 evaluated
 */
function applyProperties(metaObject, item, objectScopeIn, componentScope) {
  var QMLProperty = QmlWeb.QMLProperty;
  var objectScope = objectScopeIn || item;
  QmlWeb.executionContext = componentScope;

  if (metaObject.$children && metaObject.$children.length !== 0) {
    if (item.$defaultProperty) {
      item.$properties[item.$defaultProperty].set(metaObject.$children, QMLProperty.ReasonInit, objectScope, componentScope);
    } else {
      throw new Error("Cannot assign to unexistant default property");
    }
  }
  // We purposefully set the default property AFTER using it, in order to only
  // have it applied for instanciations of this component, but not for its
  // internal children
  if (metaObject.$defaultProperty) {
    item.$defaultProperty = metaObject.$defaultProperty;
  }

  for (var i in metaObject) {
    var value = metaObject[i];
    if (i === "id" || i === "$class") {
      // keep them
      item[i] = value;
      continue;
    }

    // skip global id's and internal values
    if (i === "id" || i[0] === "$") {
      // TODO: what? See above.
      continue;
    }

    // slots
    if (i.indexOf("on") === 0 && i[2].toUpperCase() === i[2]) {
      var signalName = i[2].toLowerCase() + i.slice(3);
      if (!connectSignal(item, signalName, value, objectScope, componentScope)) {
        if (item.$setCustomSlot) {
          item.$setCustomSlot(signalName, value, objectScope, componentScope);
        }
      }
      continue;
    }

    if (value instanceof Object) {
      if (applyProperty(item, i, value, objectScope, componentScope)) {
        continue;
      }
    }

    if (item.$properties && i in item.$properties) {
      item.$properties[i].set(value, QMLProperty.ReasonInit, objectScope, componentScope);
    } else if (i in item) {
      item[i] = value;
    } else if (item.$setCustomData) {
      item.$setCustomData(i, value);
    } else {
      console.warn("Cannot assign to non-existent property \"" + i + "\". Ignoring assignment.");
    }
  }
}

function applyProperty(item, i, value, objectScope, componentScope) {
  var QMLProperty = QmlWeb.QMLProperty;

  if (value instanceof QmlWeb.QMLSignalDefinition) {
    item[i] = QmlWeb.Signal.signal(value.parameters);
    if (item.$isComponentRoot) {
      componentScope[i] = item[i];
    }
    return true;
  }

  if (value instanceof QmlWeb.QMLMethod) {
    value.compile();
    item[i] = value.eval(objectScope, componentScope, componentScope.$basePath);
    if (item.$isComponentRoot) {
      componentScope[i] = item[i];
    }
    return true;
  }

  if (value instanceof QmlWeb.QMLAliasDefinition) {
    // TODO
    // 1. Alias must be able to point to prop or id of local object,
    //    eg: property alias q: t
    // 2. Alias may have same name as id it points to: property alias
    //    someid: someid
    // 3. Alias proxy (or property proxy) to proxy prop access to selected
    //    incapsulated object. (think twice).
    createProperty("alias", item, i);
    item.$properties[i].componentScope = componentScope;
    item.$properties[i].componentScopeBasePath = componentScope.$basePath;
    item.$properties[i].val = value;
    item.$properties[i].get = function () {
      var obj = this.componentScope[this.val.objectName];
      var propertyName = this.val.propertyName;
      return propertyName ? obj.$properties[propertyName].get() : obj;
    };
    item.$properties[i].set = function (newVal, reason, _objectScope, _componentScope) {
      if (!this.val.propertyName) {
        throw new Error("Cannot set alias property pointing to an QML object.");
      }
      var obj = this.componentScope[this.val.objectName];
      var prop = obj.$properties[this.val.propertyName];
      prop.set(newVal, reason, _objectScope, _componentScope);
    };

    if (value.propertyName) {
      var con = function con(prop) {
        var obj = prop.componentScope[prop.val.objectName];
        if (!obj) {
          console.error("qtcore: target object ", prop.val.objectName, " not found for alias ", prop);
        } else {
          var targetProp = obj.$properties[prop.val.propertyName];
          if (!targetProp) {
            console.error("qtcore: target property [", prop.val.objectName, "].", prop.val.propertyName, " not found for alias ", prop.name);
          } else {
            // targetProp.changed.connect( prop.changed );
            // it is not sufficient to connect to `changed` of source property
            // we have to propagate own changed to it too
            // seems the best way to do this is to make them identical?..
            // prop.changed = targetProp.changed;
            // obj[`${i}Changed`] = prop.changed;
            // no. because those object might be destroyed later.
            var loopWatchdog = false;
            targetProp.changed.connect(item, function () {
              for (var _len7 = arguments.length, args = Array(_len7), _key7 = 0; _key7 < _len7; _key7++) {
                args[_key7] = arguments[_key7];
              }

              if (loopWatchdog) return;
              loopWatchdog = true;
              prop.changed.apply(item, args);
              loopWatchdog = false;
            });
            prop.changed.connect(obj, function () {
              for (var _len8 = arguments.length, args = Array(_len8), _key8 = 0; _key8 < _len8; _key8++) {
                args[_key8] = arguments[_key8];
              }

              if (loopWatchdog) return;
              loopWatchdog = true;
              targetProp.changed.apply(obj, args);
              loopWatchdog = false;
            });
          }
        }
      };
      QmlWeb.engine.pendingOperations.push([con, item.$properties[i]]);
    }
    return true;
  }

  if (value instanceof QmlWeb.QMLPropertyDefinition) {
    createProperty(value.type, item, i);
    item.$properties[i].set(value.value, QMLProperty.ReasonInit, objectScope, componentScope);
    return true;
  }

  if (item[i] && value instanceof QmlWeb.QMLMetaPropertyGroup) {
    // Apply properties one by one, otherwise apply at once
    applyProperties(value, item[i], objectScope, componentScope);
    return true;
  }

  return false;
}

function connectSignal(item, signalName, value, objectScope, componentScope) {
  if (!item[signalName]) {
    console.warn("No signal called " + signalName + " found!");
    return undefined;
  } else if (typeof item[signalName].connect !== "function") {
    console.warn(signalName + " is not a signal!");
    return undefined;
  }

  if (!value.compiled) {
    var params = [];
    for (var j in item[signalName].parameters) {
      params.push(item[signalName].parameters[j].name);
    }
    // Wrap value.src in IIFE in case it includes a "return"
    value.src = "(\n      function(" + params.join(", ") + ") {\n        QmlWeb.executionContext = __executionContext;\n        QmlWeb.engine.$oldBasePath = QmlWeb.engine.$basePath;\n        QmlWeb.engine.$basePath = \"" + componentScope.$basePath + "\";\n        try {\n          (function() {\n            " + value.src + "\n          })();\n        } finally {\n          QmlWeb.engine.$basePath = QmlWeb.engine.$oldBasePath;\n        }\n      }\n    )";
    value.isFunction = false;
    value.compile();
  }
  // Don't pass in __basePath argument, as QMLEngine.$basePath is set in the
  // value.src, as we need it set at the time the slot is called.
  var slot = value.eval(objectScope, componentScope);
  item[signalName].connect(item, slot);
  return slot;
}

QmlWeb.createProperty = createProperty;
QmlWeb.applyProperties = applyProperties;
QmlWeb.connectSignal = connectSignal;

/* @license

MIT License

Copyright (c) 2011 Lauri Paimen <lauri@paimen.info>
Copyright (c) 2013 Anton Kreuzkamp <akreuzkamp@web.de>
Copyright (c) 2016 QmlWeb contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

var QMLMethod = function (_QmlWeb$QMLBinding) {
  _inherits(QMLMethod, _QmlWeb$QMLBinding);

  function QMLMethod() {
    _classCallCheck(this, QMLMethod);

    return _possibleConstructorReturn(this, (QMLMethod.__proto__ || Object.getPrototypeOf(QMLMethod)).apply(this, arguments));
  }

  return QMLMethod;
}(QmlWeb.QMLBinding);

/**
 * Create an object representing a QML property definition.
 * @param {String} type The type of the property
 * @param {Array} value The default value of the property
 * @return {Object} Object representing the defintion
 */


var QMLPropertyDefinition = function QMLPropertyDefinition(type, value) {
  _classCallCheck(this, QMLPropertyDefinition);

  this.type = type;
  this.value = value;
};

var QMLAliasDefinition = function QMLAliasDefinition(objName, propName) {
  _classCallCheck(this, QMLAliasDefinition);

  this.objectName = objName;
  this.propertyName = propName;
};

/**
 * Create an object representing a QML signal definition.
 * @param {Array} params The parameters the signal ships
 * @return {Object} Object representing the defintion
 */


var QMLSignalDefinition = function QMLSignalDefinition(params) {
  _classCallCheck(this, QMLSignalDefinition);

  this.parameters = params;
};

/**
 * Create an object representing a group of QML properties (like anchors).
 * @return {Object} Object representing the group
 */


var QMLMetaPropertyGroup = function QMLMetaPropertyGroup() {
  _classCallCheck(this, QMLMetaPropertyGroup);
};

/**
 * Create an object representing a QML element.
 * @param {String} type Type of the element
 * @param {String} onProp Name of the property specified with the "on" keyword
 */


var QMLMetaElement = function QMLMetaElement(type, onProp) {
  _classCallCheck(this, QMLMetaElement);

  this.$class = type;
  this.$children = [];
  this.$on = onProp;
};

// Convert parser tree to the format understood by engine


function convertToEngine(tree) {
  return convertToEngine.walk(tree);
}

function stringifyDots(elem) {
  var sub = elem;
  var path = [];
  while (sub[0] === "dot") {
    path.push(sub[1]);
    sub = sub[2];
  }
  path.push(sub);
  return path.join(".");
}

function applyProp(item, name, val) {
  var curr = item; // output structure
  var sub = name; // input structure
  while (sub[0] === "dot") {
    if (!curr[sub[1]]) {
      curr[sub[1]] = new QMLMetaPropertyGroup();
    }
    curr = curr[sub[1]];
    sub = sub[2];
  }
  curr[sub] = val;
}

convertToEngine.walkers = {
  toplevel: function toplevel(imports, statement) {
    var item = { $class: "Component" };
    item.$imports = imports;
    item.$children = [convertToEngine.walk(statement)];
    return item;
  },
  qmlelem: function qmlelem(elem, onProp, statements) {
    var item = new QMLMetaElement(stringifyDots(elem), onProp);

    for (var i in statements) {
      var statement = statements[i];
      var name = statement[1];
      var val = convertToEngine.walk(statement);
      switch (statement[0]) {
        case "qmldefaultprop":
          item.$defaultProperty = name;
          item[name] = val;
          break;
        case "qmlprop":
        case "qmlpropdef":
        case "qmlaliasdef":
        case "qmlmethod":
        case "qmlsignaldef":
          applyProp(item, name, val);
          break;
        case "qmlelem":
          item.$children.push(val);
          break;
        case "qmlobjdef":
          throw new Error("qmlobjdef support was removed, update qmlweb-parser to ^0.3.0.");
        case "qmlobj":
          // Create object to item
          item[name] = item[name] || new QMLMetaPropertyGroup();
          for (var j in val) {
            item[name][j] = val[j];
          }
          break;
        default:
          console.log("Unknown statement", statement);
      }
    }
    // Make $children be either a single item or an array, if it's more than one
    if (item.$children.length === 1) {
      item.$children = item.$children[0];
    }

    return item;
  },
  qmlprop: function qmlprop(name, tree, src) {
    if (name === "id") {
      // id property
      return tree[1][1];
    }
    return convertToEngine.bindout(tree, src);
  },
  qmlobjdef: function qmlobjdef(name, property, tree, src) {
    return convertToEngine.bindout(tree, src);
  },
  qmlobj: function qmlobj(elem, statements) {
    var item = {};
    for (var i in statements) {
      var statement = statements[i];
      var name = statement[1];
      var val = convertToEngine.walk(statement);
      if (statement[0] === "qmlprop") {
        applyProp(item, name, val);
      }
    }
    return item;
  },
  qmlmethod: function qmlmethod(name, tree, src) {
    return new QMLMethod(src);
  },
  qmlpropdef: function qmlpropdef(name, type, tree, src) {
    return new QMLPropertyDefinition(type, tree ? convertToEngine.bindout(tree, src) : undefined);
  },
  qmlaliasdef: function qmlaliasdef(name, objName, propName) {
    return new QMLAliasDefinition(objName, propName);
  },
  qmlsignaldef: function qmlsignaldef(name, params) {
    return new QMLSignalDefinition(params);
  },
  qmldefaultprop: function qmldefaultprop(tree) {
    return convertToEngine.walk(tree);
  },
  name: function name(src) {
    if (src === "true" || src === "false") {
      return src === "true";
    } else if (typeof src === "boolean") {
      // TODO: is this needed? kept for compat with ==
      return src;
    }
    return new QmlWeb.QMLBinding(src, ["name", src]);
  },
  num: function num(src) {
    return +src;
  },
  string: function string(src) {
    return String(src);
  },
  array: function array(tree, src) {
    var a = [];
    var isList = false;
    var hasBinding = false;
    for (var i in tree) {
      var val = convertToEngine.bindout(tree[i]);
      a.push(val);

      if (val instanceof QMLMetaElement) {
        isList = true;
      } else if (val instanceof QmlWeb.QMLBinding) {
        hasBinding = true;
      }
    }

    if (hasBinding) {
      if (isList) {
        throw new TypeError("An array may either contain bindings or Element definitions.");
      }
      return new QmlWeb.QMLBinding(src, tree);
    }

    return a;
  }
};

convertToEngine.walk = function (tree) {
  var type = tree[0];
  var walker = convertToEngine.walkers[type];
  if (!walker) {
    console.log("No walker for " + type);
    return undefined;
  }
  return walker.apply(type, tree.slice(1));
};

// Try to bind out tree and return static variable instead of binding
convertToEngine.bindout = function (statement, binding) {
  // We want to process the content of the statement
  // (but still handle the case, we get the content directly)
  var tree = statement[0] === "stat" ? statement[1] : statement;

  var type = tree[0];
  var walker = convertToEngine.walkers[type];
  if (walker) {
    return walker.apply(type, tree.slice(1));
  }
  return new QmlWeb.QMLBinding(binding, tree);
};

// Help logger
convertToEngine.amIn = function (str, tree) {
  console.log(str);
  if (tree) console.log(JSON.stringify(tree, null, "  "));
};

function loadParser() {
  if (typeof QmlWeb.parse !== "undefined") {
    return;
  }

  console.log("Loading parser...");
  var tags = document.getElementsByTagName("script");
  for (var i in tags) {
    if (tags[i].src && tags[i].src.indexOf("/qt.") !== -1) {
      var src = tags[i].src.replace("/qt.", "/qmlweb.parser.");
      // TODO: rewrite to async loading
      var xhr = new XMLHttpRequest();
      xhr.open("GET", src, false);
      xhr.send(null);
      if (xhr.status !== 200 && xhr.status !== 0) {
        // xhr.status === 0 if accessing with file://
        throw new Error("Could not load QmlWeb parser!");
      }
      new Function(xhr.responseText)();
      QmlWeb.parse = QmlWeb.parse;
      QmlWeb.jsparse = QmlWeb.jsparse;
      return;
    }
  }
}

// Function to parse qml and output tree expected by engine
function parseQML(src, file) {
  loadParser();
  QmlWeb.parse.nowParsingFile = file;
  var parsetree = QmlWeb.parse(src, QmlWeb.parse.QmlDocument);
  return convertToEngine(parsetree);
}

QmlWeb.QMLMethod = QMLMethod;
QmlWeb.QMLPropertyDefinition = QMLPropertyDefinition;
QmlWeb.QMLAliasDefinition = QMLAliasDefinition;
QmlWeb.QMLSignalDefinition = QMLSignalDefinition;
QmlWeb.QMLMetaPropertyGroup = QMLMetaPropertyGroup;
QmlWeb.QMLMetaElement = QMLMetaElement;
QmlWeb.convertToEngine = convertToEngine;
QmlWeb.loadParser = loadParser;
QmlWeb.parseQML = parseQML;

/*

QmlWeb.qrc is analogous to the Qt Resource System. It is expected to map a path
within the resource system to the following pieces of data:

1) For a QML Component, it is the return value of QmlWeb.parse
2) For a JavaScript file, it is the return value of QmlWeb.jsparse
2) For an image, it is any URL that an <img> tag can accept (e.g. a standard
   URL to an image resource, or a "data:" URI). If there is no entry for a
   given qrc image path, it will fall back to passing the path right through to
   the DOM. This is mainly a convenience until support for images is added to
   gulp-qmlweb.

The "data-qml" tag on <body> can be set to a "qrc://" URL like
"qrc:///root.qml" to use a pre-parsed "/root.qml" from QmlWeb.qrc.

Since relative URLs are resolved relative to the URL of the containing
component, any relative URL set within a file in the resource system will also
resolve within the resource system. To access a Component, JavaScript or image
file that is stored outside of the resources system from within the resource
system, a full URL must be used (e.g. "http://www.example.com/images/foo.png").

Vice-versa, in order to access a Component, JavaScript or image file that is
stored within the resource system from outside of the resource system, a full
"qrc://" URL must be used (e.g. "qrc:///images/foo.png").

More details here: http://doc.qt.io/qt-5/qml-url.html

*/
QmlWeb.qrc = {};

{
  var BACKGROUNDCOLOR = ['red', 'orange', 'yellow', 'olive', 'green', 'teal', 'blue', 'violet', 'purple', 'pink', 'brown', 'grey', 'black'];

  QmlWeb.registerQmlType({
    module: "DGrid",
    name: "DButtonColumn",
    versions: /.*/,
    baseClass: "DGrid.DColumn", // no UI
    properties: {},
    signals: {
      clicked: [{ 'name': 'button', 'type': 'var' }]
    }
  }, function () {
    function _class(meta) {
      var _this6 = this;

      _classCallCheck(this, _class);

      QmlWeb.callSuper(this, meta);
      this.doc_auto_input = true;
      this.doc_type = "Button";
      this.renderCell = function (object) {
        var value = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : "";
        var node = arguments[2];
        var options = arguments[3];

        var field = _this6.grid.cell(node).column.field,
            icon = object[field + "_icon"],
            backgroundColor = object[field + "_backgroundColor"];

        _this6.button = document.createElement('button');
        _this6.button.style.display = "block";
        _this6.button.style.marginLeft = "auto";
        _this6.button.style.marginRight = "auto";
        _this6.button.classList.add("ui", "button");
        _this6.button.onclick = function () {
          _this6.clicked(_this6.button);
        };

        if (icon) {
          var _classList;

          var classList = void 0,
              iconNode = void 0;
          iconNode = document.createElement("i");
          classList = iconNode.classList;
          (_classList = classList).add.apply(_classList, _toConsumableArray(icon.split(" ").concat(["icon"])));
          _this6.button.innerHTML = "";
          _this6.button.appendChild(iconNode);
          _this6.button.classList.add("icon");
        }

        if (value) {
          _this6.button.appendChild(document.createTextNode(value));
        }

        if (backgroundColor) {
          _this6.button.style.backgroundColor = "";
          _this6.button.classList.remove(_this6._backgroundColor);
          if (BACKGROUNDCOLOR.includes(backgroundColor)) {
            _this6.button.classList.add(backgroundColor);
          } else {
            _this6.button.style.backgroundColor = backgroundColor;
          }
          _this6._backgroundColor = backgroundColor;
        }

        node.appendChild(_this6.button);
      };
    }

    _createClass(_class, [{
      key: "validateProperty",
      value: function validateProperty(prop) {
        prop = prop.toLowerCase();
        if (backgroundColor.includes(prop)) return [true, "" + prop];
        return [false, ""];
      }
    }]);

    return _class;
  }());
}

QmlWeb.registerQmlType({
  module: "DGrid",
  name: "DCheckBoxColumn",
  versions: /.*/,
  baseClass: "DGrid.DColumn", // no UI
  properties: {
    readonly: "bool"
  },
  signals: {
    clicked: []
  }
}, function () {
  function _class2(meta) {
    var _this7 = this;

    _classCallCheck(this, _class2);

    QmlWeb.callSuper(this, meta);
    this.renderCell = function (object, value, node, options) {
      _this7.checkbox = document.createElement('input');
      _this7.checkbox.type = "checkbox";
      _this7.checkbox.checked = value;
      _this7.checkbox.style.display = "block";
      _this7.checkbox.style.marginLeft = "auto";
      _this7.checkbox.style.marginRight = "auto";
      _this7.checkbox.onclick = function () {
        return !_this7.readonly;
      };
      _this7.checkbox.addEventListener('click', function () {
        return _this7.clicked();
      });
      node.appendChild(_this7.checkbox);
    };
  }

  return _class2;
}());

QmlWeb.registerQmlType({
  module: "DGrid",
  name: "DColumn",
  versions: /.*/,
  baseClass: "QtQml.QtObject", // no UI
  properties: {
    field: "string",
    //id need to be null, unless CompoundColumns bug
    id: { type: "string", initialValue: null },
    children: "var",
    label: "string",
    className: "var", // CSS class or function
    colSpan: "var",
    rowSpan: "var",
    sortable: { type: "bool", initialValue: true },
    get: { type: "var", initialValue: null }, // function
    set: { type: "var", initialValue: null },
    formatter: { type: "var", initialValue: null },
    renderCell: "var",
    //*** Do not uncomment this line!! ***
    // renderHeaderCell cause CompoundColumns bug
    // renderHeaderCell: { type: "var", initialValue: null },
    width: "int",
    hidden: "bool",
    doc_label: "string",
    doc_mandatory: "bool",
    doc_auto_input: "bool",
    doc_read_only: "bool",
    doc_condition: "string",
    doc_remark: "string",
    doc_skip: { type: "bool", initialValue: false },
    doc_type: "string" },
  signals: {}
}, function () {
  function _class3(meta) {
    _classCallCheck(this, _class3);

    QmlWeb.callSuper(this, meta);
  }

  return _class3;
}());

QmlWeb.registerQmlType({
  module: "DGrid",
  name: "DComboBoxColumn",
  versions: /.*/,
  baseClass: "DGrid.DColumn", // no UI
  properties: {
    model: {
      type: "var",
      initialValue: {
        "default": [{ name: "", id: "" }]
      }
    }
  },
  signals: {
    changed: [{ 'name': 'value', 'type': 'var' }, { 'name': 'text', 'type': 'var' }]
  }
}, function () {
  function _class4(meta) {
    var _this8 = this;

    _classCallCheck(this, _class4);

    QmlWeb.callSuper(this, meta);
    this.modelChanged.connect(this, this.$onModelChanged);
    this.renderCell = function (object) {
      var value = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : "";
      var node = arguments[2];
      var options = arguments[3];

      var field = _this8.grid.cell(node).column.field,
          store = _this8.modelMap.get(object[field + "_model"]);

      var dropdownNode = document.createElement("div");
      _this8.inputNode = document.createElement("input");
      _this8.iconNode = document.createElement("i");
      _this8.defaultTextNode = document.createElement("div");
      _this8.menuNode = document.createElement("div");

      dropdownNode.classList.add("ui", "fluid", "selection", "dropdown");
      _this8.inputNode.type = "hidden";
      _this8.inputNode.name = _this8.name;
      _this8.iconNode.classList.add("dropdown", "icon");
      _this8.defaultTextNode.classList.add("default", "text");
      _this8.defaultTextNode.innerHTML = "";
      _this8.menuNode.classList.add("menu");

      store.forEach(function (item) {
        var itemNode = document.createElement("div");
        itemNode.classList.add("item");
        itemNode.setAttribute("data-value", item['id']);
        itemNode.innerHTML = item['name'];
        _this8.menuNode.appendChild(itemNode);
      });

      dropdownNode.appendChild(_this8.inputNode);
      dropdownNode.appendChild(_this8.iconNode);
      dropdownNode.appendChild(_this8.defaultTextNode);
      dropdownNode.appendChild(_this8.menuNode);

      node.appendChild(dropdownNode);
      node.style.overflow = "visible";

      $(document).ready(function () {
        _this8.dropdown = $(dropdownNode).dropdown();
        _this8.dropdown.dropdown("set selected", value);
      });

      dropdownNode.addEventListener("change", function () {
        _this8.changed(_this8.dropdown.dropdown("get value"), _this8.dropdown.dropdown("get text"));
      });
    };
  }

  _createClass(_class4, [{
    key: "extractMap",
    value: function extractMap(value) {
      var splitted = void 0,
          res = {},
          map = value.split(";");

      map = map.filter(function (val) {
        return val && //val is not empty
        val.split(":").length === 2 && //length of splitted val is 2 
        val.split(":")[0] && //the first part of splitted val is not empty
        val.split(":")[1]; //the second part of splitted val is not empty
      });

      map.forEach(function (val) {
        splitted = val.split(":");
        splitted[0] = splitted[0].replace("'", '').trim();
        splitted[1] = splitted[1].replace("'", '').trim();
        res[splitted[0]] = splitted[1];
      });

      return res;
    }
  }, {
    key: "$onModelChanged",
    value: function $onModelChanged() {
      var _this9 = this;

      this.modelMap = new Map();
      this.model.forEach(function (model, index) {
        var modelName = void 0,
            _model = [];
        model.forEach(function (item) {
          //collect items in this model
          if (typeof item !== "string") _model.push(item);
          //get the name of this model
          else if (typeof item === "string") modelName = item;
        });
        //map model name to its model item
        _this9.modelMap.set(modelName, _model);
      });
    }
  }]);

  return _class4;
}());

QmlWeb.registerQmlType({
  module: "DGrid",
  name: "DCompoundColumn",
  versions: /.*/,
  baseClass: "QtQml.QtObject", // no UI
  properties: {
    field: "string",
    label: "string",
    children: "list",
    doc_label: "string",
    doc_mandatory: "bool",
    doc_auto_input: "bool",
    doc_read_only: "bool",
    doc_condition: "string",
    doc_remark: "string",
    doc_skip: { type: "bool", initialValue: false },
    doc_type: "string" },
  signals: {}
}, function () {
  function _class5(meta) {
    _classCallCheck(this, _class5);

    QmlWeb.callSuper(this, meta);
  }

  return _class5;
}());

QmlWeb.registerQmlType({
  module: "DGrid",
  name: "DCustomColumn",
  versions: /.*/,
  baseClass: "DGrid.DColumn", // no UI
  properties: {
    content: "Component"
  },
  defaultProperty: "content",
  signals: {
    clicked: []
  }
}, function () {
  function _class6(meta) {
    var _this10 = this;

    _classCallCheck(this, _class6);

    QmlWeb.callSuper(this, meta);
    //keep reference of rendered item
    this.items = {};

    this.renderCell = function (object) {
      var value = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : "";
      var node = arguments[2];
      var options = arguments[3];

      _this10.$removeChildren(object["storekey"]);
      _this10.items[object["storekey"]] = _this10.$initialComponent(object);
      node.appendChild(_this10.items[object["storekey"]].dom);
    };
  }

  _createClass(_class6, [{
    key: "$onRemoveRow",
    value: function $onRemoveRow(row) {
      var index = row.id.split('-')[2];
      this.$removeChildren(index);
    }
  }, {
    key: "$initialComponent",
    value: function $initialComponent(object) {
      var QMLOperationState = QmlWeb.QMLOperationState;
      var createProperty = QmlWeb.createProperty;
      var newItem = this.content.$createObject();

      // To properly import JavaScript in the context of a component
      this.content.finalizeImports();

      if (typeof newItem.$properties.modelData === "undefined") {
        createProperty("variant", newItem, "modelData");
      }

      newItem.$properties.modelData.set(object, QmlWeb.QMLProperty.ReasonInit, newItem, null);

      if (QmlWeb.engine.operationState !== QMLOperationState.Init && QmlWeb.engine.operationState !== QMLOperationState.Idle) {
        this.$callOnCompleted(newItem);
      }

      if (QmlWeb.engine.operationState !== QMLOperationState.Init) {
        QmlWeb.engine.$initializePropertyBindings();
      }

      return newItem;
    }
  }, {
    key: "$removeChildren",
    value: function $removeChildren(index) {
      var item = this.items[index];
      if (item) {
        item.$delete();
        this.$removeChildProperties(item);
        delete this.items[index];
      }
    }
  }, {
    key: "$removeChildProperties",
    value: function $removeChildProperties(child) {
      var signals = QmlWeb.engine.completedSignals;
      signals.splice(signals.indexOf(child.Component.completed), 1);
      for (var i = 0; i < child.children.length; i++) {
        this.$removeChildProperties(child.children[i]);
      }
    }
  }, {
    key: "$callOnCompleted",
    value: function $callOnCompleted(child) {
      child.Component.completed();
      var QMLBaseObject = QmlWeb.getConstructor("QtQml", "2.0", "QtObject");
      for (var i = 0; i < child.$tidyupList.length; i++) {
        if (child.$tidyupList[i] instanceof QMLBaseObject) {
          this.$callOnCompleted(child.$tidyupList[i]);
        }
      }
    }
  }]);

  return _class6;
}());

QmlWeb.registerQmlType({
  module: "DGrid",
  name: "DEditorColumn",
  versions: /.*/,
  baseClass: "DGrid.DColumn", // no UI
  properties: {
    editor: { type: "string", initialValue: "text" },
    editOn: { type: "string", initialValue: "click" }
  },
  signals: {}
}, function () {
  function _class7(meta) {
    _classCallCheck(this, _class7);

    QmlWeb.callSuper(this, meta);
  }

  return _class7;
}());

require(["dojo/_base/declare", "dgrid/Grid", "dgrid/OnDemandGrid", "dgrid/Selection", "dgrid/extensions/ColumnResizer", "dgrid/Keyboard", "dgrid/extensions/ColumnHider", "dojo/aspect", "dojo/dom-class", "dojo/dom-construct", "dojo/dom-style", "dgrid/Editor", "dstore/Memory", "dgrid/extensions/CompoundColumns"], function (declare, dgrid, OnDemandGrid, Selection, ColumnResizer, Keyboard, ColumnHider, aspect, domClass, domConstruct, domStyle, Editor, Memory, CompoundColumns) {

  QmlWeb.registerQmlType({
    module: "DGrid",
    name: "DGrid",
    versions: /.*/,
    baseClass: "Semantic.Html.Dom",
    properties: {
      width: "int",
      height: "int",
      columns: "list",
      enabled: { type: "bool", initialValue: true },
      model: { type: "var", initialValue: [] },
      selectedRow: { type: "var", initialValue: {} },
      showHeader: { type: "bool", initialValue: true }
    },
    signals: {
      selected: [{ type: "var", name: "event" }, { type: "var", name: "data" }], // dgrid event
      deselected: [{ type: "var", name: "event" }], // dgrid deselect event
      entered: [],
      selectedCell: [{ type: "var", name: "cell" }] }
  }, function () {
    function _class8(meta) {
      _classCallCheck(this, _class8);

      QmlWeb.callSuper(this, meta);
      this.Component.completed.connect(this, this.Component$onCompleted);
      this.modelChanged.connect(this, this.$onModelChanged);
      this.widthChanged.connect(this, this.$onWidthChanged);
      this.heightChanged.connect(this, this.$onHeightChanged);
      this.dojoUtil = {};
      this.dojoUtil.domClass = domClass;
      this.dojoUtil.domConstruct = domConstruct;
      this.dojoUtil.domStyle = domStyle;
      this.baseClass = "";
    }

    _createClass(_class8, [{
      key: "$onModelChanged",
      value: function $onModelChanged(newModel, oldModel, propName) {
        if (oldModel.toString() && oldModel.fetched) {
          oldModel.fetched.disconnect(this, this.$onModelFetched);
        }
        if (this.model.fetched) {
          this.model.fetched.connect(this, this.$onModelFetched);
          isModelChange = true;
        }
        if (this.widget) {
          this.widget.refresh();
          this.setStore();
          // this.widget.renderArray(this.model);
          this.selectedRow = {};
        }
      }
    }, {
      key: "$onModelFetched",
      value: function $onModelFetched() {
        this.widget.set("collection", this.model.currentStore);
        if (isModelChange) {
          // this.widget.refresh();
          isModelChange = false;
        }
        this.widget.resize();
      }
    }, {
      key: "$onHeightChanged",
      value: function $onHeightChanged() {
        this.dom.style.height = this.height + "px";
      }
    }, {
      key: "$onWidthChanged",
      value: function $onWidthChanged() {
        this.dom.style.width = this.width + "px";
      }
    }, {
      key: "Component$onCompleted",
      value: function Component$onCompleted() {
        var _this11 = this;

        // DGrid is a special case, we need all children to complete parsing first
        //  so all definition of columns are ready for us to render grid
        var columns = this.columns;
        var grid_setting = [OnDemandGrid, Selection, ColumnResizer, Keyboard, ColumnHider, Editor];
        var grid_columns = this.columns;

        // CompoundColumn checking, add into grid setting and clean grid columns
        if (this.isCompoundColumn(columns)) {
          grid_setting.push(CompoundColumns);
          grid_columns = this.makeColumn(this.columns);
        }
        var CustomGrid = declare(grid_setting, {
          removeRow: function removeRow(rowElement, preserveDom) {
            this.inherited(arguments);
            columns.forEach(function (column) {
              if (column.$onRemoveRow) {
                column.$onRemoveRow(rowElement);
              }
            });
          }
        });

        this.widget = new CustomGrid({
          columns: grid_columns,
          selectionMode: "single",
          cellNavigation: true,
          adjustLastColumn: false,
          keepScrollPosition: true,
          noColumnHider: false,
          showHeader: this.showHeader,
          loadingMessage: 'LOADING . . .',
          noDataMessage: 'ไม่มีข้อมูล',
          minRowsPerPage: 40
        }, this.dom);

        // need to call startup
        // incase grid is in Accordion or Tab
        this.widget.startup();

        this.selectedRow = {};
        this.widget.on('dgrid-select', function (event) {
          //Event Ref: https://github.com/SitePen/dgrid/blob/master/doc/components/mixins/Selection.md
          _this11.selectedRow = _this11.getFirstRowData(event);
          _this11.selected(event, _this11.selectedRow);
        });

        this.widget.on('dgrid-deselect', function (event) {
          return _this11.deselected(event, _this11.getFirstRowData(event));
        });
        this.widget.on('.dgrid-row:dblclick', function () {
          return _this11.entered();
        });
        this.widget.on('keypress', function () {
          if (event.keyCode === Qt.Key_Enter) {
            _this11.entered();
          }
        });
        this.widget.on('.dgrid-content .dgrid-cell:click', function (evt) {
          _this11.selectedCell(_this11.widget.cell(evt));
        });

        aspect.after(this.widget, "renderRow", function (row, args) {
          if (_this11.renderRow) {
            return _this11.renderRow(row, args, _this11.dojoUtil);
          }
          return row;
        });

        this.setStore();
        document.body.addEventListener("resizeDgrid", function (evt) {
          // evt.detail.dom: for dom detail;
          //check if evet.detail.dom is a parent or ancestor of this.dom

          //For Accordion, Modal, Tab
          var isParent = evt.detail.dom.contains(_this11.dom);
          isParent && _this11.widget.resize();
        });
      }
    }, {
      key: "isCompoundColumn",
      value: function isCompoundColumn(columns) {
        var _iteratorNormalCompletion = true;
        var _didIteratorError = false;
        var _iteratorError = undefined;

        try {
          for (var _iterator = columns[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
            column = _step.value;

            if (column.$class == "DCompoundColumn") {
              return true;
            }
          }
        } catch (err) {
          _didIteratorError = true;
          _iteratorError = err;
        } finally {
          try {
            if (!_iteratorNormalCompletion && _iterator.return) {
              _iterator.return();
            }
          } finally {
            if (_didIteratorError) {
              throw _iteratorError;
            }
          }
        }

        return false;
      }
    }, {
      key: "makeColumn",
      value: function makeColumn(columns) {
        var result = [];
        var _iteratorNormalCompletion2 = true;
        var _didIteratorError2 = false;
        var _iteratorError2 = undefined;

        try {
          for (var _iterator2 = columns[Symbol.iterator](), _step2; !(_iteratorNormalCompletion2 = (_step2 = _iterator2.next()).done); _iteratorNormalCompletion2 = true) {
            column = _step2.value;

            if (column.$class == "DCompoundColumn") {
              result.push({
                label: column.label,
                children: this.makeColumn(column.children)
              });
            } else {
              result.push({
                field: column.field,
                label: column.label,
                width: column.width,
                editor: column.editor,
                editOn: column.editOn,
                renderCell: column.renderCell,
                renderRow: column.renderRow
              });
            }
          }
        } catch (err) {
          _didIteratorError2 = true;
          _iteratorError2 = err;
        } finally {
          try {
            if (!_iteratorNormalCompletion2 && _iterator2.return) {
              _iterator2.return();
            }
          } finally {
            if (_didIteratorError2) {
              throw _iteratorError2;
            }
          }
        }

        return result;
      }
    }, {
      key: "setStore",
      value: function setStore() {
        if (_typeof(this.model.store) === "object") {
          if (!this.model.target) return;
          this.widget.set("collection", this.model.store);
          this.widget.resize();
          return;
        }
        this.model.forEach(function (item, index) {
          item.storekey = index;
        });

        var store = new Memory({
          data: {
            items: this.model,
            identifier: 'storekey'
          }
        });
        this.widget.set("collection", store);
        this.widget.refresh();
        this.widget.resize();
      }
    }, {
      key: "getFirstRowData",
      value: function getFirstRowData(event) {
        if (event.rows.length > 0) return event.rows[0].data;
        return {};
      }
    }, {
      key: "deselectCurrentRow",
      value: function deselectCurrentRow() {
        var current_row = -1;
        for (var row in this.widget.selection) {
          current_row = parseInt(row);
        }
        this.widget.deselect(current_row);
        this.selectedRow = {};
      }
    }, {
      key: "down",
      value: function down() {
        var current_row = -1;
        for (var row in this.widget.selection) {
          current_row = parseInt(row);
        }
        this.widget.deselect(current_row);
        if (this.widget._total == current_row + 1) {
          current_row -= 1;
        }
        this.widget.select(current_row + 1);
        cur_row = this.widget.row(current_row + 1);

        if (cur_row.element) cur_row.element.scrollIntoViewIfNeeded();
      }
    }, {
      key: "up",
      value: function up() {
        var current_row = 1;
        for (var row in this.widget.selection) {
          current_row = parseInt(row);
        }
        this.widget.deselect(current_row);
        if (current_row == 0) {
          current_row = 1;
        }
        this.widget.select(current_row - 1);
        cur_row = this.widget.row(current_row - 1);

        if (cur_row.element) cur_row.element.scrollIntoViewIfNeeded();
      }
    }, {
      key: "selectRow",
      value: function selectRow(row) {
        this.widget.select(row);
      }
    }, {
      key: "resize",
      value: function resize() {
        this.widget.resize();
      }
    }]);

    return _class8;
  }());
});
require(["dojo/_base/declare", "dstore/Rest", "dstore/Trackable", "dstore/SimpleQuery"], function (declare, Rest, SimpleQuery, Trackable) {
  var TrackableRest = declare([Rest, SimpleQuery, Trackable], {
    _getTarget: function _getTarget(id) {
      // normalize URL for resource, e.g., /apis/REG/patient/1/ (always have the trailing slash)
      var target = this.target;
      if (target.slice(-1) == '/') {
        return target + id + '/';
      } else {
        return target + '/' + id + '/';
      }
    }
  });
  QmlWeb.registerQmlType({
    module: "DGrid",
    name: "RestStore",
    versions: /.*/,
    baseClass: "QtQml.QtObject", // no UI
    properties: {
      //id need to be null, unless CompoundColumns bug
      id: { type: "string", initialValue: null },
      target: "string",
      rangeStartParam: { type: "string", initialValue: "offset" },
      rangeCountParam: { type: "string", initialValue: "limit" },
      sortParam: { type: "string", initialValue: "sort" }
    },
    signals: {
      fetched: []
    }
  }, function () {
    function _class9(meta) {
      _classCallCheck(this, _class9);

      QmlWeb.callSuper(this, meta);
      this.Component.completed.connect(this, this.Component$onCompleted);
      this.rangeStartParamChanged.connect(this, this.$onRangeStartParamChanged);
      this.rangeCountParamChanged.connect(this, this.$onRangeCountParamChanged);
      this.targetChanged.connect(this, this.$onTargetChanged);
      this.store = new TrackableRest({
        target: this.target,
        rangeStartParam: this.rangeStartParam,
        rangeCountParam: this.rangeCountParam,
        sortParam: this.sortParam,
        headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
      });
      this.currentStore = this.store;
    }

    _createClass(_class9, [{
      key: "filter",
      value: function filter(query) {
        // query Example 
        // query = {
        // 	name1 : value1,
        // 	name2 : value2,
        // }
        this.currentStore = this.store.filter(query);
        this.fetched();
      }
    }, {
      key: "Component$onCompleted",
      value: function Component$onCompleted() {}
    }, {
      key: "$onRangeStartParamChanged",
      value: function $onRangeStartParamChanged() {
        this.store.rangeStartParam = this.rangeStartParam;
        this.currentStore = this.store;
      }
    }, {
      key: "$onRangeCountParamChanged",
      value: function $onRangeCountParamChanged() {
        this.store.rangeCountParam = this.rangeCountParam;
        this.currentStore = this.store;
      }
    }, {
      key: "$onTargetChanged",
      value: function $onTargetChanged() {
        this.store.target = this.target;
        this.currentStore.target = this.target;
        this.fetched();
      }
    }, {
      key: "addRow",
      value: function addRow(object) {
        this.store.add(object);
      }
    }, {
      key: "editRow",
      value: function editRow(object) {
        if (object.id === undefined) {
          throw new Error("object must contains 'id' to edit row");
          return;
        }
        this.store.put(object);
      }
    }, {
      key: "removeRow",
      value: function removeRow(id) {
        this.store.remove(id);
      }
    }, {
      key: "getCookie",
      value: function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
          var cookies = document.cookie.split(';');
          for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == name + '=') {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
            }
          }
        }
        return cookieValue;
      }
    }]);

    return _class9;
  }());
});

require(["dojo/_base/declare", 'dgrid/OnDemandGrid', "dgrid/Selection", "dgrid/extensions/ColumnResizer", "dgrid/Keyboard", "dgrid/extensions/ColumnHider", "dojo/aspect", "dojo/dom-class", "dojo/dom-construct", "dojo/dom-style", 'dgrid/Editor', 'dstore/Memory', 'dstore/Trackable', 'dstore/Tree', 'dgrid/Tree'], function (declare, OnDemandGrid, Selection, ColumnResizer, Keyboard, ColumnHider, aspect, domClass, domConstruct, domStyle, Editor, Memory, Trackable, TreeStoreMixin, Tree) {

  QmlWeb.registerQmlType({
    module: "DGrid",
    name: "Tree",
    versions: /.*/,
    baseClass: "Semantic.Html.Dom",
    properties: {
      width: "int",
      height: "int",
      columns: "list",
      enabled: { type: "bool", initialValue: true },
      model: { type: "var", initialValue: [] },
      selectedRow: { type: "var", initialValue: {} },
      expand: "bool"
    },
    signals: {
      selected: [{ type: "var", name: "event" }, { type: "var", name: "data" }], // dgrid event
      deselected: [{ type: "var", name: "event" }], // dgrid deselect event
      entered: []
    }
  }, function () {
    function _class10(meta) {
      _classCallCheck(this, _class10);

      QmlWeb.callSuper(this, meta);
      this.Component.completed.connect(this, this.Component$onCompleted);
      this.modelChanged.connect(this, this.$onModelChanged);
      this.widthChanged.connect(this, this.$onWidthChanged);
      this.heightChanged.connect(this, this.$onHeightChanged);
    }

    _createClass(_class10, [{
      key: "Component$onCompleted",
      value: function Component$onCompleted() {
        var _this12 = this;

        // DGrid is a special case, we need all children to complete parsing first
        //  so all definition of columns are ready for us to render grid
        var columns = this.columns;
        var CustomGrid = declare([OnDemandGrid, Keyboard, Selection, Tree], {
          removeRow: function removeRow(rowElement, preserveDom) {
            this.inherited(arguments);
            columns.forEach(function (column) {
              if (column.$onRemoveRow) {
                column.$onRemoveRow(rowElement);
              }
            });
          }
        });
        var tree = this;
        this.columns[0].renderExpando = true;
        this.widget = new CustomGrid({
          columns: this.columns,
          selectionMode: "single",
          cellNavigation: true,
          adjustLastColumn: false,
          keepScrollPosition: true,
          noColumnHider: false,
          showHeader: true,
          loadingMessage: 'LOADING . . .',
          noDataMessage: 'ไม่มีข้อมูล',
          shouldExpand: function shouldExpand(object) {
            return tree.expand !== undefined ? tree.expand : true;
          }
        }, this.dom);
        this.widget.startup();

        this.selectedRow = {};
        this.widget.on('dgrid-select', function (event) {
          //Event Ref: https://github.com/SitePen/dgrid/blob/master/doc/components/mixins/Selection.md
          _this12.selectedRow = _this12.getFirstRowData(event);
          _this12.selected(event, _this12.selectedRow);
        });

        aspect.after(this.widget, "renderRow", function (row, args) {
          if (_this12.renderRow) {
            return _this12.renderRow(row, args, _this12.dojoUtil);
          }
          return row;
        });

        this.setStore();
      }
    }, {
      key: "$onHeightChanged",
      value: function $onHeightChanged() {
        this.dom.style.height = this.height + "px";
      }
    }, {
      key: "$onWidthChanged",
      value: function $onWidthChanged() {
        this.dom.style.width = this.width + "px";
      }
    }, {
      key: "$onModelChanged",
      value: function $onModelChanged() {
        if (this.widget) {
          this.widget.refresh();
          this.setStore();
          // this.widget.renderArray(this.model);
          this.selectedRow = {};
        }
      }
    }, {
      key: "getFirstRowData",
      value: function getFirstRowData(event) {
        if (event.rows.length > 0) return event.rows[0].data;
        return {};
      }
    }, {
      key: "setStore",
      value: function setStore() {
        this.model.forEach(function (items, index) {
          items.id = index;
          if ('children' in items && _typeof(items.children) === "object") {
            items.hasChildren = true;
            items.children.forEach(function (child, i) {
              child.id = index + '_' + i;
            });
          }
        });

        var store = new (declare([Memory, Trackable, TreeStoreMixin]))({
          data: this.model,
          getChildren: function getChildren(parent) {
            return new Memory({
              data: parent.children
            });
          },
          mayHaveChildren: function mayHaveChildren(object) {
            return 'hasChildren' in object ? object.hasChildren : false;
          }
        });
        this.widget.set("collection", store);
        this.widget.refresh();
        this.widget.resize();
      }
    }]);

    return _class10;
  }());
});
QmlWeb.registerQmlType({
  module: "QmlWeb.Dom",
  name: "DomElement",
  versions: /.*/,
  baseClass: "QtQuick.Item",
  properties: {
    tagName: { type: "string", initialValue: "div" }
  }
}, function () {
  function _class11(meta) {
    _classCallCheck(this, _class11);

    QmlWeb.callSuper(this, meta);

    var tagName = meta.object.tagName || "div";
    this.dom = document.createElement(tagName);

    // TODO: support properties, styles, perhaps changing the tagName
  }

  return _class11;
}());

require(['dstore/Memory', 'dstore/RequestMemory', "dstore/Cache", 'dstore/Request'], function (Memory, RequestMemory, Cache, Request) {

  QmlWeb.registerQmlType({
    module: "QmlWeb",
    name: "RequestMemory",
    versions: /.*/,
    baseClass: "QtQml.QtObject",
    properties: {
      url: "string"
    },
    signals: {
      fetched: []
    }
  }, function () {
    function _class12(meta) {
      _classCallCheck(this, _class12);

      QmlWeb.callSuper(this, meta);
      this.Component.completed.connect(this, this.Component$onCompleted);
    }

    _createClass(_class12, [{
      key: "Component$onCompleted",
      value: function Component$onCompleted() {
        this.fetch();
      }
    }, {
      key: "getItem",
      value: function getItem(value) {
        var data = [];
        this.store.get(value).then(function (object) {
          data.push(object);
        });
        return data;
      }
    }, {
      key: "getItems",
      value: function getItems() {
        var data = [];
        this.store.forEach(function (object) {
          data.push(object);
        });
        return data;
      }

      // use this method to set a queryset for filter()

    }, {
      key: "getFilter",
      value: function getFilter() {
        // Operator

        // eq: Property values must equal the filter value argument.
        // ne: Property values must not equal the filter value argument.
        // lt: Property values must be less than the filter value argument.
        // lte: Property values must be less than or equal to the filter value argument.
        // gt: Property values must be greater than the filter value argument.
        // gte: Property values must be greater than or equal to the filter value argument.
        // in: An array should be passed in as the second argument, and property values must be equal to one of the values in the array.
        // match: Property values must match the provided regular expression.
        // contains: Filters for objects where the specified property's value is an array and the array contains any value that equals the provided value or satisfies the provided expression.

        // and: This takes two arguments that are other filter objects, that both must be true.
        // or: This takes two arguments that are other filter objects, where one of the two must be true.

        // more at https://github.com/SitePen/dstore/blob/master/docs/Collection.md

        return this.store.Filter();
      }
    }, {
      key: "filter",
      value: function filter(queryset) {
        var data = [];
        this.store.filter(queryset).forEach(function (object) {
          data.push(object);
        });
        return data;
      }
    }, {
      key: "fetch",
      value: function fetch() {
        var _this13 = this;

        if (this.url == "") {
          console.error("Request Memory : fetch error URL is not defined");
          return;
        }

        this.store = new RequestMemory({
          target: this.url
        });

        this.store.fetchRequest.response.then(function () {
          _this13.getItems();
          _this13.fetched();
        });
      }
    }]);

    return _class12;
  }());
});

/***
 * Original code come from QmlWeb.RestModel
 * 
 * We should improve various aspect of this Component to
 *     best match DjangoRestFramework Convention
 * 
 * 1. HTTP POST = Create new object            /patient/
 * 2. HTTP PUT  = Update existing object       /patient/ID/
 * 3. HTTP GET  = List all patients            /patient/
 *    HTTP GET  = List all patients matching criteria   /patient/?firstname=XXXX
 * 4. HTTP DELETE = Delete object              /patient/ID/
 */
QmlWeb.registerQmlType({
  module: "QmlWeb",
  name: "RestModel",
  versions: /.*/,
  baseClass: "QtQml.QtObject", // no UI
  properties: {
    url: "string",
    isLoading: "bool",
    mimeType: { type: "string", initialValue: "application/json" }, // receiving data from server
    queryMimeType: { // sending data to server
      type: "string",
      initialValue: "application/json"
    },
    query: "var",
    merge: "var",
    hierarchy: "var",
    //ignore property when generate body for post query
    ignore: { type: "var", initialValue: [] }
  },
  signals: {
    fetched: [],
    saved: [],
    failed: [{ name: "error", type: "var" }, { name: "xhr", type: "var" }] }
}, function () {
  function _class13(meta) {
    _classCallCheck(this, _class13);

    QmlWeb.callSuper(this, meta);
    this.attributes = this.getAttributes();
    this.runningRequests = 0;
  }

  _createClass(_class13, [{
    key: "fetch",
    value: function fetch() {
      var _this14 = this;

      this.$ajax({
        method: "GET",
        mimeType: this.mimetype,
        query: this.query,
        success: function success(xhr) {
          _this14.$xhrReadResponse(xhr);
          _this14.fetched();
        },
        failure: function failure(xhr) {
          _this14.$propagateFailSignal(xhr);
        }
      });
    }
  }, {
    key: "remove",
    value: function remove() {
      var _this15 = this;

      this.$ajax({
        method: "DELETE",
        success: function success() {
          _this15.destroy();
        },
        failure: function failure(xhr) {
          _this15.$propagateFailSignal(xhr);
        }
      });
    }
  }, {
    key: "create",
    value: function create() {
      this.$sendToServer("POST");
    }
  }, {
    key: "save",
    value: function save() {
      this.$sendToServer("PUT");
    }
  }, {
    key: "$sendToServer",
    value: function $sendToServer(method) {
      var _this16 = this;

      this.$ajax({
        method: method,
        mimeType: this.queryMimeType,
        body: this.$generateBodyForPostQuery(),
        success: function success(xhr) {
          _this16.$xhrReadResponse(xhr);
          _this16.saved();
        },
        failure: function failure(xhr) {
          console.log("FAILED: xhr status code = " + xhr.status);
          _this16.$propagateFailSignal(xhr);
        }
      });
    }
  }, {
    key: "$propagateFailSignal",
    value: function $propagateFailSignal(xhr) {
      /**
      When XHR failed, propagate failed to all nested RestModel (in merge, and hierarchy)
      All RestModel's onFailed will be fired
      **/
      var error = JSON.parse(xhr.response);
      if (this.merge) {
        this.failed;
        var _iteratorNormalCompletion3 = true;
        var _didIteratorError3 = false;
        var _iteratorError3 = undefined;

        try {
          for (var _iterator3 = this.merge[Symbol.iterator](), _step3; !(_iteratorNormalCompletion3 = (_step3 = _iterator3.next()).done); _iteratorNormalCompletion3 = true) {
            var child = _step3.value;

            child.$propagateFailSignal(xhr);
          }
        } catch (err) {
          _didIteratorError3 = true;
          _iteratorError3 = err;
        } finally {
          try {
            if (!_iteratorNormalCompletion3 && _iterator3.return) {
              _iterator3.return();
            }
          } finally {
            if (_didIteratorError3) {
              throw _iteratorError3;
            }
          }
        }
      }
      if (this.hierarchy) {
        for (var key in this.hierarchy) {
          this.hierarchy[key].$propagateFailSignal(xhr);
        }
      }
      this.failed(error, xhr);
    }
  }, {
    key: "$generateBodyForPostQuery",
    value: function $generateBodyForPostQuery() {
      var object = {};
      var Repeater = QmlWeb.getConstructor("Semantic.Html", "1.0", "Repeater");
      for (var i = 0; i < this.attributes.length; i++) {
        if (this.ignore.includes(this.attributes[i])) continue;

        object[this.attributes[i]] = this.$properties[this.attributes[i]].get();
        var prop = this.$properties[this.attributes[i]];
        if (prop.val && prop.val.objectName) {
          var target_object = this.$context[prop.val.objectName];
          if (target_object instanceof Repeater && target_object.model instanceof QmlWeb.ItemModel) {
            var array = [];
            for (var j = 0; j < target_object.$items.length; j++) {
              var restObject = {};
              restObject = this.convertRestModelToObject(target_object.$items[j].model);
              array.push(restObject);
            }
            object[this.attributes[i]] = array;
          }
        }
      }
      if (this.merge) {
        this.mergeData(object, this.merge);
      }
      if (this.hierarchy) {
        this.hierarchyData(object, this.hierarchy);
      }
      switch (this.queryMimeType) {
        case "application/json":
        case "text/json":
          return JSON.stringify(object);
        case "application/x-www-urlencoded":
          return this.$objectToUrlEncoded(object);
      }
      return undefined;
    }
  }, {
    key: "convertRestModelToObject",
    value: function convertRestModelToObject(restModel) {
      var object = {};
      for (var i = 0; i < restModel.attributes.length; i++) {
        object[restModel.attributes[i]] = restModel.$properties[restModel.attributes[i]].get();
      }
      return object;
    }
  }, {
    key: "mergeData",
    value: function mergeData(object, data) {
      for (var j = 0; j < data.length; j++) {
        for (var i = 0; i < data[j].$attributes.length; i++) {
          if (object.hasOwnProperty(data[j].$attributes[i])) {
            var error = "Property of RestModel has duplicate name = '" + data[j].$attributes[i] + "'";
            throw new Error(error);
          }
          object[data[j].$attributes[i]] = data[j].$properties[data[j].$attributes[i]].get();
        }
        if (data[j].merge) {
          this.mergeData(object, data[j].merge);
        }
        if (data[j].hierarchy) {
          this.hierarchyData(object, data[j].hierarchy);
        }
      }
    }
  }, {
    key: "hierarchyData",
    value: function hierarchyData(object, data) {
      for (var index in data) {
        var newObject = {};
        for (var i = 0; i < data[index].attributes.length; i++) {
          newObject[data[index].attributes[i]] = data[index].$properties[data[index].attributes[i]].get();
        }
        object[index] = newObject;
        if (data[index].merge) {
          this.mergeData(newObject, data[index].merge);
        }
        if (data[index].hierarchy) {
          this.hierarchyData(newObject, data[index].hierarchy);
        }
      }
    }
  }, {
    key: "$objectToUrlEncoded",
    value: function $objectToUrlEncoded(object, prefix) {
      var parts = [];
      for (var key in object) {
        if (object.hasOwnProperty(key) && object[key] !== undefined) {
          var value = object[key];
          if (typeof prefix !== "undefined") {
            key = prefix + "[" + key + "]";
          }
          if ((typeof value === "undefined" ? "undefined" : _typeof(value)) === "object") {
            parts.push(this.$objectToUrlEncoded(value, key));
          } else {
            var ekey = this.$myEncodeURIComponent(key);
            var evalue = this.$myEncodeURIComponent(value);
            parts.push(ekey + "=" + evalue);
          }
        }
      }
      return parts.join("&");
    }
  }, {
    key: "$myEncodeURIComponent",
    value: function $myEncodeURIComponent(str) {
      return encodeURIComponent(str).replace(/[!'()*]/g, function (c) {
        return "%" + c.charCodeAt(0).toString(16);
      });
    }
  }, {
    key: "$ajax",
    value: function $ajax(options) {
      var _this17 = this;

      var csrftoken = this.getCookie('csrftoken');
      var queryString = "";
      if (options.query) {
        queryString = '?' + this.$objectToUrlEncoded(options.query);
        console.log('query string is ' + queryString);
      }
      var xhr = new XMLHttpRequest();
      xhr.overrideMimeType(this.mimeType);
      xhr.onreadystatechange = function () {
        if (xhr.readyState === XMLHttpRequest.DONE) {
          if (xhr.status === 200 || xhr.status === 201) {
            options.success(xhr);
          } else {
            options.failure(xhr);
          }
          _this17.runningRequests -= 1;
          if (_this17.runningRequests <= 0) {
            _this17.isLoading = false;
          }
        }
      };
      xhr.open(options.method, this.url + queryString, true);
      // send CSRF token by headers
      xhr.setRequestHeader('X-CSRFToken', csrftoken);

      if (typeof options.body !== "undefined") {
        xhr.setRequestHeader("Content-Type", this.queryMimeType);
        xhr.send(options.body);
      } else {
        xhr.send(null);
      }
      this.runningRequests += 1;
      this.isLoading = true;
    }
  }, {
    key: "$xhrReadResponse",
    value: function $xhrReadResponse(xhr) {
      var responseObject = void 0;
      if (this.mimeType === "application/json" || this.mimeType === "text/json") {
        responseObject = JSON.parse(xhr.responseText);
      }
      this.$updatePropertiesFromResponseObject(responseObject);
    }
  }, {
    key: "$updatePropertiesFromResponseObject",
    value: function $updatePropertiesFromResponseObject(responseObject) {
      var QMLProperty = QmlWeb.QMLProperty;
      var Repeater = QmlWeb.getConstructor("Semantic.Html", "1.0", "Repeater");
      for (var key in responseObject) {
        // for Repeater
        var prop = this.$properties[key];
        if (prop && prop.type == "alias") {
          var target_object = this.$context[prop.val.objectName];
          if (target_object instanceof Repeater) {
            var newMod = new QmlWeb.ItemModel(responseObject[key]);
            var roleNames = [];
            for (var i in responseObject[key][0]) {
              if (i !== "index") {
                roleNames.push(i);
              }
            }
            newMod.setRoleNames(roleNames);
            this.$properties[key].set(newMod, QMLProperty.ReasonUser);
            continue;
          }
        }
        if (responseObject.hasOwnProperty(key) && this.$hasProperty(key)) {
          this.$properties[key].set(responseObject[key], QMLProperty.ReasonUser);
        }
      }
      if (this.merge) {
        this.updateMergeData(responseObject, this.merge);
      }
      if (this.hierarchy) {
        this.updateHierarchyData(responseObject, this.hierarchy);
      }
    }
  }, {
    key: "updateMergeData",
    value: function updateMergeData(responseObject, data) {
      var QMLProperty = QmlWeb.QMLProperty;
      for (var i = 0; i < data.length; i++) {
        for (var key in responseObject) {
          if (responseObject.hasOwnProperty(key) && typeof data[i].$properties[key] !== "undefined") {
            data[i].$properties[key].set(responseObject[key], QMLProperty.ReasonUser);
          }
        }
        if (data[i].merge) {
          this.updateMergeData(responseObject, data[i].merge);
        }
        if (data[i].hierarchy) {
          this.updateHierarchyData(responseObject, data[i].hierarchy);
        }
      }
    }
  }, {
    key: "updateHierarchyData",
    value: function updateHierarchyData(responseObject, data) {
      var QMLProperty = QmlWeb.QMLProperty;
      for (var index in data) {
        for (var key in responseObject) {
          if (index == key && _typeof(responseObject[key]) === "object") {
            for (var keyData in responseObject[key]) {
              if (responseObject[key].hasOwnProperty(keyData) && typeof data[index].$properties[keyData] !== "undefined") {
                data[index].$properties[keyData].set(responseObject[key][keyData], QMLProperty.ReasonUser);
              }
            }

            if (data[index].merge) {
              this.updateMergeData(responseObject[key], data[index].merge);
            }
            if (data[index].hierarchy) {
              this.updateHierarchyData(responseObject[key], data[index].hierarchy);
            }
          }
        }
      }
    }
  }, {
    key: "$hasProperty",
    value: function $hasProperty(name) {
      return typeof this.$properties[name] !== "undefined";
    }
  }, {
    key: "getCookie",
    value: function getCookie(name) {
      var cookieValue = null;
      if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
          var cookie = cookies[i].trim();
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) == name + '=') {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  }]);

  return _class13;
}());
QmlWeb.registerQmlType({
  module: "QmlWeb",
  name: "Utility",
  versions: /.*/,
  baseClass: "QtQml.QtObject", // no UI
  properties: {}
}, function () {
  function _class14(meta) {
    _classCallCheck(this, _class14);

    QmlWeb.callSuper(this, meta);
  }

  _createClass(_class14, [{
    key: "setCookie",
    value: function setCookie(cname, cvalue, exdays) {
      var d = new Date();
      d.setTime(d.getTime() + exdays * 24 * 60 * 60 * 1000);
      var expires = "expires=" + d.toUTCString();
      document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
    }
  }, {
    key: "getCookie",
    value: function getCookie(cname) {
      var name = cname + "=";
      var decodedCookie = decodeURIComponent(document.cookie);
      var ca = decodedCookie.split(';');
      for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
          c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
          return c.substring(name.length, c.length);
        }
      }
      return "";
    }
  }]);

  return _class14;
}());

QmlWeb.registerQmlType({
  module: "Qt.labs.settings",
  name: "Settings",
  versions: /.*/,
  baseClass: "QtQuick.Item",
  properties: {
    category: "string"
  }
}, function () {
  function _class15(meta) {
    _classCallCheck(this, _class15);

    QmlWeb.callSuper(this, meta);

    if (typeof window.localStorage === "undefined") {
      return;
    }

    this.Component.completed.connect(this, this.Component$onCompleted);
  }

  _createClass(_class15, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.$loadProperties();
      this.$initializeProperties();
    }
  }, {
    key: "$getKey",
    value: function $getKey(attrName) {
      return this.category + "/" + attrName;
    }
  }, {
    key: "$loadProperties",
    value: function $loadProperties() {
      var _this18 = this;

      this.$attributes.forEach(function (attrName) {
        if (!_this18.$properties[attrName]) return;

        var key = _this18.$getKey(attrName);
        _this18[attrName] = localStorage.getItem(key);
      });
    }
  }, {
    key: "$initializeProperties",
    value: function $initializeProperties() {
      var _this19 = this;

      this.$attributes.forEach(function (attrName) {
        if (!_this19.$properties[attrName]) return;

        var emitter = _this19;
        var signalName = attrName + "Changed";

        if (_this19.$properties[attrName].type === "alias") {
          emitter = _this19.$context[_this19.$properties[attrName].val.objectName];
          signalName = _this19.$properties[attrName].val.propertyName + "Changed";
        }

        emitter[signalName].connect(_this19, function () {
          localStorage.setItem(_this19.$getKey(attrName), _this19[attrName]);
        });
      });
    }
  }]);

  return _class15;
}());

QmlWeb.registerQmlType({
  module: "QtGraphicalEffects",
  name: "FastBlur",
  versions: /.*/,
  baseClass: "QtQuick.Item",
  properties: {
    radius: "real",
    source: { type: "var", initialValue: null }
  }
}, function () {
  function _class16(meta) {
    _classCallCheck(this, _class16);

    QmlWeb.callSuper(this, meta);

    this.$previousSource = null;
    this.$filterObject = undefined;

    this.radiusChanged.connect(this, this.$onRadiusChanged);
    this.sourceChanged.connect(this, this.$onSourceChanged);
  }

  _createClass(_class16, [{
    key: "$onRadiusChanged",
    value: function $onRadiusChanged() {
      this.$updateEffect(this.source);
    }
  }, {
    key: "$onSourceChanged",
    value: function $onSourceChanged() {
      this.$updateEffect(this.source);
    }
  }, {
    key: "$updateFilterObject",
    value: function $updateFilterObject() {
      this.$filterObject = {
        transformType: "filter",
        operation: "blur",
        parameters: this.radius + "px"
      };
    }
  }, {
    key: "$updateEffect",
    value: function $updateEffect(source) {
      console.log("updating effect");
      if (this.$previousSource) {
        var index = this.$previousSource.transform.indexOf(this.$filterObject);
        this.$previousSource.transform.splice(index, 1);
        this.$previousSource.$updateTransform();
      }
      if (source && source.transform) {
        this.$updateFilterObject();
        console.log("updating effect:", this.$filterObject, source);
        source.transform.push(this.$filterObject);
        source.$updateTransform();
        this.$previousSource = source;
      } else {
        this.$previousSource = null;
      }
    }
  }]);

  return _class16;
}());

QmlWeb.registerQmlType({
  module: "QtMobility",
  name: "GeoLocation",
  versions: /.*/,
  baseClass: "QtQuick.Item",
  properties: {
    accuracy: "double",
    altitude: "double",
    altitudeAccuracy: "double",
    heading: "double",
    latitude: "double",
    longitude: "double",
    speed: "double",
    timestamp: "date",
    label: "string"
  }
}, function () {
  function _class17(meta) {
    var _this20 = this;

    _classCallCheck(this, _class17);

    QmlWeb.callSuper(this, meta);

    if (!navigator.geolocation) {
      return;
    }

    navigator.geolocation.getCurrentPosition(function (pos) {
      return _this20.$updatePosition(pos);
    });
    navigator.geolocation.watchPosition(function (pos) {
      return _this20.$updatePosition(pos);
    });
  }

  _createClass(_class17, [{
    key: "$updatePosition",
    value: function $updatePosition(position) {
      this.accuracy = position.coords.accuracy;
      this.altitude = position.coords.altitude;
      this.altitudeAccuracy = position.coords.altitudeAccuracy;
      this.heading = position.coords.heading;
      this.latitude = position.coords.latitude;
      this.longitude = position.coords.longitude;
      this.speed = position.coords.speed;
      this.timestamp = position.timestamp;
    }
  }]);

  return _class17;
}());

QmlWeb.registerQmlType({
  module: "QtMultimedia",
  name: "Video",
  versions: /^5\./,
  baseClass: "QtQuick.Item",
  enums: {
    MediaPlayer: {
      NoError: 0, ResourceError: 1, FormatError: 2, NetworkError: 4,
      AccessDenied: 8, ServiceMissing: 16,

      StoppedState: 0, PlayingState: 1, PausedState: 2,

      NoMedia: 0, Loading: 1, Loaded: 2, Buffering: 4, Stalled: 8,
      EndOfMedia: 16, InvalidMedia: 32, UnknownStatus: 64
    },
    VideoOutput: { PreserveAspectFit: 0, PreserveAspectCrop: 1, Stretch: 2 }
  },
  properties: {
    source: "string",
    duration: "int",
    position: "int",
    autoPlay: "bool",
    muted: "bool",
    volume: "real",
    playbackRate: "real",
    playbackState: "enum", // MediaPlayer.StoppedState
    fillMode: "enum", // VideoOutput.PreserveAspectFit
    status: "enum", // MediaPlayer.NoMedia
    error: "enum" // MediaPlayer.NoError
  },
  signals: {
    paused: [],
    playing: [],
    stopped: []
  }
}, function () {
  function _class18(meta) {
    var _this21 = this;

    _classCallCheck(this, _class18);

    QmlWeb.callSuper(this, meta);

    this.$runningEventListener = 0;

    this.impl = document.createElement("video");
    this.impl.style.width = this.impl.style.height = "100%";
    this.impl.style.margin = "0";
    this.dom.appendChild(this.impl);

    this.volume = this.impl.volume;
    this.duration = this.impl.duration;

    this.impl.addEventListener("play", function () {
      _this21.playing();
      _this21.playbackState = _this21.MediaPlayer.PlayingState;
    });

    this.impl.addEventListener("pause", function () {
      _this21.paused();
      _this21.playbackState = _this21.MediaPlayer.PausedState;
    });

    this.impl.addEventListener("timeupdate", function () {
      _this21.$runningEventListener++;
      _this21.position = _this21.impl.currentTime * 1000;
      _this21.$runningEventListener--;
    });

    this.impl.addEventListener("ended", function () {
      _this21.stopped();
      _this21.playbackState = _this21.MediaPlayer.StoppedState;
    });

    this.impl.addEventListener("progress", function () {
      if (_this21.impl.buffered.length > 0) {
        _this21.progress = _this21.impl.buffered.end(0) / _this21.impl.duration;
        _this21.status = _this21.progress < 1 ? _this21.MediaPlayer.Buffering : _this21.MediaPlayer.Buffered;
      }
    });

    this.impl.addEventListener("stalled", function () {
      _this21.status = _this21.MediaPlayer.Stalled;
    });

    this.impl.addEventListener("canplaythrough", function () {
      _this21.status = _this21.MediaPlayer.Buffered;
    });

    this.impl.addEventListener("loadstart", function () {
      _this21.status = _this21.MediaPlayer.Loading;
    });

    this.impl.addEventListener("durationchanged", function () {
      _this21.duration = _this21.impl.duration;
    });

    this.impl.addEventListener("volumechanged", function () {
      _this21.$runningEventListener++;
      _this21.volume = _this21.impl.volume;
      _this21.$runningEventListener--;
    });

    this.impl.addEventListener("suspend", function () {
      _this21.error |= _this21.MediaPlayer.NetworkError;
    });

    this.impl.addEventListener("error", function () {
      _this21.error |= _this21.MediaPlayer.ResourceError;
    });

    this.impl.addEventListener("ratechange", function () {
      _this21.$runningEventListener++;
      _this21.playbackRate = _this21.impl.playbackRate;
      _this21.$runningEventListener--;
    });

    this.autoPlayChanged.connect(this, this.$onAutoPlayChanged);
    this.sourceChanged.connect(this, this.$onSourceChanged);
    this.positionChanged.connect(this, this.$onPositionChanged);
    this.volumeChanged.connect(this, this.$onVolumeChanged);
    this.playbackRateChanged.connect(this, this.$onPlaybackRateChanged);
    this.mutedChanged.connect(this, this.$onMutedChanged);
    this.fillModeChanged.connect(this, this.$onFillModeChanged);
  }

  _createClass(_class18, [{
    key: "$onAutoPlayChanged",
    value: function $onAutoPlayChanged(newVal) {
      this.impl.autoplay = newVal;
    }
  }, {
    key: "$onSourceChanged",
    value: function $onSourceChanged(source) {
      var parts = source.split(".");
      var extension = parts[parts.length - 1].toLowerCase();
      var mime = this.mimetypeFromExtension(extension);
      this.impl.src = source;
      if (!this.impl.canPlayType(mime)) {
        this.error |= this.MediaPlayer.FormatError;
      }
    }
  }, {
    key: "$onPositionChanged",
    value: function $onPositionChanged(currentTime) {
      if (this.$runningEventListener > 0) return;
      this.impl.currentTime = currentTime / 1000;
    }
  }, {
    key: "$onVolumeChanged",
    value: function $onVolumeChanged(volume) {
      if (this.$runningEventListener > 0) return;
      this.impl.volume = volume;
    }
  }, {
    key: "$onPlaybackRateChanged",
    value: function $onPlaybackRateChanged(playbackRate) {
      if (this.$runningEventListener > 0) return;
      this.impl.playbackRate = playbackRate;
    }
  }, {
    key: "$onMutedChanged",
    value: function $onMutedChanged(newValue) {
      if (newValue) {
        this.$volulmeBackup = this.impl.volume;
        this.volume = 0;
      } else {
        this.volume = this.$volumeBackup;
      }
    }
  }, {
    key: "$onFillModeChanged",
    value: function $onFillModeChanged(newValue) {
      switch (newValue) {
        case this.VideoOutput.Stretch:
          this.impl.style.objectFit = "fill";
          break;
        case this.VideoOutput.PreserveAspectFit:
          this.impl.style.objectFit = "";
          break;
        case this.VideoOutput.PreserveAspectCrop:
          this.impl.style.objectFit = "cover";
          break;
      }
    }
  }, {
    key: "pause",
    value: function pause() {
      this.impl.pause();
    }
  }, {
    key: "play",
    value: function play() {
      this.impl.play();
    }
  }, {
    key: "seek",
    value: function seek(offset) {
      this.impl.currentTime = offset * 1000;
    }
  }, {
    key: "stop",
    value: function stop() {}
  }, {
    key: "mimetypeFromExtension",
    value: function mimetypeFromExtension(extension) {
      var mimetypes = {
        ogg: "video/ogg",
        ogv: "video/ogg",
        ogm: "video/ogg",
        mp4: "video/mp4",
        webm: "video/webm"
      };
      return mimetypes[extension] || "";
    }
  }]);

  return _class18;
}());

QmlWeb.registerQmlType({
  module: "QtQml",
  name: "Binding",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    target: { type: "QtObject", initialValue: null },
    property: { type: "string", initialValue: "" },
    value: { type: "var", initialValue: undefined },
    when: { type: "bool", initialValue: true }
  }
}, function () {
  function _class19(meta) {
    _classCallCheck(this, _class19);

    QmlWeb.callSuper(this, meta);

    this.$property = undefined;

    this.valueChanged.connect(this, this.$onValueChanged);
    this.targetChanged.connect(this, this.$updateBinding);
    this.propertyChanged.connect(this, this.$updateBinding);
    this.whenChanged.connect(this, this.$updateBinding);
  }

  _createClass(_class19, [{
    key: "$updateBinding",
    value: function $updateBinding() {
      if (!this.when || !this.target || !this.target.hasOwnProperty(this.property) || this.value === undefined) {
        this.$property = undefined;
        return;
      }
      this.$property = this.target.$properties[this.property];
      this.$onValueChanged(this.value); // trigger value update
    }
  }, {
    key: "$onValueChanged",
    value: function $onValueChanged(value) {
      if (value !== undefined && this.$property) {
        this.$property.set(value);
      }
    }
  }]);

  return _class19;
}());

var QMLContext = function () {
  function QMLContext() {
    _classCallCheck(this, QMLContext);
  }

  _createClass(QMLContext, [{
    key: "nameForObject",
    value: function nameForObject(obj) {
      for (var name in this) {
        if (this[name] === obj) {
          return name;
        }
      }
      return undefined;
    }
  }]);

  return QMLContext;
}();

var QMLComponent = function () {
  function QMLComponent(meta) {
    var _this22 = this;

    _classCallCheck(this, QMLComponent);

    if (QmlWeb.constructors[meta.object.$class] === QMLComponent) {
      this.$metaObject = meta.object.$children[0];
    } else {
      this.$metaObject = meta.object;
    }
    this.$context = meta.context;

    this.$jsImports = [];

    if (meta.object.$imports instanceof Array) {
      var moduleImports = [];
      var loadImport = function loadImport(importDesc) {
        if (/\.js$/.test(importDesc[1])) {
          _this22.$jsImports.push(importDesc);
        } else {
          moduleImports.push(importDesc);
        }
      };

      for (var i = 0; i < meta.object.$imports.length; ++i) {
        loadImport(meta.object.$imports[i]);
      }
      QmlWeb.loadImports(this, moduleImports);
      if (this.$context) {
        this.finalizeImports(this.$context);
      }
    }

    /* If this Component does not have any imports, it is likely one that was
     * created within another Component file. It should inherit the
     * importContextId of the Component file it was created within. */
    if (this.importContextId === undefined) {
      this.importContextId = meta.context.importContextId;
    }
  }

  _createClass(QMLComponent, [{
    key: "finalizeImports",
    value: function finalizeImports($context) {
      var engine = QmlWeb.engine;
      for (var i = 0; i < this.$jsImports.length; ++i) {
        var importDesc = this.$jsImports[i];
        var js = engine.loadJS(engine.$resolvePath(importDesc[1]));

        if (!js) {
          console.log("Component.finalizeImports: failed to import JavaScript", importDesc[1]);
          continue;
        }

        if (importDesc[3] !== "") {
          $context[importDesc[3]] = {};
          QmlWeb.importJavascriptInContext(js, $context[importDesc[3]]);
        } else {
          QmlWeb.importJavascriptInContext(js, $context);
        }
      }
    }
  }, {
    key: "$createObject",
    value: function $createObject(parent) {
      var properties = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
      var context = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : this.$context;

      var engine = QmlWeb.engine;
      var oldState = engine.operationState;
      engine.operationState = QmlWeb.QMLOperationState.Init;
      // change base path to current component base path
      var bp = engine.$basePath;
      engine.$basePath = this.$basePath ? this.$basePath : engine.$basePath;

      var newContext = context ? Object.create(context) : new QMLContext();

      if (this.importContextId !== undefined) {
        newContext.importContextId = this.importContextId;
      }

      var item = QmlWeb.construct({
        object: this.$metaObject,
        parent: parent,
        context: newContext,
        isComponentRoot: true
      });

      Object.keys(properties).forEach(function (propname) {
        item[propname] = properties.propname;
      });

      // change base path back
      // TODO looks a bit hacky
      engine.$basePath = bp;

      engine.operationState = oldState;
      return item;
    }
  }, {
    key: "createObject",
    value: function createObject(parent) {
      var properties = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};

      var item = this.$createObject(parent, properties);
      var QMLItem = QmlWeb.getConstructor("QtQuick", "2.0", "Item");

      if (item instanceof QMLItem) {
        item.$properties.parent.set(parent, QmlWeb.QMLProperty.ReasonInit);
      }

      return item;
    }
  }], [{
    key: "getAttachedObject",
    value: function getAttachedObject() {
      if (!this.$Component) {
        this.$Component = new QmlWeb.QObject(this);
        this.$Component.completed = QmlWeb.Signal.signal([]);
        QmlWeb.engine.completedSignals.push(this.$Component.completed);

        this.$Component.destruction = QmlWeb.Signal.signal([]);
      }
      return this.$Component;
    }
  }]);

  return QMLComponent;
}();

QmlWeb.registerQmlType({
  global: true,
  module: "QtQml",
  name: "Component",
  versions: /.*/,
  baseClass: "QtObject",
  constructor: QMLComponent
});

QmlWeb.registerQmlType({
  module: "QtQml",
  name: "Connections",
  versions: /.*/,
  baseClass: "QtObject",
  properties: {
    target: "QtObject",
    ignoreUnknownSignals: "bool"
  }
}, function () {
  function _class20(meta) {
    _classCallCheck(this, _class20);

    QmlWeb.callSuper(this, meta);
    this.target = this.$parent;
    this.$connections = {};

    this.$old_target = this.target;
    this.targetChanged.connect(this, this.$onTargetChanged);
    this.Component.completed.connect(this, this.Component$onCompleted);
  }

  _createClass(_class20, [{
    key: "$onTargetChanged",
    value: function $onTargetChanged() {
      this.$reconnectTarget();
    }
  }, {
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.$reconnectTarget();
    }
  }, {
    key: "$reconnectTarget",
    value: function $reconnectTarget() {
      var old_target = this.$old_target;
      for (var i in this.$connections) {
        var c = this.$connections[i];
        if (c._currentConnection && old_target && old_target[i] && typeof old_target[i].disconnect === "function") {
          old_target[i].disconnect(c._currentConnection);
        }
        if (this.target) {
          c._currentConnection = QmlWeb.connectSignal(this.target, i, c.value, c.objectScope, c.componentScope);
        }
      }
      this.$old_target = this.target;
    }
  }, {
    key: "$setCustomSlot",
    value: function $setCustomSlot(propName, value, objectScope, componentScope) {
      this.$connections[propName] = { value: value, objectScope: objectScope, componentScope: componentScope };
    }
  }]);

  return _class20;
}());

// Base object for all qml elements

QmlWeb.registerQmlType({
  module: "QtQml",
  name: "QtObject",
  versions: /.*/
}, function (_QmlWeb$QObject2) {
  _inherits(_class21, _QmlWeb$QObject2);

  function _class21(meta) {
    _classCallCheck(this, _class21);

    var _this23 = _possibleConstructorReturn(this, (_class21.__proto__ || Object.getPrototypeOf(_class21)).call(this, meta.parent));

    _this23.$isComponentRoot = meta.isComponentRoot;
    _this23.$context = meta.context;

    // Component get own properties
    _this23.$attributes = [];
    for (var key in meta.object) {
      if (!meta.object.hasOwnProperty(key) || !meta.object[key]) {
        continue;
      }
      var name = meta.object[key].__proto__.constructor.name;
      if (name === "QMLPropertyDefinition" || name === "QMLAliasDefinition") {
        _this23.$attributes.push(key);
      }
    }

    var Signal = QmlWeb.Signal;

    _this23.Keys = new QmlWeb.QObject(_this23);
    _this23.Keys.asteriskPresed = Signal.signal();
    _this23.Keys.backPressed = Signal.signal();
    _this23.Keys.backtabPressed = Signal.signal();
    _this23.Keys.callPressed = Signal.signal();
    _this23.Keys.cancelPressed = Signal.signal();
    _this23.Keys.deletePressed = Signal.signal();
    for (var i = 0; i < 10; ++i) {
      _this23.Keys["digit" + i + "Pressed"] = Signal.signal();
    }
    _this23.Keys.escapePressed = Signal.signal();
    _this23.Keys.flipPressed = Signal.signal();
    _this23.Keys.hangupPressed = Signal.signal();
    _this23.Keys.leftPressed = Signal.signal();
    _this23.Keys.menuPressed = Signal.signal();
    _this23.Keys.noPressed = Signal.signal();
    _this23.Keys.pressed = Signal.signal();
    _this23.Keys.released = Signal.signal();
    _this23.Keys.returnPressed = Signal.signal();
    _this23.Keys.rightPressed = Signal.signal();
    _this23.Keys.selectPressed = Signal.signal();
    _this23.Keys.spacePressed = Signal.signal();
    _this23.Keys.tabPressed = Signal.signal();
    _this23.Keys.upPressed = Signal.signal();
    _this23.Keys.volumeDownPressed = Signal.signal();
    _this23.Keys.volumeUpPressed = Signal.signal();
    _this23.Keys.yesPressed = Signal.signal();
    return _this23;
  }

  _createClass(_class21, [{
    key: "getAttributes",
    value: function getAttributes() {
      return this.$attributes;
    }
  }]);

  return _class21;
}(QmlWeb.QObject));

QmlWeb.registerQmlType({
  module: "QtQml",
  name: "Timer",
  versions: /.*/,
  baseClass: "QtObject",
  properties: {
    interval: { type: "int", initialValue: 1000 },
    parent: { type: "QtObject", readOnly: true },
    repeat: "bool",
    running: "bool",
    triggeredOnStart: "bool"
  },
  signals: {
    triggered: []
  }
}, function () {
  function _class22(meta) {
    var _this24 = this;

    _classCallCheck(this, _class22);

    QmlWeb.callSuper(this, meta);

    this.$properties.parent.set(this.$parent, QmlWeb.QMLProperty.ReasonInit);

    /* This ensures that if the user toggles the "running" property manually,
     * the timer will trigger. */
    this.runningChanged.connect(this, this.$onRunningChanged);

    QmlWeb.engine.$addTicker(function () {
      return _this24.$ticker.apply(_this24, arguments);
    });

    QmlWeb.engine.$registerStart(function () {
      if (_this24.running) {
        _this24.restart();
      }
    });

    QmlWeb.engine.$registerStop(function () {
      return _this24.stop();
    });
  }

  _createClass(_class22, [{
    key: "start",
    value: function start() {
      this.running = true;
    }
  }, {
    key: "stop",
    value: function stop() {
      this.running = false;
    }
  }, {
    key: "restart",
    value: function restart() {
      this.stop();
      this.start();
    }
  }, {
    key: "$ticker",
    value: function $ticker(now) {
      if (!this.running) return;
      if (now - this.$prevTrigger >= this.interval) {
        this.$prevTrigger = now;
        this.$trigger();
      }
    }
  }, {
    key: "$onRunningChanged",
    value: function $onRunningChanged() {
      if (this.running) {
        this.$prevTrigger = Date.now();
        if (this.triggeredOnStart) {
          this.$trigger();
        }
      }
    }
  }, {
    key: "$trigger",
    value: function $trigger() {
      if (!this.repeat) {
        // We set the value directly in order to be able to emit the
        // runningChanged signal after triggered, like Qt does it.
        this.$properties.running.val = false;
      }

      // Trigger this.
      this.triggered();

      if (!this.repeat) {
        // Emit changed signal manually after setting the value manually above.
        this.runningChanged();
      }
    }
  }]);

  return _class22;
}());

QmlWeb.registerQmlType({
  module: "QtQuick.Controls",
  name: "Button",
  versions: /.*/,
  baseClass: "QtQuick.Item",
  properties: {
    text: "string",
    enabled: { type: "bool", initialValue: true }
  },
  signals: {
    clicked: []
  }
}, function () {
  function _class23(meta) {
    var _this25 = this;

    _classCallCheck(this, _class23);

    QmlWeb.callSuper(this, meta);

    this.Component.completed.connect(this, this.Component$onCompleted);
    this.textChanged.connect(this, this.$onTextChanged);
    this.enabledChanged.connect(this, this.$onEnabledChanged);

    var button = this.impl = document.createElement("button");
    button.style.pointerEvents = "auto";
    this.dom.appendChild(button);

    button.onclick = function () {
      _this25.clicked();
    };
  }

  _createClass(_class23, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.implicitWidth = this.impl.offsetWidth;
      this.implicitHeight = this.impl.offsetHeight;
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged(newVal) {
      this.impl.textContent = newVal;
      //TODO: Replace those statically sized borders
      this.implicitWidth = this.impl.offsetWidth;
      this.implicitHeight = this.impl.offsetHeight;
    }
  }, {
    key: "$onEnabledChanged",
    value: function $onEnabledChanged(newVal) {
      this.impl.disabled = !newVal;
    }
  }]);

  return _class23;
}());

QmlWeb.registerQmlType({
  module: "QtQuick.Controls",
  name: "CheckBox",
  versions: /.*/,
  baseClass: "QtQuick.Item",
  properties: {
    text: "string",
    checked: "bool",
    color: "color"
  }
}, function () {
  function _class24(meta) {
    var _this26 = this;

    _classCallCheck(this, _class24);

    QmlWeb.callSuper(this, meta);

    this.impl = document.createElement("label");
    this.impl.style.pointerEvents = "auto";

    var checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.style.verticalAlign = "text-bottom";
    checkbox.addEventListener("change", function () {
      _this26.checked = checkbox.checked;
    });
    this.impl.appendChild(checkbox);

    var span = document.createElement("span");
    this.impl.appendChild(span);

    this.dom.appendChild(this.impl);

    var QMLFont = QmlWeb.getConstructor("QtQuick", "2.0", "Font");
    this.font = new QMLFont(this);

    this.Component.completed.connect(this, this.Component$onCompleted);
    this.textChanged.connect(this, this.$onTextChanged);
    this.colorChanged.connect(this, this.$onColorChanged);
    this.checkedChanged.connect(this, this.$onCheckedChanged);
  }

  _createClass(_class24, [{
    key: "$onTextChanged",
    value: function $onTextChanged(newVal) {
      this.impl.children[1].innerHTML = newVal;
      this.implicitHeight = this.impl.offsetHeight;
      this.implicitWidth = this.impl.offsetWidth > 0 ? this.impl.offsetWidth + 4 : 0;
    }
  }, {
    key: "$onColorChanged",
    value: function $onColorChanged(newVal) {
      this.impl.children[1].style.color = new QmlWeb.QColor(newVal);
    }
  }, {
    key: "$onCheckedChanged",
    value: function $onCheckedChanged() {
      this.impl.children[0].checked = this.checked;
    }
  }, {
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.implicitHeight = this.impl.offsetHeight;
      this.implicitWidth = this.impl.offsetWidth > 0 ? this.impl.offsetWidth + 4 : 0;
    }
  }]);

  return _class24;
}());

QmlWeb.registerQmlType({
  module: "QtQuick.Controls",
  name: "ComboBox",
  versions: /.*/,
  baseClass: "QtQuick.Item",
  properties: {
    count: "int",
    currentIndex: "int",
    currentText: "string",
    menu: { type: "array", initialValue: [] },
    model: { type: "array", initialValue: [] },
    pressed: "bool"
  },
  signals: {
    accepted: [],
    activated: [{ type: "int", name: "index" }]
  }
}, function () {
  function _class25(meta) {
    var _this27 = this;

    _classCallCheck(this, _class25);

    QmlWeb.callSuper(this, meta);

    this.dom.style.pointerEvents = "auto";
    this.name = "QMLComboBox";

    this.Component.completed.connect(this, this.Component$onCompleted);
    this.modelChanged.connect(this, this.$onModelChanged);

    this.dom.onclick = function () {
      var index = _this27.dom.firstChild.selectedIndex;
      _this27.currentIndex = index;
      _this27.currentText = _this27.model[index];
      _this27.accepted();
      _this27.activated(index);
    };
  }

  _createClass(_class25, [{
    key: "find",
    value: function find(text) {
      return this.model.indexOf(text);
    }
  }, {
    key: "selectAll",
    value: function selectAll() {
      // TODO
    }
  }, {
    key: "textAt",
    value: function textAt(index) {
      return this.model[index];
    }
  }, {
    key: "$updateImpl",
    value: function $updateImpl() {
      this.currentIndex = 0;
      this.count = this.model.length;
      var entries = [];
      for (var i = 0; i < this.count; i++) {
        var elt = this.model[i];
        //if (elt instanceof Array) { // TODO - optgroups? update model !
        //    var count_i = elt.length;
        //    for (var j = 0; j < count_i; j++)
        //        html += "<option>" + elt[j] + "</option>";
        //}
        //else
        entries.push("<option>" + elt + "</option>");
      }
      // TODO: remove innerHTML, port to DOM
      this.dom.innerHTML = "<select>" + entries.join("") + "</select>";
      this.impl = this.dom.firstChild;
    }
  }, {
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.$updateImpl();
      this.implicitWidth = this.impl.offsetWidth;
      this.implicitHeight = this.impl.offsetHeight;
    }
  }, {
    key: "$onModelChanged",
    value: function $onModelChanged() {
      this.$updateImpl();
    }
  }]);

  return _class25;
}());

QmlWeb.registerQmlType({
  module: "QtQuick.Controls",
  name: "ScrollView",
  versions: /.*/,
  baseClass: "QtQuick.Item",
  properties: {
    contentItem: "Item",
    flickableItem: "Item", // TODO  0) implement it  1) make it read-only
    viewport: "Item", // TODO
    frameVisible: "bool",
    highlightOnFocus: "bool", // TODO test
    verticalScrollBarPolicy: "enum",
    horizontalScrollBarPolicy: "enum",
    style: "Component" // TODO
  },
  defaultProperty: "contentItem"
}, function () {
  function _class26(meta) {
    _classCallCheck(this, _class26);

    QmlWeb.callSuper(this, meta);

    this.css.pointerEvents = "auto";
    this.setupFocusOnDom(this.dom);

    this.contentItemChanged.connect(this, this.$onContentItemChanged);
    this.flickableItemChanged.connect(this, this.$onFlickableItemChanged);
    this.viewportChanged.connect(this, this.$onViewportChanged);
    this.frameVisibleChanged.connect(this, this.$onFrameVisibleChanged);
    this.highlightOnFocusChanged.connect(this, this.$onHighlightOnFocusChanged);
    this.horizontalScrollBarPolicyChanged.connect(this, this.$onHorizontalScrollBarPolicyChanged);
    this.verticalScrollBarPolicyChanged.connect(this, this.$onVerticalScrollBarPolicyChanged);
    this.styleChanged.connect(this, this.$onStyleChanged);
    this.childrenChanged.connect(this, this.$onChildrenChanged);
    this.focusChanged.connect(this, this.$onFocusChanged);

    this.width = this.implicitWidth = 240; // default QML ScrollView width
    this.height = this.implicitHeight = 150; // default QML ScrollView height
    this.width = this.implicitWidth;
    this.height = this.implicitHeight;

    var Qt = QmlWeb.Qt;
    this.contentItem = undefined;
    this.flickableItem = undefined;
    this.viewport = undefined;
    this.frameVisible = false;
    this.highlightOnFocus = false;
    this.verticalScrollBarPolicy = Qt.ScrollBarAsNeeded;
    this.horizontalScrollBarPolicy = Qt.ScrollBarAsNeeded;
    this.style = undefined;
  }

  _createClass(_class26, [{
    key: "$onContentItemChanged",
    value: function $onContentItemChanged(newItem) {
      if ((typeof newItem === "undefined" ? "undefined" : _typeof(newItem)) !== undefined) {
        newItem.parent = this;
      }
    }
  }, {
    key: "$onFlickableItemChanged",
    value: function $onFlickableItemChanged() {}
  }, {
    key: "$onHighlightOnFocusChanged",
    value: function $onHighlightOnFocusChanged() {}
  }, {
    key: "$onViewportChanged",
    value: function $onViewportChanged() {}
  }, {
    key: "$onFocusChanged",
    value: function $onFocusChanged(focus) {
      this.css.outline = this.highlight && focus ? "outline: lightblue solid 2px;" : "";
    }
  }, {
    key: "$onFrameVisibleChanged",
    value: function $onFrameVisibleChanged(visible) {
      this.css.border = visible ? "1px solid gray" : "hidden";
    }
  }, {
    key: "$onHorizontalScrollBarPolicyChanged",
    value: function $onHorizontalScrollBarPolicyChanged(newPolicy) {
      this.css.overflowX = this.$scrollBarPolicyToCssOverflow(newPolicy);
    }
  }, {
    key: "$onVerticalScrollBarPolicyChanged",
    value: function $onVerticalScrollBarPolicyChanged(newPolicy) {
      this.css.overflowY = this.$scrollBarPolicyToCssOverflow(newPolicy);
    }
  }, {
    key: "$onStyleChanged",
    value: function $onStyleChanged() {}
  }, {
    key: "$onChildrenChanged",
    value: function $onChildrenChanged() {
      if (typeof this.contentItem === "undefined" && this.children.length === 1) {
        this.contentItem = this.children[0];
      }
    }
  }, {
    key: "$scrollBarPolicyToCssOverflow",
    value: function $scrollBarPolicyToCssOverflow(policy) {
      var Qt = QmlWeb.Qt;
      switch (policy) {
        case Qt.ScrollBarAsNeeded:
          return "auto";
        case Qt.ScrollBarAlwaysOff:
          return "hidden";
        case Qt.ScrollBarAlwaysOn:
          return "scroll";
      }
      return "auto";
    }
  }]);

  return _class26;
}());

QmlWeb.registerQmlType({
  module: "QtQuick.Controls",
  name: "TextArea",
  versions: /.*/,
  baseClass: "QtQuick.TextEdit"
}, function () {
  function _class27(meta) {
    _classCallCheck(this, _class27);

    QmlWeb.callSuper(this, meta);
    var textarea = this.impl;
    textarea.style.padding = "5px";
    textarea.style.borderWidth = "1px";
    textarea.style.backgroundColor = "#fff";
  }

  return _class27;
}());

/**
 *
 * TextField is used to accept a line of text input.
 * Input constraints can be placed on a TextField item
 * (for example, through a validator or inputMask).
 * Setting echoMode to an appropriate value enables TextField
 * to be used for a password input field.
 *
 * Valid entries for echoMode and alignment are defined in TextInput.
 *
 */

QmlWeb.registerQmlType({
  module: "QtQuick.Controls",
  name: "TextField",
  versions: /.*/,
  baseClass: "QtQuick.Item",
  enums: {
    TextInput: { Normal: 0, Password: 1, NoEcho: 2, PasswordEchoOnEdit: 3 }
  },
  properties: {
    text: "string",
    maximumLength: { type: "int", initialValue: -1 },
    readOnly: "bool",
    validator: "var",
    echoMode: "enum" // TextInput.Normal
  },
  signals: {
    accepted: []
  }
}, function () {
  function _class28(meta) {
    var _this28 = this;

    _classCallCheck(this, _class28);

    QmlWeb.callSuper(this, meta);

    var QMLFont = QmlWeb.getConstructor("QtQuick", "2.0", "Font");
    this.font = new QMLFont(this);

    var input = this.impl = document.createElement("input");
    input.type = "text";
    input.disabled = true;
    input.style.pointerEvents = "auto";
    input.style.margin = "0";
    input.style.width = "100%";
    this.dom.appendChild(input);
    this.setupFocusOnDom(input);
    input.disabled = false;

    this.Component.completed.connect(this, this.Component$onCompleted);
    this.textChanged.connect(this, this.$onTextChanged);
    this.echoModeChanged.connect(this, this.$onEchoModeChanged);
    this.maximumLengthChanged.connect(this, this.$onMaximumLengthChanged);
    this.readOnlyChanged.connect(this, this.$onReadOnlyChanged);
    this.Keys.pressed.connect(this, this.Keys$onPressed);

    this.impl.addEventListener("input", function () {
      return _this28.$updateValue();
    });
  }

  _createClass(_class28, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.implicitWidth = this.impl.offsetWidth;
      this.implicitHeight = this.impl.offsetHeight;
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged(newVal) {
      // See TextInput for comments
      if (this.impl.value !== newVal) {
        this.impl.value = newVal;
      }
    }
  }, {
    key: "$onEchoModeChanged",
    value: function $onEchoModeChanged(newVal) {
      var TextInput = this.TextInput;
      var input = this.impl;
      switch (newVal) {
        case TextInput.Normal:
          input.type = "text";
          break;
        case TextInput.Password:
          input.type = "password";
          break;
        case TextInput.NoEcho:
          // Not supported, use password, that's nearest
          input.type = "password";
          break;
        case TextInput.PasswordEchoOnEdit:
          // Not supported, use password, that's nearest
          input.type = "password";
          break;
      }
    }
  }, {
    key: "$onMaximumLengthChanged",
    value: function $onMaximumLengthChanged(newVal) {
      this.impl.maxLength = newVal < 0 ? null : newVal;
    }
  }, {
    key: "$onReadOnlyChanged",
    value: function $onReadOnlyChanged(newVal) {
      this.impl.disabled = newVal;
    }
  }, {
    key: "Keys$onPressed",
    value: function Keys$onPressed(e) {
      var Qt = QmlWeb.Qt;
      var submit = e.key === Qt.Key_Return || e.key === Qt.Key_Enter;
      if (submit && this.$testValidator()) {
        this.accepted();
        e.accepted = true;
      }
    }
  }, {
    key: "$testValidator",
    value: function $testValidator() {
      if (this.validator) {
        return this.validator.validate(this.text);
      }
      return true;
    }
  }, {
    key: "$updateValue",
    value: function $updateValue() {
      if (this.text !== this.impl.value) {
        this.$canEditReadOnlyProperties = true;
        this.text = this.impl.value;
        this.$canEditReadOnlyProperties = false;
      }
    }
  }]);

  return _class28;
}());

QmlWeb.registerQmlType({
  module: "QtQuick.Window",
  name: "Screen",
  versions: /.*/,
  baseClass: "QtQuick.Item",
  properties: {
    name: "string",
    orientation: "enum",
    orientationUpdateMask: "enum",
    primaryOrientation: "enum",
    pixelDensity: "real",
    devicePixelRatio: "real",
    desktopAvailableHeight: "int",
    desktopAvailableWidth: "int",
    height: "int",
    width: "int"
  }
}, function () {
  function _class29(meta) {
    _classCallCheck(this, _class29);

    QmlWeb.callSuper(this, meta);

    // TODO: rewrite as an attached object and forbid constructing
    this.Component.completed.connect(this, this.Component$onCompleted);
  }

  _createClass(_class29, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var Qt = QmlWeb.Qt;
      this.desktopAvailableHeight = window.outerHeight;
      this.desktopAvailableWidth = window.outerWidth;
      this.devicePixelRatio = window.devicePixelRatio;
      this.height = window.innerHeight;
      this.name = this.name;
      this.orientation = Qt.PrimaryOrientation;
      this.orientationUpdateMask = 0;
      this.pixelDensity = 100.0; // TODO
      this.primaryOrientation = Qt.PrimaryOrientation;
      this.width = window.innerWidth;
    }
  }]);

  return _class29;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "AnimatedImage",
  versions: /.*/,
  baseClass: "Image"
}, function () {
  function _class30(meta) {
    _classCallCheck(this, _class30);

    QmlWeb.callSuper(this, meta);
  }

  return _class30;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Animation",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  enums: {
    Animation: { Infinite: -1 },
    Easing: QmlWeb.Easing
  },
  properties: {
    alwaysRunToEnd: "bool",
    loops: { type: "int", initialValue: 1 },
    paused: "bool",
    running: "bool"
  }
}, function () {
  function _class31(meta) {
    _classCallCheck(this, _class31);

    QmlWeb.callSuper(this, meta);
  }

  _createClass(_class31, [{
    key: "restart",
    value: function restart() {
      this.stop();
      this.start();
    }
  }, {
    key: "start",
    value: function start() {
      this.running = true;
    }
  }, {
    key: "stop",
    value: function stop() {
      this.running = false;
    }
  }, {
    key: "pause",
    value: function pause() {
      this.paused = true;
    }
  }, {
    key: "resume",
    value: function resume() {
      this.paused = false;
    }
  }, {
    key: "complete",
    value: function complete() {
      // To be overridden
      console.log("Unbound method for", this);
    }
  }]);

  return _class31;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Behavior",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    animation: "Animation",
    enabled: { type: "bool", initialValue: true }
  },
  defaultProperty: "animation"
}, function () {
  function _class32(meta) {
    _classCallCheck(this, _class32);

    QmlWeb.callSuper(this, meta);
    this.$on = meta.object.$on;

    this.animationChanged.connect(this, this.$onAnimationChanged);
    this.enabledChanged.connect(this, this.$onEnabledChanged);
  }

  _createClass(_class32, [{
    key: "$onAnimationChanged",
    value: function $onAnimationChanged(newVal) {
      newVal.target = this.$parent;
      newVal.property = this.$on;
      this.$parent.$properties[this.$on].animation = newVal;
    }
  }, {
    key: "$onEnabledChanged",
    value: function $onEnabledChanged(newVal) {
      this.$parent.$properties[this.$on].animation = newVal ? this.animation : null;
    }
  }]);

  return _class32;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "BorderImage",
  versions: /.*/,
  baseClass: "Item",
  enums: {
    BorderImage: {
      Stretch: "stretch", Repeat: "repeat", Round: "round",
      Null: 1, Ready: 2, Loading: 3, Error: 4
    }
  },
  properties: {
    source: "url",
    smooth: { type: "bool", initialValue: true },
    // BorderImage.Stretch
    horizontalTileMode: { type: "enum", initialValue: "stretch" },
    // BorderImage.Stretch
    verticalTileMode: { type: "enum", initialValue: "stretch" },
    progress: "real",
    status: { type: "enum", initialValue: 1 } // BorderImage.Null
  }
}, function () {
  function _class33(meta) {
    var _this29 = this;

    _classCallCheck(this, _class33);

    QmlWeb.callSuper(this, meta);

    var createProperty = QmlWeb.createProperty;
    this.border = new QmlWeb.QObject(this);
    createProperty("int", this.border, "left");
    createProperty("int", this.border, "right");
    createProperty("int", this.border, "top");
    createProperty("int", this.border, "bottom");

    var bg = this.impl = document.createElement("div");
    bg.style.pointerEvents = "none";
    bg.style.height = "100%";
    bg.style.boxSizing = "border-box";
    this.dom.appendChild(bg);

    this.$img = new Image();
    this.$img.addEventListener("load", function () {
      _this29.progress = 1;
      _this29.status = _this29.BorderImage.Ready;
    });
    this.$img.addEventListener("error", function () {
      _this29.status = _this29.BorderImage.Error;
    });

    this.sourceChanged.connect(this, this.$onSourceChanged);
    this.border.leftChanged.connect(this, this.$updateBorder);
    this.border.rightChanged.connect(this, this.$updateBorder);
    this.border.topChanged.connect(this, this.$updateBorder);
    this.border.bottomChanged.connect(this, this.$updateBorder);
    this.horizontalTileModeChanged.connect(this, this.$updateBorder);
    this.verticalTileModeChanged.connect(this, this.$updateBorder);
    this.smoothChanged.connect(this, this.$onSmoothChanged);
  }

  _createClass(_class33, [{
    key: "$onSourceChanged",
    value: function $onSourceChanged(source) {
      this.progress = 0;
      this.status = this.BorderImage.Loading;
      var style = this.impl.style;
      var imageURL = QmlWeb.engine.$resolveImageURL(source);
      style.OBorderImageSource = "url(\"" + imageURL + "\")";
      style.borderImageSource = "url(\"" + imageURL + "\")";
      this.$img.src = imageURL;
      if (this.$img.complete) {
        this.progress = 1;
        this.status = this.BorderImage.Ready;
      }
    }
  }, {
    key: "$updateBorder",
    value: function $updateBorder() {
      var style = this.impl.style;
      var _border = this.border,
          right = _border.right,
          left = _border.left,
          top = _border.top,
          bottom = _border.bottom;

      var slice = top + " " + right + " " + bottom + " " + left + " fill";
      var width = top + "px " + right + "px " + bottom + "px " + left + "px";
      var repeat = this.horizontalTileMode + " " + this.verticalTileMode;
      style.OBorderImageSlice = slice;
      style.OBorderImageRepeat = repeat;
      style.OBorderImageWidth = width;
      style.borderImageSlice = slice;
      style.borderImageRepeat = repeat;
      style.borderImageWidth = width;
    }
  }, {
    key: "$onSmoothChanged",
    value: function $onSmoothChanged(val) {
      var style = this.impl.style;
      if (val) {
        style.imageRendering = "auto";
      } else {
        style.imageRendering = "-webkit-optimize-contrast";
        style.imageRendering = "-moz-crisp-edges";
        style.imageRendering = "crisp-edges";
        style.imageRendering = "pixelated";
      }
    }
  }]);

  return _class33;
}());

// TODO
// Currently only a skeleton implementation

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Canvas",
  versions: /.*/,
  baseClass: "Item",
  properties: {
    available: { type: "bool", initialValue: true },
    canvasSize: { type: "var", initialValue: [0, 0] },
    canvasWindow: { type: "var", initialValue: [0, 0, 0, 0] },
    context: { type: "var", initialValue: {} },
    contextType: { type: "string", initialValue: "contextType" },
    renderStrategy: "enum",
    renderTarget: "enum",
    tileSize: { type: "var", initialValue: [0, 0] }
  },
  signals: {
    imageLoaded: [],
    paint: [{ type: "var", name: "region" }],
    painted: []
  }
}, function () {
  function _class34(meta) {
    _classCallCheck(this, _class34);

    QmlWeb.callSuper(this, meta);
  }

  _createClass(_class34, [{
    key: "cancelRequestAnimationFrame",
    value: function cancelRequestAnimationFrame() /*handle*/{
      return false;
    }
  }, {
    key: "getContext",
    value: function getContext() /*context_id, ...args*/{
      return {};
    }
  }, {
    key: "isImageError",
    value: function isImageError() /*image*/{
      return true;
    }
  }, {
    key: "isImageLoaded",
    value: function isImageLoaded() /*image*/{
      return false;
    }
  }, {
    key: "isImageLoading",
    value: function isImageLoading() /*image*/{
      return false;
    }
  }, {
    key: "loadImage",
    value: function loadImage(image) {
      //loadImageAsync(image);
      if (this.isImageLoaded(image)) {
        this.imageLoaded();
      }
    }
  }, {
    key: "markDirty",
    value: function markDirty(area) {
      // if dirty
      this.paint(area);
    }
  }, {
    key: "requestAnimationFrame",
    value: function requestAnimationFrame() /*callback*/{
      return 0;
    }
  }, {
    key: "requestPaint",
    value: function requestPaint() {}
  }, {
    key: "save",
    value: function save() /*file_name*/{
      return false;
    }
  }, {
    key: "toDataURL",
    value: function toDataURL() /*mime_type*/{
      return "";
    }
  }, {
    key: "unloadImage",
    value: function unloadImage() /*image*/{}
  }]);

  return _class34;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Column",
  versions: /.*/,
  baseClass: "Positioner"
}, function () {
  function _class35(meta) {
    _classCallCheck(this, _class35);

    QmlWeb.callSuper(this, meta);
  }

  _createClass(_class35, [{
    key: "layoutChildren",
    value: function layoutChildren() {
      var curPos = 0;
      var maxWidth = 0;
      for (var i = 0; i < this.children.length; i++) {
        var child = this.children[i];
        if (!child.visible || !child.width || !child.height) {
          continue;
        }
        maxWidth = child.width > maxWidth ? child.width : maxWidth;
        child.y = curPos;
        curPos += child.height + this.spacing;
      }
      this.implicitWidth = maxWidth;
      this.implicitHeight = curPos - this.spacing;
      // We want no spacing at the bottom side
    }
  }]);

  return _class35;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "DoubleValidator",
  versions: /.*/,
  baseClass: "Item",
  enums: {
    DoubleValidator: { StandardNotation: 1, ScientificNotation: 2 }
  },
  properties: {
    bottom: { type: "real", initialValue: -Infinity },
    top: { type: "real", initialValue: Infinity },
    decimals: { type: "int", initialValue: 1000 },
    // DoubleValidator.ScientificNotation
    notation: { type: "enum", initialValue: 2 }
  }
}, function () {
  function _class36(meta) {
    _classCallCheck(this, _class36);

    QmlWeb.callSuper(this, meta);
    this.$standardRegExp = /^(-|\+)?\s*[0-9]+(\.[0-9]+)?$/;
    this.$scientificRegExp = /^(-|\+)?\s*[0-9]+(\.[0-9]+)?(E(-|\+)?[0-9]+)?$/;
  }

  _createClass(_class36, [{
    key: "getRegExpForNotation",
    value: function getRegExpForNotation(notation) {
      switch (notation) {
        case this.DoubleValidator.ScientificNotation:
          return this.$scientificRegExp;
        case this.DoubleValidator.StandardNotation:
          return this.$standardRegExp;
      }
      return null;
    }
  }, {
    key: "$getDecimalsForNumber",
    value: function $getDecimalsForNumber(number) {
      if (Math.round(number) === number) {
        return 0;
      }
      var str = "" + number;
      return (/\d*$/.exec(str)[0].length
      );
    }
  }, {
    key: "validate",
    value: function validate(string) {
      var regExp = this.getRegExpForNotation(this.notation);
      if (!regExp.test(string.trim())) {
        return false;
      }
      var value = parseFloat(string);
      return this.bottom <= value && this.top >= value && this.$getDecimalsForNumber(value) <= this.decimals;
    }
  }]);

  return _class36;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Flow",
  versions: /.*/,
  baseClass: "Positioner",
  enums: {
    Flow: { LeftToRight: 0, TopToBottom: 1 }
  },
  properties: {
    flow: "enum", // Flow.LeftToRight
    layoutDirection: "enum" // Flow.LeftToRight
  }
}, function () {
  function _class37(meta) {
    _classCallCheck(this, _class37);

    QmlWeb.callSuper(this, meta);

    this.flowChanged.connect(this, this.layoutChildren);
    this.layoutDirectionChanged.connect(this, this.layoutChildren);
    this.widthChanged.connect(this, this.layoutChildren);
    this.heightChanged.connect(this, this.layoutChildren);
    this.layoutChildren();
  }

  _createClass(_class37, [{
    key: "layoutChildren",
    value: function layoutChildren() {
      if (this.flow === undefined) {
        // Flow has not been fully initialized yet
        return;
      }

      var curHPos = 0;
      var curVPos = 0;
      var rowSize = 0;
      for (var i = 0; i < this.children.length; i++) {
        var child = this.children[i];
        if (!child.visible || !child.width || !child.height) {
          continue;
        }

        if (this.flow === this.Flow.LeftToRight) {
          if (!this.$isUsingImplicitWidth && curHPos + child.width > this.width) {
            curHPos = 0;
            curVPos += rowSize + this.spacing;
            rowSize = 0;
          }
          rowSize = child.height > rowSize ? child.height : rowSize;
          child.x = this.layoutDirection === this.Flow.TopToBottom ? this.width - curHPos - child.width : curHPos;
          child.y = curVPos;
          curHPos += child.width + this.spacing;
        } else {
          // Flow.TopToBottom
          if (!this.$isUsingImplicitHeight && curVPos + child.height > this.height) {
            curVPos = 0;
            curHPos += rowSize + this.spacing;
            rowSize = 0;
          }
          rowSize = child.width > rowSize ? child.width : rowSize;
          child.x = this.layoutDirection === this.Flow.TopToBottom ? this.width - curHPos - child.width : curHPos;
          child.y = curVPos;
          curVPos += child.height + this.spacing;
        }
      }

      if (this.flow === this.Flow.LeftToRight) {
        this.implicitWidth = curHPos - this.spacing;
        this.implicitHeight = curVPos + rowSize;
      } else {
        // Flow.TopToBottom
        this.implicitWidth = curHPos + rowSize;
        this.implicitHeight = curVPos - this.spacing;
      }
    }
  }]);

  return _class37;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Font",
  versions: /.*/,
  baseClass: "QtQml.QtObject"
}, function (_QmlWeb$QObject3) {
  _inherits(_class38, _QmlWeb$QObject3);

  function _class38(parent) {
    _classCallCheck(this, _class38);

    // TODO: callSuper support?
    var _this30 = _possibleConstructorReturn(this, (_class38.__proto__ || Object.getPrototypeOf(_class38)).call(this, parent));

    _this30.Font = global.Font; // TODO: make a sane enum

    var Font = _this30.Font;
    var createProperty = QmlWeb.createProperty;

    createProperty("bool", _this30, "bold");
    createProperty("enum", _this30, "capitalization", { initialValue: Font.MixedCase });
    createProperty("string", _this30, "family", { initialValue: "sans-serif" });
    createProperty("bool", _this30, "italic");
    createProperty("real", _this30, "letterSpacing");
    createProperty("int", _this30, "pixelSize", { initialValue: 13 });
    createProperty("real", _this30, "pointSize", { initialValue: 10 });
    createProperty("bool", _this30, "strikeout");
    createProperty("bool", _this30, "underline");
    createProperty("enum", _this30, "weight", { initialValue: Font.Normal });
    createProperty("real", _this30, "wordSpacing");

    _this30.$sizeLock = false;

    _this30.boldChanged.connect(_this30, _this30.$onBoldChanged);
    _this30.capitalizationChanged.connect(_this30, _this30.$onCapitalizationChanged);
    _this30.familyChanged.connect(_this30, _this30.$onFamilyChanged);
    _this30.italicChanged.connect(_this30, _this30.$onItalicChanged);
    _this30.letterSpacingChanged.connect(_this30, _this30.$onLetterSpacingChanged);
    _this30.pixelSizeChanged.connect(_this30, _this30.$onPixelSizeChanged);
    _this30.pointSizeChanged.connect(_this30, _this30.$onPointSizeChanged);
    _this30.strikeoutChanged.connect(_this30, _this30.$onStrikeoutChanged);
    _this30.underlineChanged.connect(_this30, _this30.$onUnderlineChanged);
    _this30.weightChanged.connect(_this30, _this30.$onWidthChanged);
    _this30.wordSpacingChanged.connect(_this30, _this30.$onWordSpacingChanged);
    return _this30;
  }

  _createClass(_class38, [{
    key: "$onBoldChanged",
    value: function $onBoldChanged(newVal) {
      var Font = this.Font;
      this.weight = newVal ? Font.Bold : Font.Normal;
    }
  }, {
    key: "$onCapitalizationChanged",
    value: function $onCapitalizationChanged(newVal) {
      var style = this.$parent.dom.firstChild.style;
      style.fontVariant = newVal === this.Font.SmallCaps ? "small-caps" : "none";
      style.textTransform = this.$capitalizationToTextTransform(newVal);
    }
  }, {
    key: "$onFamilyChanged",
    value: function $onFamilyChanged(newVal) {
      var style = this.$parent.dom.firstChild.style;
      style.fontFamily = newVal;
    }
  }, {
    key: "$onItalicChanged",
    value: function $onItalicChanged(newVal) {
      var style = this.$parent.dom.firstChild.style;
      style.fontStyle = newVal ? "italic" : "normal";
    }
  }, {
    key: "$onLetterSpacingChanged",
    value: function $onLetterSpacingChanged(newVal) {
      var style = this.$parent.dom.firstChild.style;
      style.letterSpacing = newVal !== undefined ? newVal + "px" : "";
    }
  }, {
    key: "$onPixelSizeChanged",
    value: function $onPixelSizeChanged(newVal) {
      if (!this.$sizeLock) {
        this.pointSize = newVal * 0.75;
      }
      var val = newVal + "px";
      this.$parent.dom.style.fontSize = val;
      this.$parent.dom.firstChild.style.fontSize = val;
    }
  }, {
    key: "$onPointSizeChanged",
    value: function $onPointSizeChanged(newVal) {
      this.$sizeLock = true;
      this.pixelSize = Math.round(newVal / 0.75);
      this.$sizeLock = false;
    }
  }, {
    key: "$onStrikeoutChanged",
    value: function $onStrikeoutChanged(newVal) {
      var style = this.$parent.dom.firstChild.style;
      style.textDecoration = newVal ? "line-through" : this.$parent.font.underline ? "underline" : "none";
    }
  }, {
    key: "$onUnderlineChanged",
    value: function $onUnderlineChanged(newVal) {
      var style = this.$parent.dom.firstChild.style;
      style.textDecoration = this.$parent.font.strikeout ? "line-through" : newVal ? "underline" : "none";
    }
  }, {
    key: "$onWidthChanged",
    value: function $onWidthChanged(newVal) {
      var style = this.$parent.dom.firstChild.style;
      style.fontWeight = this.$weightToCss(newVal);
    }
  }, {
    key: "$onWordSpacingChanged",
    value: function $onWordSpacingChanged(newVal) {
      var style = this.$parent.dom.firstChild.style;
      style.wordSpacing = newVal !== undefined ? newVal + "px" : "";
    }
  }, {
    key: "$weightToCss",
    value: function $weightToCss(weight) {
      var Font = this.Font;
      switch (weight) {
        case Font.Thin:
          return "100";
        case Font.ExtraLight:
          return "200";
        case Font.Light:
          return "300";
        case Font.Normal:
          return "400";
        case Font.Medium:
          return "500";
        case Font.DemiBold:
          return "600";
        case Font.Bold:
          return "700";
        case Font.ExtraBold:
          return "800";
        case Font.Black:
          return "900";
      }
      return "normal";
    }
  }, {
    key: "$capitalizationToTextTransform",
    value: function $capitalizationToTextTransform(capitalization) {
      var Font = this.Font;
      switch (capitalization) {
        case Font.AllUppercase:
          return "uppercase";
        case Font.AllLowercase:
          return "lowercase";
        case Font.Capitalize:
          return "capitalize";
      }
      return "none";
    }
  }]);

  return _class38;
}(QmlWeb.QObject));

global.Font = {
  // Capitalization
  MixedCase: 0,
  AllUppercase: 1,
  AllLowercase: 2,
  SmallCaps: 3,
  Capitalize: 4,
  // Weight
  Thin: 0,
  ExtraLight: 12,
  Light: 25,
  Normal: 50,
  Medium: 57,
  DemiBold: 63,
  Bold: 75,
  ExtraBold: 81,
  Black: 87
};

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "FontLoader",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  enums: {
    FontLoader: { Null: 0, Ready: 1, Loading: 2, Error: 3 }
  },
  properties: {
    name: "string",
    source: "url",
    status: "enum" // FontLoader.Null
  }
}, function () {
  function _class39(meta) {
    _classCallCheck(this, _class39);

    QmlWeb.callSuper(this, meta);

    this.$domStyle = document.createElement("style");
    this.$lastName = "";
    this.$inTouchName = false;

    /*
      Maximum timeout is the maximum time for a font to load. If font isn't
      loaded in this time, the status is set to Error.
      For both cases (with and without FontLoader.js) if the font takes more
      than the maximum timeout to load, dimensions recalculations for elements
      that are using this font will not be triggered or will have no effect.
       FontLoader.js uses only the last timeout. The state and name properties
      are set immediately when the font loads. If the font could not be loaded,
      the Error status will be set only when this timeout expires. If the font
      loading takes more than the timeout, the name property is set, but the
      status is set to Error.
       Fallback sets the font name immediately and touches it several times to
      trigger dimensions recalcuations. The status is set to Error and should
      not be used.
    */
    // 15 seconds maximum
    this.$timeouts = [20, 50, 100, 300, 500, 1000, 3000, 5000, 10000, 15000];

    this.sourceChanged.connect(this, this.$onSourceChanged);
    this.nameChanged.connect(this, this.$onNameChanged);
  }

  _createClass(_class39, [{
    key: "$loadFont",
    value: function $loadFont(fontName) {
      var _this31 = this;

      /* global FontLoader */
      if (this.$lastName === fontName || this.$inTouchName) {
        return;
      }
      this.$lastName = fontName;

      if (!fontName) {
        this.status = this.FontLoader.Null;
        return;
      }
      this.status = this.FontLoader.Loading;
      if (typeof FontLoader === "function") {
        var fontLoader = new FontLoader([fontName], {
          fontsLoaded: function fontsLoaded(error) {
            if (error !== null) {
              if (_this31.$lastName === fontName && error.notLoadedFontFamilies[0] === fontName) {
                // Set the name for the case of font loading after the timeout.
                _this31.name = fontName;
                _this31.status = _this31.FontLoader.Error;
              }
            }
          },
          fontLoaded: function fontLoaded(fontFamily) {
            if (_this31.$lastName === fontName && fontFamily === fontName) {
              _this31.name = fontName;
              _this31.status = _this31.FontLoader.Ready;
            }
          }
        }, this.$timeouts[this.$timeouts.length - 1]);
        // Else I get problems loading multiple fonts (FontLoader.js bug?)
        FontLoader.testDiv = null;
        fontLoader.loadFonts();
      } else {
        console.warn("FontLoader.js library is not loaded.\nYou should load FontLoader.js if you want to use QtQuick FontLoader elements.\nRefs: https://github.com/smnh/FontLoader.");
        // You should not rely on 'status' property without FontLoader.js.
        this.status = this.FontLoader.Error;
        this.name = fontName;
        this.$cycleTouchName(fontName, 0);
      }
    }
  }, {
    key: "$cycleTouchName",
    value: function $cycleTouchName(fontName, i) {
      var _this32 = this;

      if (this.$lastName !== fontName) {
        return;
      }
      if (i > 0) {
        var name = this.name;
        this.$inTouchName = true;
        // Calling this.nameChanged() is not enough, we have to actually change
        // the value to flush the bindings.
        this.name = "sans-serif";
        this.name = name;
        this.$inTouchName = false;
      }
      if (i < this.$timeouts.length) {
        setTimeout(function () {
          _this32.$cycleTouchName(fontName, i + 1);
        }, this.$timeouts[i] - (i > 0 ? this.$timeouts[i - 1] : 0));
      }
    }
  }, {
    key: "$onSourceChanged",
    value: function $onSourceChanged(font_src) {
      var rand = Math.round(Math.random() * 1e15);
      var fontName = "font_" + Date.now().toString(36) + "_" + rand.toString(36);
      this.$domStyle.innerHTML = "@font-face {\n      font-family: " + fontName + ";\n      src: url('" + font_src + "');\n    }";
      document.getElementsByTagName("head")[0].appendChild(this.$domStyle);
      this.$loadFont(fontName);
    }
  }, {
    key: "$onNameChanged",
    value: function $onNameChanged(fontName) {
      this.$loadFont(fontName);
    }
  }]);

  return _class39;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Grid",
  versions: /.*/,
  baseClass: "Positioner",
  enums: {
    Grid: { LeftToRight: 0, TopToBottom: 1 }
  },
  properties: {
    columns: "int",
    rows: "int",
    flow: "enum",
    layoutDirection: "enum"
  }
}, function () {
  function _class40(meta) {
    _classCallCheck(this, _class40);

    QmlWeb.callSuper(this, meta);

    this.columnsChanged.connect(this, this.layoutChildren);
    this.rowsChanged.connect(this, this.layoutChildren);
    this.flowChanged.connect(this, this.layoutChildren);
    this.layoutDirectionChanged.connect(this, this.layoutChildren);
    this.layoutChildren();
  }

  _createClass(_class40, [{
    key: "layoutChildren",
    value: function layoutChildren() {
      // How many items are actually visible?
      var visibleItems = this.$getVisibleItems();

      // How many rows and columns do we need?

      var _$calculateSize = this.$calculateSize(visibleItems.length),
          _$calculateSize2 = _slicedToArray(_$calculateSize, 2),
          c = _$calculateSize2[0],
          r = _$calculateSize2[1];

      // How big are the colums/rows?


      var _$calculateGrid = this.$calculateGrid(visibleItems, c, r),
          _$calculateGrid2 = _slicedToArray(_$calculateGrid, 2),
          colWidth = _$calculateGrid2[0],
          rowHeight = _$calculateGrid2[1];

      // Do actual positioning
      // When layoutDirection is RightToLeft we need oposite order of coumns


      var step = this.layoutDirection === 1 ? -1 : 1;
      var startingPoint = this.layoutDirection === 1 ? c - 1 : 0;
      var endPoint = this.layoutDirection === 1 ? -1 : c;
      var curHPos = 0;
      var curVPos = 0;
      if (this.flow === 0) {
        for (var i = 0; i < r; i++) {
          for (var j = startingPoint; j !== endPoint; j += step) {
            var item = visibleItems[i * c + j];
            if (!item) {
              break;
            }
            item.x = curHPos;
            item.y = curVPos;

            curHPos += colWidth[j] + this.spacing;
          }
          curVPos += rowHeight[i] + this.spacing;
          curHPos = 0;
        }
      } else {
        for (var _i = startingPoint; _i !== endPoint; _i += step) {
          for (var _j = 0; _j < r; _j++) {
            var _item = visibleItems[_i * r + _j];
            if (!_item) {
              break;
            }
            _item.x = curHPos;
            _item.y = curVPos;

            curVPos += rowHeight[_j] + this.spacing;
          }
          curHPos += colWidth[_i] + this.spacing;
          curVPos = 0;
        }
      }

      // Set implicit size
      var gridWidth = -this.spacing;
      var gridHeight = -this.spacing;
      for (var _i2 in colWidth) {
        gridWidth += colWidth[_i2] + this.spacing;
      }
      for (var _i3 in rowHeight) {
        gridHeight += rowHeight[_i3] + this.spacing;
      }
      this.implicitWidth = gridWidth;
      this.implicitHeight = gridHeight;
    }
  }, {
    key: "$getVisibleItems",
    value: function $getVisibleItems() {
      return this.children.filter(function (child) {
        return child.visible && child.width && child.height;
      });
    }
  }, {
    key: "$calculateSize",
    value: function $calculateSize(length) {
      var cols = void 0;
      var rows = void 0;
      if (!this.columns && !this.rows) {
        cols = 4;
        rows = Math.ceil(length / cols);
      } else if (!this.columns) {
        rows = this.rows;
        cols = Math.ceil(length / rows);
      } else {
        cols = this.columns;
        rows = Math.ceil(length / cols);
      }
      return [cols, rows];
    }
  }, {
    key: "$calculateGrid",
    value: function $calculateGrid(visibleItems, cols, rows) {
      var colWidth = [];
      var rowHeight = [];

      if (this.flow === 0) {
        for (var i = 0; i < rows; i++) {
          for (var j = 0; j < cols; j++) {
            var item = visibleItems[i * cols + j];
            if (!item) {
              break;
            }
            if (!colWidth[j] || item.width > colWidth[j]) {
              colWidth[j] = item.width;
            }
            if (!rowHeight[i] || item.height > rowHeight[i]) {
              rowHeight[i] = item.height;
            }
          }
        }
      } else {
        for (var _i4 = 0; _i4 < cols; _i4++) {
          for (var _j2 = 0; _j2 < rows; _j2++) {
            var _item2 = visibleItems[_i4 * rows + _j2];
            if (!_item2) {
              break;
            }
            if (!rowHeight[_j2] || _item2.height > rowHeight[_j2]) {
              rowHeight[_j2] = _item2.height;
            }
            if (!colWidth[_i4] || _item2.width > colWidth[_i4]) {
              colWidth[_i4] = _item2.width;
            }
          }
        }
      }

      return [colWidth, rowHeight];
    }
  }]);

  return _class40;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Image",
  versions: /.*/,
  baseClass: "Item",
  enums: {
    Image: {
      Stretch: 1, PreserveAspectFit: 2, PreserveAspectCrop: 3,
      Tile: 4, TileVertically: 5, TileHorizontally: 6,

      Null: 1, Ready: 2, Loading: 3, Error: 4
    }
  },
  properties: {
    asynchronous: { type: "bool", initialValue: true },
    cache: { type: "bool", initialValue: true },
    smooth: { type: "bool", initialValue: true },
    fillMode: { type: "enum", initialValue: 1 }, // Image.Stretch
    mirror: "bool",
    progress: "real",
    source: "url",
    status: { type: "enum", initialValue: 1 } // Image.Null
  }
}, function () {
  function _class41(meta) {
    var _this33 = this;

    _classCallCheck(this, _class41);

    QmlWeb.callSuper(this, meta);

    var createProperty = QmlWeb.createProperty;

    this.sourceSize = new QmlWeb.QObject(this);
    createProperty("int", this.sourceSize, "width");
    createProperty("int", this.sourceSize, "height");

    var bg = this.impl = document.createElement("div");
    bg.style.pointerEvents = "none";
    bg.style.height = "100%";
    this.dom.appendChild(bg);

    this.$img = new Image();
    this.$img.addEventListener("load", function () {
      var w = _this33.$img.naturalWidth;
      var h = _this33.$img.naturalHeight;
      _this33.sourceSize.width = w;
      _this33.sourceSize.height = h;
      _this33.implicitWidth = w;
      _this33.implicitHeight = h;
      _this33.progress = 1;
      _this33.status = _this33.Image.Ready;
    });
    this.$img.addEventListener("error", function () {
      _this33.status = _this33.Image.Error;
    });

    this.sourceChanged.connect(this, this.$onSourceChanged);
    this.mirrorChanged.connect(this, this.$onMirrorChanged);
    this.fillModeChanged.connect(this, this.$onFillModeChanged);
    this.smoothChanged.connect(this, this.$onSmoothChanged);
  }

  _createClass(_class41, [{
    key: "$updateFillMode",
    value: function $updateFillMode() {
      var val = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : this.fillMode;

      var style = this.impl.style;
      switch (val) {
        default:
        case this.Image.Stretch:
          style.backgroundRepeat = "auto";
          style.backgroundSize = "100% 100%";
          style.backgroundPosition = "auto";
          break;
        case this.Image.Tile:
          style.backgroundRepeat = "auto";
          style.backgroundSize = "auto";
          style.backgroundPosition = "center";
          break;
        case this.Image.PreserveAspectFit:
          style.backgroundRepeat = "no-repeat";
          style.backgroundSize = "contain";
          style.backgroundPosition = "center";
          break;
        case this.Image.PreserveAspectCrop:
          style.backgroundRepeat = "no-repeat";
          style.backgroundSize = "cover";
          style.backgroundPosition = "center";
          break;
        case this.Image.TileVertically:
          style.backgroundRepeat = "repeat-y";
          style.backgroundSize = "100% auto";
          style.backgroundPosition = "auto";
          break;
        case this.Image.TileHorizontally:
          style.backgroundRepeat = "repeat-x";
          style.backgroundSize = "auto 100%";
          style.backgroundPosition = "auto";
          break;
      }
    }
  }, {
    key: "$onSourceChanged",
    value: function $onSourceChanged(source) {
      this.progress = 0;
      this.status = this.Image.Loading;
      var imageURL = QmlWeb.engine.$resolveImageURL(source);
      this.impl.style.backgroundImage = "url(\"" + imageURL + "\")";
      this.$img.src = imageURL;
      if (this.$img.complete) {
        this.progress = 1;
        this.status = this.Image.Ready;
      }
      this.$updateFillMode();
    }
  }, {
    key: "$onMirrorChanged",
    value: function $onMirrorChanged(val) {
      var transformRule = "scale(-1,1)";
      if (!val) {
        var index = this.transform.indexOf(transformRule);
        if (index >= 0) {
          this.transform.splice(index, 1);
        }
      } else {
        this.transform.push(transformRule);
      }
      this.$updateTransform();
    }
  }, {
    key: "$onFillModeChanged",
    value: function $onFillModeChanged(val) {
      this.$updateFillMode(val);
    }
  }, {
    key: "$onSmoothChanged",
    value: function $onSmoothChanged(val) {
      var style = this.impl.style;
      if (val) {
        style.imageRendering = "auto";
      } else {
        style.imageRendering = "-webkit-optimize-contrast";
        style.imageRendering = "-moz-crisp-edges";
        style.imageRendering = "crisp-edges";
        style.imageRendering = "pixelated";
      }
    }
  }]);

  return _class41;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "IntValidator",
  versions: /.*/,
  baseClass: "Item",
  properties: {
    bottom: { type: "int", initialValue: -2147483647 },
    top: { type: "int", initialValue: 2147483647 }
  }
}, function () {
  function _class42(meta) {
    _classCallCheck(this, _class42);

    QmlWeb.callSuper(this, meta);
  }

  _createClass(_class42, [{
    key: "validate",
    value: function validate(string) {
      var regExp = /^(-|\+)?\s*[0-9]+$/;
      var acceptable = regExp.test(string.trim());

      if (acceptable) {
        var value = parseInt(string, 10);
        acceptable = this.bottom <= value && this.top >= value;
      }
      return acceptable;
    }
  }]);

  return _class42;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Item",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    $opacity: { type: "real", initialValue: 1 },
    parent: "Item",
    state: "string",
    states: "list",
    transitions: "list",
    data: "list",
    children: "list",
    resources: "list",
    transform: "list",
    x: "real",
    y: "real",
    z: "real",
    width: "real",
    height: "real",
    implicitWidth: "real",
    implicitHeight: "real",
    left: "real",
    right: "real",
    top: "real",
    bottom: "real",
    horizontalCenter: "real",
    verticalCenter: "real",
    rotation: "real",
    scale: { type: "real", initialValue: 1 },
    opacity: { type: "real", initialValue: 1 },
    visible: { type: "bool", initialValue: true },
    clip: "bool",
    focus: "bool"
  },
  defaultProperty: "data"
}, function () {
  function _class43(meta) {
    var _this34 = this;

    _classCallCheck(this, _class43);

    QmlWeb.callSuper(this, meta);

    if (this.$parent === null) {
      // This is the root element. Initialize it.
      this.dom = QmlWeb.engine.rootElement || document.body;
      this.dom.innerHTML = "";
      // Needed to make absolute positioning work
      this.dom.style.position = "relative";
      this.dom.style.top = "0";
      this.dom.style.left = "0";
      // No QML stuff should stand out the root element
      this.dom.style.overflow = "hidden";
    } else {
      if (!this.dom) {
        // Create a dom element for this item.
        this.dom = document.createElement("div");
      }
      this.dom.style.position = "absolute";
    }
    this.dom.style.pointerEvents = "none";
    // In case the class is qualified, only use the last part for the css class
    // name.
    var classComponent = meta.object.$class.split(".").pop();
    this.dom.className = "" + classComponent + (this.id ? " " + this.id : "");
    this.css = this.dom.style;
    this.impl = null; // Store the actually drawn element

    this.css.boxSizing = "border-box";

    var createProperty = QmlWeb.createProperty;

    if (this.$isComponentRoot) {
      createProperty("var", this, "activeFocus");
    }

    this.parentChanged.connect(this, this.$onParentChanged_);
    this.dataChanged.connect(this, this.$onDataChanged);
    this.stateChanged.connect(this, this.$onStateChanged);
    this.visibleChanged.connect(this, this.$onVisibleChanged_);
    this.clipChanged.connect(this, this.$onClipChanged);
    this.zChanged.connect(this, this.$onZChanged);
    this.xChanged.connect(this, this.$onXChanged);
    this.yChanged.connect(this, this.$onYChanged);
    this.widthChanged.connect(this, this.$onWidthChanged_);
    this.heightChanged.connect(this, this.$onHeightChanged_);
    this.focusChanged.connect(this, this.$onFocusChanged_);

    this.widthChanged.connect(this, this.$updateHGeometry);
    this.heightChanged.connect(this, this.$updateVGeometry);
    this.implicitWidthChanged.connect(this, this.$onImplicitWidthChanged);
    this.implicitHeightChanged.connect(this, this.$onImplicitHeightChanged);

    this.$isUsingImplicitWidth = true;
    this.$isUsingImplicitHeight = true;

    this.anchors = new QmlWeb.QObject(this);
    createProperty("var", this.anchors, "left");
    createProperty("var", this.anchors, "right");
    createProperty("var", this.anchors, "top");
    createProperty("var", this.anchors, "bottom");
    createProperty("var", this.anchors, "horizontalCenter");
    createProperty("var", this.anchors, "verticalCenter");
    createProperty("Item", this.anchors, "fill");
    createProperty("Item", this.anchors, "centerIn");
    createProperty("real", this.anchors, "margins");
    createProperty("real", this.anchors, "leftMargin");
    createProperty("real", this.anchors, "rightMargin");
    createProperty("real", this.anchors, "topMargin");
    createProperty("real", this.anchors, "bottomMargin");
    this.anchors.leftChanged.connect(this, this.$updateHGeometry);
    this.anchors.rightChanged.connect(this, this.$updateHGeometry);
    this.anchors.topChanged.connect(this, this.$updateVGeometry);
    this.anchors.bottomChanged.connect(this, this.$updateVGeometry);
    this.anchors.horizontalCenterChanged.connect(this, this.$updateHGeometry);
    this.anchors.verticalCenterChanged.connect(this, this.$updateVGeometry);
    this.anchors.fillChanged.connect(this, this.$updateHGeometry);
    this.anchors.fillChanged.connect(this, this.$updateVGeometry);
    this.anchors.centerInChanged.connect(this, this.$updateHGeometry);
    this.anchors.centerInChanged.connect(this, this.$updateVGeometry);
    this.anchors.leftMarginChanged.connect(this, this.$updateHGeometry);
    this.anchors.rightMarginChanged.connect(this, this.$updateHGeometry);
    this.anchors.topMarginChanged.connect(this, this.$updateVGeometry);
    this.anchors.bottomMarginChanged.connect(this, this.$updateVGeometry);
    this.anchors.marginsChanged.connect(this, this.$updateHGeometry);
    this.anchors.marginsChanged.connect(this, this.$updateVGeometry);

    // childrenRect property
    this.childrenRect = new QmlWeb.QObject(this);
    createProperty("real", this.childrenRect, "x"); // TODO ro
    createProperty("real", this.childrenRect, "y"); // TODO ro
    createProperty("real", this.childrenRect, "width"); // TODO ro
    createProperty("real", this.childrenRect, "height"); // TODO ro

    this.rotationChanged.connect(this, this.$updateTransform);
    this.scaleChanged.connect(this, this.$updateTransform);
    this.transformChanged.connect(this, this.$updateTransform);

    this.Component.completed.connect(this, this.Component$onCompleted_);
    this.opacityChanged.connect(this, this.$calculateOpacity);
    if (this.$parent) {
      this.$parent.$opacityChanged.connect(this, this.$calculateOpacity);
    }

    this.spacing = 0;
    this.$revertActions = [];
    this.css.left = this.x + "px";
    this.css.top = this.y + "px";

    // Init size of root element
    if (this.$parent === null) {
      if (!QmlWeb.engine.rootElement) {
        // Case 1: Qml scene is placed in body tag

        // event handling by addEventListener is probably better than setting
        // window.onresize
        var updateQmlGeometry = function updateQmlGeometry() {
          _this34.implicitHeight = window.innerHeight;
          _this34.implicitWidth = window.innerWidth;
        };
        window.addEventListener("resize", updateQmlGeometry);
        updateQmlGeometry();
      } else {
        // Case 2: Qml scene is placed in some element tag

        // we have to call `this.implicitHeight =` and `this.implicitWidth =`
        // each time the rootElement changes it's geometry
        // to reposition child elements of qml scene

        // it is good to have this as named method of dom element, so we can
        // call it from outside too, whenever element changes it's geometry
        // (not only on window resize)
        this.dom.updateQmlGeometry = function () {
          _this34.implicitHeight = _this34.dom.offsetHeight;
          _this34.implicitWidth = _this34.dom.offsetWidth;
        };
        window.addEventListener("resize", this.dom.updateQmlGeometry);
        this.dom.updateQmlGeometry();
      }
    }
  }

  _createClass(_class43, [{
    key: "$onParentChanged_",
    value: function $onParentChanged_(newParent, oldParent, propName) {
      if (oldParent) {
        oldParent.children.splice(oldParent.children.indexOf(this), 1);
        oldParent.childrenChanged();
        oldParent.dom.removeChild(this.dom);
      }
      if (newParent && newParent.children.indexOf(this) === -1) {
        newParent.children.push(this);
        newParent.childrenChanged();
      }
      if (newParent) {
        newParent.dom.appendChild(this.dom);
      }
      this.$updateHGeometry(newParent, oldParent, propName);
      this.$updateVGeometry(newParent, oldParent, propName);
    }
  }, {
    key: "$onDataChanged",
    value: function $onDataChanged(newData) {
      var QMLItem = QmlWeb.getConstructor("QtQuick", "2.0", "Item");
      for (var i in newData) {
        var child = newData[i];
        if (child instanceof QMLItem) {
          child.parent = this; // This will also add it to children.
        } else {
          this.resources.push(child);
        }
      }
    }
  }, {
    key: "$onStateChanged",
    value: function $onStateChanged(newVal, oldVal) {
      // let oldState; // TODO: do we need oldState?
      var newState = void 0;
      for (var i = 0; i < this.states.length; i++) {
        if (this.states[i].name === newVal) {
          newState = this.states[i];
        }
        /*
        else if (this.states[i].name === oldVal) {
          oldState = this.states[i];
        }
        */
      }

      var actions = this.$revertActions.slice();

      // Get current values for revert actions
      for (var _i5 in actions) {
        var action = actions[_i5];
        action.from = action.target[action.property];
      }
      if (newState) {
        var changes = newState.$getAllChanges();

        // Get all actions we need to do and create actions to revert them
        for (var _i6 = 0; _i6 < changes.length; _i6++) {
          this.$applyChange(actions, changes[_i6]);
        }
      }

      // Set all property changes and fetch the actual values afterwards
      // The latter is needed for transitions. We need to set all properties
      // before we fetch the values because properties can be interdependent.
      for (var _i7 in actions) {
        var _action = actions[_i7];
        _action.target.$properties[_action.property].set(_action.value, QmlWeb.QMLProperty.ReasonUser, _action.target, newState ? newState.$context : _action.target.$context);
      }
      for (var _i8 in actions) {
        var _action2 = actions[_i8];
        _action2.to = _action2.target[_action2.property];
        if (_action2.explicit) {
          // Remove binding
          _action2.target[_action2.property] = _action2.target[_action2.property];
          _action2.value = _action2.target[_action2.property];
        }
      }

      // Find the best transition to use
      var transition = void 0;
      var rating = 0;
      for (var _i9 = 0; _i9 < this.transitions.length; _i9++) {
        // We need to stop running transitions, so let's do
        // it while iterating through the transitions anyway
        this.transitions[_i9].$stop();
        var curTransition = this.transitions[_i9];
        var curRating = 0;
        if (curTransition.from === oldVal || curTransition.reversible && curTransition.from === newVal) {
          curRating += 2;
        } else if (curTransition.from === "*") {
          curRating++;
        } else {
          continue;
        }
        if (curTransition.to === newVal || curTransition.reversible && curTransition.to === oldVal) {
          curRating += 2;
        } else if (curTransition.to === "*") {
          curRating++;
        } else {
          continue;
        }
        if (curRating > rating) {
          rating = curRating;
          transition = curTransition;
        }
      }
      if (transition) {
        transition.$start(actions);
      }
    }
  }, {
    key: "$applyChange",
    value: function $applyChange(actions, change) {
      var _this35 = this;

      var arrayFindIndex = QmlWeb.helpers.arrayFindIndex;

      var _loop = function _loop(j) {
        var item = change.$actions[j];

        var action = {
          target: change.target,
          property: item.property,
          origValue: change.target.$properties[item.property].binding || change.target.$properties[item.property].val,
          value: item.value,
          from: change.target[item.property],
          to: undefined,
          explicit: change.explicit
        };

        var actionIndex = arrayFindIndex(actions, function (element) {
          return element.target === action.target && element.property === action.property;
        });
        if (actionIndex !== -1) {
          actions[actionIndex] = action;
        } else {
          actions.push(action);
        }

        // Look for existing revert action, else create it
        var revertIndex = arrayFindIndex(_this35.$revertActions, function (element) {
          return element.target === change.target && element.property === item.property;
        });
        if (revertIndex !== -1 && !change.restoreEntryValues) {
          // We don't want to revert, so remove it
          _this35.$revertActions.splice(revertIndex, 1);
        } else if (revertIndex === -1 && change.restoreEntryValues) {
          _this35.$revertActions.push({
            target: change.target,
            property: item.property,
            value: change.target.$properties[item.property].binding || change.target.$properties[item.property].val,
            from: undefined,
            to: change.target[item.property]
          });
        }
      };

      for (var j = 0; j < change.$actions.length; j++) {
        _loop(j);
      }
    }
  }, {
    key: "$onVisibleChanged_",
    value: function $onVisibleChanged_(newVal) {
      this.css.visibility = newVal ? "inherit" : "hidden";
    }
  }, {
    key: "$onClipChanged",
    value: function $onClipChanged(newVal) {
      this.css.overflow = newVal ? "hidden" : "visible";
    }
  }, {
    key: "$onZChanged",
    value: function $onZChanged() {
      this.$updateTransform();
    }
  }, {
    key: "$onXChanged",
    value: function $onXChanged(newVal) {
      this.css.left = newVal + "px";
      this.$updateHGeometry();
    }
  }, {
    key: "$onYChanged",
    value: function $onYChanged(newVal) {
      this.css.top = newVal + "px";
      this.$updateVGeometry();
    }
  }, {
    key: "$onWidthChanged_",
    value: function $onWidthChanged_(newVal) {
      this.css.width = newVal ? newVal + "px" : "auto";
    }
  }, {
    key: "$onHeightChanged_",
    value: function $onHeightChanged_(newVal) {
      this.css.height = newVal ? newVal + "px" : "auto";
    }
  }, {
    key: "$onFocusChanged",
    value: function $onFocusChanged(newVal) {
      if (newVal) {
        if (this.dom.firstChild) {
          this.dom.firstChild.focus();
        }
        document.qmlFocus = this;
        this.$context.activeFocus = this;
      } else if (document.qmlFocus === this) {
        document.getElementsByTagName("BODY")[0].focus();
        document.qmlFocus = QmlWeb.engine.rootContext().base;
        this.$context.activeFocus = null;
      }
    }
  }, {
    key: "setupFocusOnDom",
    value: function setupFocusOnDom(element) {
      var _this36 = this;

      var updateFocus = function updateFocus() {
        var hasFocus = document.activeElement === _this36.dom || document.activeElement === _this36.dom.firstChild;
        if (_this36.focus !== hasFocus) {
          _this36.focus = hasFocus;
        }
      };
      element.addEventListener("focus", updateFocus);
      element.addEventListener("blur", updateFocus);
    }
  }, {
    key: "$updateTransform",
    value: function $updateTransform() {
      var QMLTranslate = QmlWeb.getConstructor("QtQuick", "2.0", "Translate");
      var QMLRotation = QmlWeb.getConstructor("QtQuick", "2.0", "Rotation");
      var QMLScale = QmlWeb.getConstructor("QtQuick", "2.0", "Scale");
      var transform = "rotate(" + this.rotation + "deg) scale(" + this.scale + ")";
      var filter = "";
      var transformStyle = "preserve-3d";

      for (var i = 0; i < this.transform.length; i++) {
        var t = this.transform[i];
        if (t instanceof QMLRotation) {
          var ax = t.axis;
          transform += " rotate3d(" + ax.x + ", " + ax.y + ", " + ax.z + ", " + ax.angle + "deg)";
        } else if (t instanceof QMLScale) {
          transform += " scale(" + t.xScale + ", " + t.yScale + ")";
        } else if (t instanceof QMLTranslate) {
          transform += " translate(" + t.x + "px, " + t.y + "px)";
        } else if (typeof t.transformType !== "undefined") {
          if (t.transformType === "filter") {
            filter += t.operation + "(" + t.parameters + ") ";
          }
        } else if (typeof t === "string") {
          transform += t;
        }
      }
      if (typeof this.z === "number") {
        transform += " translate3d(0, 0, " + this.z + "px)";
      }
      this.dom.style.transform = transform;
      this.dom.style.transformStyle = transformStyle;
      this.dom.style.webkitTransform = transform; // Chrome, Safari and Opera
      this.dom.style.webkitTransformStyle = transformStyle;
      this.dom.style.msTransform = transform; // IE
      this.dom.style.filter = filter;
      this.dom.style.webkitFilter = filter; // Chrome, Safari and Opera
    }
  }, {
    key: "Component$onCompleted_",
    value: function Component$onCompleted_() {
      this.$calculateOpacity();
    }
  }, {
    key: "$calculateOpacity",
    value: function $calculateOpacity() {
      // TODO: reset all opacity on layer.enabled changed
      /*
      if (false) { // TODO: check layer.enabled
        this.css.opacity = this.opacity;
      }
      */
      var parentOpacity = this.$parent && this.$parent.$opacity || 1;
      this.$opacity = this.opacity * parentOpacity;
      if (this.impl) {
        this.impl.style.opacity = this.$opacity;
      }
    }
  }, {
    key: "$onImplicitWidthChanged",
    value: function $onImplicitWidthChanged() {
      if (this.$isUsingImplicitWidth) {
        this.width = this.implicitWidth;
        this.$isUsingImplicitWidth = true;
      }
    }
  }, {
    key: "$onImplicitHeightChanged",
    value: function $onImplicitHeightChanged() {
      if (this.$isUsingImplicitHeight) {
        this.height = this.implicitHeight;
        this.$isUsingImplicitHeight = true;
      }
    }
  }, {
    key: "$updateHGeometry",
    value: function $updateHGeometry(newVal, oldVal, propName) {
      var anchors = this.anchors || this;
      if (this.$updatingHGeometry) {
        return;
      }
      this.$updatingHGeometry = true;

      var flags = QmlWeb.Signal.UniqueConnection;
      var lM = anchors.leftMargin || anchors.margins;
      var rM = anchors.rightMargin || anchors.margins;
      var w = this.width;
      var left = this.parent ? this.parent.left : 0;

      // Width
      if (propName === "width") {
        this.$isUsingImplicitWidth = false;
      }

      // Position TODO: Layouts

      var u = {}; // our update object

      if (anchors.fill !== undefined) {
        var fill = anchors.fill;
        var props = fill.$properties;
        props.left.changed.connect(this, this.$updateHGeometry, flags);
        props.right.changed.connect(this, this.$updateHGeometry, flags);
        props.width.changed.connect(this, this.$updateHGeometry, flags);

        this.$isUsingImplicitWidth = false;
        u.width = fill.width - lM - rM;
        u.x = fill.left - left + lM;
        u.left = fill.left + lM;
        u.right = fill.right - rM;
        u.horizontalCenter = (u.left + u.right) / 2;
      } else if (anchors.centerIn !== undefined) {
        var horizontalCenter = anchors.centerIn.$properties.horizontalCenter;
        horizontalCenter.changed.connect(this, this.$updateHGeometry, flags);

        u.horizontalCenter = anchors.centerIn.horizontalCenter;
        u.x = u.horizontalCenter - w / 2 - left;
        u.left = u.horizontalCenter - w / 2;
        u.right = u.horizontalCenter + w / 2;
      } else if (anchors.left !== undefined) {
        u.left = anchors.left + lM;
        if (anchors.right !== undefined) {
          u.right = anchors.right - rM;
          this.$isUsingImplicitWidth = false;
          u.width = u.right - u.left;
          u.x = u.left - left;
          u.horizontalCenter = (u.right + u.left) / 2;
        } else if (anchors.horizontalCenter !== undefined) {
          u.horizontalCenter = anchors.horizontalCenter;
          this.$isUsingImplicitWidth = false;
          u.width = (u.horizontalCenter - u.left) * 2;
          u.x = u.left - left;
          u.right = 2 * u.horizontalCenter - u.left;
        } else {
          u.x = u.left - left;
          u.right = u.left + w;
          u.horizontalCenter = u.left + w / 2;
        }
      } else if (anchors.right !== undefined) {
        u.right = anchors.right - rM;
        if (anchors.horizontalCenter !== undefined) {
          u.horizontalCenter = anchors.horizontalCenter;
          this.$isUsingImplicitWidth = false;
          u.width = (u.right - u.horizontalCenter) * 2;
          u.x = 2 * u.horizontalCenter - u.right - left;
          u.left = 2 * u.horizontalCenter - u.right;
        } else {
          u.x = u.right - w - left;
          u.left = u.right - w;
          u.horizontalCenter = u.right - w / 2;
        }
      } else if (anchors.horizontalCenter !== undefined) {
        u.horizontalCenter = anchors.horizontalCenter;
        u.x = u.horizontalCenter - w / 2 - left;
        u.left = u.horizontalCenter - w / 2;
        u.right = u.horizontalCenter + w / 2;
      } else {
        if (this.parent) {
          var leftProp = this.parent.$properties.left;
          leftProp.changed.connect(this, this.$updateHGeometry, flags);
        }

        u.left = this.x + left;
        u.right = u.left + w;
        u.horizontalCenter = u.left + w / 2;
      }

      for (var key in u) {
        this[key] = u[key];
      }

      this.$updatingHGeometry = false;

      if (this.parent) this.$updateChildrenRect(this.parent);
    }
  }, {
    key: "$updateVGeometry",
    value: function $updateVGeometry(newVal, oldVal, propName) {
      var anchors = this.anchors || this;
      if (this.$updatingVGeometry) {
        return;
      }
      this.$updatingVGeometry = true;

      var flags = QmlWeb.Signal.UniqueConnection;
      var tM = anchors.topMargin || anchors.margins;
      var bM = anchors.bottomMargin || anchors.margins;
      var h = this.height;
      var top = this.parent ? this.parent.top : 0;

      // HeighttopProp
      if (propName === "height") {
        this.$isUsingImplicitHeight = false;
      }

      // Position TODO: Layouts

      var u = {}; // our update object

      if (anchors.fill !== undefined) {
        var fill = anchors.fill;
        var props = fill.$properties;
        props.top.changed.connect(this, this.$updateVGeometry, flags);
        props.bottom.changed.connect(this, this.$updateVGeometry, flags);
        props.height.changed.connect(this, this.$updateVGeometry, flags);

        this.$isUsingImplicitHeight = false;
        u.height = fill.height - tM - bM;
        u.y = fill.top - top + tM;
        u.top = fill.top + tM;
        u.bottom = fill.bottom - bM;
        u.verticalCenter = (u.top + u.bottom) / 2;
      } else if (anchors.centerIn !== undefined) {
        var verticalCenter = anchors.centerIn.$properties.verticalCenter;
        verticalCenter.changed.connect(this, this.$updateVGeometry, flags);

        u.verticalCenter = anchors.centerIn.verticalCenter;
        u.y = u.verticalCenter - h / 2 - top;
        u.top = u.verticalCenter - h / 2;
        u.bottom = u.verticalCenter + h / 2;
      } else if (anchors.top !== undefined) {
        u.top = anchors.top + tM;
        if (anchors.bottom !== undefined) {
          u.bottom = anchors.bottom - bM;
          this.$isUsingImplicitHeight = false;
          u.height = u.bottom - u.top;
          u.y = u.top - top;
          u.verticalCenter = (u.bottom + u.top) / 2;
        } else if ((u.verticalCenter = anchors.verticalCenter) !== undefined) {
          this.$isUsingImplicitHeight = false;
          u.height = (u.verticalCenter - u.top) * 2;
          u.y = u.top - top;
          u.bottom = 2 * u.verticalCenter - u.top;
        } else {
          u.y = u.top - top;
          u.bottom = u.top + h;
          u.verticalCenter = u.top + h / 2;
        }
      } else if (anchors.bottom !== undefined) {
        u.bottom = anchors.bottom - bM;
        if ((u.verticalCenter = anchors.verticalCenter) !== undefined) {
          this.$isUsingImplicitHeight = false;
          u.height = (u.bottom - u.verticalCenter) * 2;
          u.y = 2 * u.verticalCenter - u.bottom - top;
          u.top = 2 * u.verticalCenter - u.bottom;
        } else {
          u.y = u.bottom - h - top;
          u.top = u.bottom - h;
          u.verticalCenter = u.bottom - h / 2;
        }
      } else if (anchors.verticalCenter !== undefined) {
        u.verticalCenter = anchors.verticalCenter;
        u.y = u.verticalCenter - h / 2 - top;
        u.top = u.verticalCenter - h / 2;
        u.bottom = u.verticalCenter + h / 2;
      } else {
        if (this.parent) {
          var topProp = this.parent.$properties.top;
          topProp.changed.connect(this, this.$updateVGeometry, flags);
        }

        u.top = this.y + top;
        u.bottom = u.top + h;
        u.verticalCenter = u.top + h / 2;
      }

      for (var key in u) {
        this[key] = u[key];
      }

      this.$updatingVGeometry = false;

      if (this.parent) this.$updateChildrenRect(this.parent);
    }
  }, {
    key: "$updateChildrenRect",
    value: function $updateChildrenRect(component) {
      if (!component || !component.children || component.children.length === 0) {
        return;
      }
      var children = component.children;

      var maxWidth = 0;
      var maxHeight = 0;
      var minX = children.length > 0 ? children[0].x : 0;
      var minY = children.length > 0 ? children[0].y : 0;

      for (var i = 0; i < children.length; i++) {
        var child = children[i];
        maxWidth = Math.max(maxWidth, child.x + child.width);
        maxHeight = Math.max(maxHeight, child.y + child.heighth);
        minX = Math.min(minX, child.x);
        minY = Math.min(minX, child.y);
      }

      component.childrenRect.x = minX;
      component.childrenRect.y = minY;
      component.childrenRect.width = maxWidth;
      component.childrenRect.height = maxHeight;
    }
  }]);

  return _class43;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "ListElement",
  versions: /.*/,
  baseClass: "QtQml.QtObject"
}, function () {
  function _class44(meta) {
    _classCallCheck(this, _class44);

    QmlWeb.callSuper(this, meta);

    var createProperty = QmlWeb.createProperty;
    for (var i in meta.object) {
      if (i[0] !== "$") {
        createProperty("variant", this, i);
      }
    }
    QmlWeb.applyProperties(meta.object, this, this, this.$context);
  }

  return _class44;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "ListModel",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    count: "int",
    $items: "list"
  },
  defaultProperty: "$items"
}, function () {
  function _class45(meta) {
    var _this37 = this;

    _classCallCheck(this, _class45);

    QmlWeb.callSuper(this, meta);

    this.$firstItem = true;
    this.$itemsChanged.connect(this, this.$on$itemsChanged);
    this.$model = new QmlWeb.JSItemModel();
    this.$model.data = function (index, role) {
      return _this37.$items[index][role];
    };
    this.$model.rowCount = function () {
      return _this37.$items.length;
    };
  }

  _createClass(_class45, [{
    key: "$on$itemsChanged",
    value: function $on$itemsChanged(newVal) {
      this.count = this.$items.length;
      if (this.$firstItem && newVal.length > 0) {
        var QMLListElement = QmlWeb.getConstructor("QtQuick", "2.0", "ListElement");
        this.$firstItem = false;
        var roleNames = [];
        var dict = newVal[0];
        if (dict instanceof QMLListElement) {
          dict = dict.$properties;
        }
        for (var i in dict) {
          if (i !== "index") {
            roleNames.push(i);
          }
        }
        this.$model.setRoleNames(roleNames);
      }
    }
  }, {
    key: "append",
    value: function append(dict) {
      var index = this.$items.length;
      var c = 0;

      if (dict instanceof Array) {
        for (var key in dict) {
          this.$items.push(dict[key]);
          c++;
        }
      } else {
        this.$items.push(dict);
        c = 1;
      }

      this.$itemsChanged(this.$items);
      this.$model.rowsInserted(index, index + c);
    }
  }, {
    key: "clear",
    value: function clear() {
      this.$items.length = 0;
      this.count = 0;
      this.$model.modelReset();
    }
  }, {
    key: "get",
    value: function get(index) {
      return this.$items[index];
    }
  }, {
    key: "insert",
    value: function insert(index, dict) {
      this.$items.splice(index, 0, dict);
      this.$itemsChanged(this.$items);
      this.$model.rowsInserted(index, index + 1);
    }
  }, {
    key: "move",
    value: function move(from, to, n) {
      var vals = this.$items.splice(from, n);
      for (var i = 0; i < vals.length; i++) {
        this.$items.splice(to + i, 0, vals[i]);
      }
      this.$model.rowsMoved(from, from + n, to);
    }
  }, {
    key: "remove",
    value: function remove(index) {
      this.$items.splice(index, 1);
      this.$model.rowsRemoved(index, index + 1);
      this.count = this.$items.length;
    }
  }, {
    key: "set",
    value: function set(index, dict) {
      this.$items[index] = dict;
      this.$model.dataChanged(index, index);
    }
  }, {
    key: "setProperty",
    value: function setProperty(index, property, value) {
      this.$items[index][property] = value;
      this.$model.dataChanged(index, index);
    }
  }]);

  return _class45;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "ListView",
  versions: /.*/,
  baseClass: "Repeater",
  properties: {
    orientation: "enum",
    spacing: "real"
  }
}, function () {
  function _class46(meta) {
    _classCallCheck(this, _class46);

    QmlWeb.callSuper(this, meta);
    this.modelChanged.connect(this, this.$styleChanged);
    this.delegateChanged.connect(this, this.$styleChanged);
    this.orientationChanged.connect(this, this.$styleChanged);
    this.spacingChanged.connect(this, this.$styleChanged);
    this._childrenInserted.connect(this, this.$applyStyleOnItem);
  }

  _createClass(_class46, [{
    key: "container",
    value: function container() {
      return this;
    }
  }, {
    key: "$applyStyleOnItem",
    value: function $applyStyleOnItem($item) {
      var Qt = QmlWeb.Qt;
      $item.dom.style.position = "initial";
      if (this.orientation === Qt.Horizontal) {
        $item.dom.style.display = "inline-block";
        if ($item !== this.$items[0]) {
          $item.dom.style["margin-left"] = this.spacing + "px";
        }
      } else {
        $item.dom.style.display = "block";
        if ($item !== this.$items[0]) {
          $item.dom.style["margin-top"] = this.spacing + "px";
        }
      }
    }
  }, {
    key: "$styleChanged",
    value: function $styleChanged() {
      for (var i = 0; i < this.$items.length; ++i) {
        this.$applyStyleOnItem(this.$items[i]);
      }
    }
  }]);

  return _class46;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Loader",
  versions: /.*/,
  baseClass: "Item",
  properties: {
    active: { type: "bool", initialValue: true },
    asynchronous: "bool",
    item: "var",
    progress: "real",
    source: "url",
    sourceComponent: "Component",
    status: { type: "enum", initialValue: 1 }
  },
  signals: {
    loaded: []
  }
}, function () {
  function _class47(meta) {
    _classCallCheck(this, _class47);

    QmlWeb.callSuper(this, meta);

    this.$sourceUrl = "";

    this.activeChanged.connect(this, this.$onActiveChanged);
    this.sourceChanged.connect(this, this.$onSourceChanged);
    this.sourceComponentChanged.connect(this, this.$onSourceComponentChanged);
    this.widthChanged.connect(this, this.$updateGeometry);
    this.heightChanged.connect(this, this.$updateGeometry);
  }

  _createClass(_class47, [{
    key: "$onActiveChanged",
    value: function $onActiveChanged() {
      if (!this.active) {
        this.$unload();
        return;
      }
      if (this.source) {
        this.$onSourceChanged(this.source);
      } else if (this.sourceComponent) {
        this.$onSourceComponentChanged(this.sourceComponent);
      }
    }
  }, {
    key: "$onSourceChanged",
    value: function $onSourceChanged(fileName) {
      // TODO
      // if (fileName == this.$sourceUrl && this.item !== undefined) return;
      if (!this.active) return;
      this.$unload();

      var tree = QmlWeb.engine.loadComponent(fileName);
      var QMLComponent = QmlWeb.getConstructor("QtQml", "2.0", "Component");
      var meta = { object: tree, context: this, parent: this };
      var qmlComponent = new QMLComponent(meta);
      qmlComponent.$basePath = QmlWeb.engine.extractBasePath(tree.$file);
      qmlComponent.$imports = tree.$imports;
      qmlComponent.$file = tree.$file;
      QmlWeb.engine.loadImports(tree.$imports, qmlComponent.$basePath, qmlComponent.importContextId);
      var loadedComponent = this.$createComponentObject(qmlComponent, this);
      this.sourceComponent = loadedComponent;
      this.$sourceUrl = fileName;
    }
  }, {
    key: "$onSourceComponentChanged",
    value: function $onSourceComponentChanged(newItem) {
      if (!this.active) return;
      this.$unload();
      var QMLComponent = QmlWeb.getConstructor("QtQml", "2.0", "Component");
      var qmlComponent = newItem;
      if (newItem instanceof QMLComponent) {
        qmlComponent = newItem.$createObject(this, {}, this);
      }
      qmlComponent.parent = this;
      this.item = qmlComponent;
      this.$updateGeometry();
      if (this.item) {
        this.loaded();
      }
    }
  }, {
    key: "setSource",
    value: function setSource(url, options) {
      this.$sourceUrl = url;
      this.props = options;
      this.source = url;
    }
  }, {
    key: "$unload",
    value: function $unload() {
      if (!this.item) return;
      this.item.$delete();
      this.item.parent = undefined;
      this.item = undefined;
    }
  }, {
    key: "$callOnCompleted",
    value: function $callOnCompleted(child) {
      child.Component.completed();
      var QMLBaseObject = QmlWeb.getConstructor("QtQml", "2.0", "QtObject");
      for (var i = 0; i < child.$tidyupList.length; i++) {
        if (child.$tidyupList[i] instanceof QMLBaseObject) {
          this.$callOnCompleted(child.$tidyupList[i]);
        }
      }
    }
  }, {
    key: "$createComponentObject",
    value: function $createComponentObject(qmlComponent, parent) {
      var newComponent = qmlComponent.createObject(parent);
      qmlComponent.finalizeImports();
      if (QmlWeb.engine.operationState !== QmlWeb.QMLOperationState.Init) {
        // We don't call those on first creation, as they will be called
        // by the regular creation-procedures at the right time.
        QmlWeb.engine.$initializePropertyBindings();
        this.$callOnCompleted(newComponent);
      }
      return newComponent;
    }
  }, {
    key: "$updateGeometry",
    value: function $updateGeometry() {
      // Loader size doesn't exist
      if (!this.width) {
        this.width = this.item ? this.item.width : 0;
      } else if (this.item) {
        // Loader size exists
        this.item.width = this.width;
      }

      if (!this.height) {
        this.height = this.item ? this.item.height : 0;
      } else if (this.item) {
        // Loader size exists
        this.item.height = this.height;
      }
    }
  }]);

  return _class47;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "MouseArea",
  versions: /.*/,
  baseClass: "Item",
  properties: {
    acceptedButtons: { type: "variant", initialValue: 1 }, // Qt.LeftButton
    enabled: { type: "bool", initialValue: true },
    hoverEnabled: "bool",
    mouseX: "real",
    mouseY: "real",
    pressed: "bool",
    containsMouse: "bool",
    pressedButtons: { type: "variant", initialValue: 0 },
    cursorShape: "enum" // Qt.ArrowCursor
  },
  signals: {
    clicked: [{ type: "variant", name: "mouse" }],
    doubleClicked: [{ type: "variant", name: "mouse" }],
    entered: [],
    exited: [],
    positionChanged: [{ type: "variant", name: "mouse" }]
  }
}, function () {
  function _class48(meta) {
    var _this38 = this;

    _classCallCheck(this, _class48);

    QmlWeb.callSuper(this, meta);

    this.dom.style.pointerEvents = "all";

    // IE does not handle mouse clicks to transparent divs, so we have
    // to set a background color and make it invisible using opacity
    // as that doesn't affect the mouse handling.
    this.dom.style.backgroundColor = "white";
    this.dom.style.opacity = 0;

    this.cursorShapeChanged.connect(this, this.$onCursorShapeChanged);

    this.dom.addEventListener("click", function (e) {
      return _this38.$handleClick(e);
    });
    this.dom.addEventListener("contextmenu", function (e) {
      return _this38.$handleClick(e);
    });
    var handleMouseUp = function handleMouseUp() {
      _this38.pressed = false;
      _this38.pressedButtons = 0;
      document.removeEventListener("mouseup", handleMouseUp);
    };
    this.dom.addEventListener("mousedown", function (e) {
      if (!_this38.enabled) return;
      var mouse = _this38.$eventToMouse(e);
      _this38.mouseX = mouse.x;
      _this38.mouseY = mouse.y;
      _this38.pressed = true;
      _this38.pressedButtons = mouse.button;
      document.addEventListener("mouseup", handleMouseUp);
    });
    this.dom.addEventListener("dblclick", function (e) {
      _this38.doubleClicked(e);
    });
    this.dom.addEventListener("mouseover", function () {
      _this38.containsMouse = true;
      _this38.entered();
    });
    this.dom.addEventListener("mouseout", function () {
      _this38.containsMouse = false;
      _this38.exited();
    });
    this.dom.addEventListener("mousemove", function (e) {
      if (!_this38.enabled || !_this38.hoverEnabled && !_this38.pressed) return;
      var mouse = _this38.$eventToMouse(e);
      _this38.positionChanged(mouse);
      _this38.mouseX = mouse.x;
      _this38.mouseY = mouse.y;
    });
  }

  _createClass(_class48, [{
    key: "$onCursorShapeChanged",
    value: function $onCursorShapeChanged() {
      this.dom.style.cursor = this.$cursorShapeToCSS();
    }
  }, {
    key: "$handleClick",
    value: function $handleClick(e) {
      var mouse = this.$eventToMouse(e);
      if (this.enabled && this.acceptedButtons & mouse.button) {
        this.clicked(mouse);
      }
      // This decides whether to show the browser's context menu on right click or
      // not
      return !(this.acceptedButtons & QmlWeb.Qt.RightButton);
    }
  }, {
    key: "$eventToMouse",
    value: function $eventToMouse(e) {
      var Qt = QmlWeb.Qt;
      return {
        accepted: true,
        button: e.button === 0 ? Qt.LeftButton : e.button === 1 ? Qt.MiddleButton : e.button === 2 ? Qt.RightButton : 0,
        modifiers: e.ctrlKey * Qt.CtrlModifier | e.altKey * Qt.AltModifier | e.shiftKey * Qt.ShiftModifier | e.metaKey * Qt.MetaModifier,
        x: e.offsetX || e.layerX,
        y: e.offsetY || e.layerY
      };
    }

    // eslint-disable-next-line complexity

  }, {
    key: "$cursorShapeToCSS",
    value: function $cursorShapeToCSS() {
      var Qt = QmlWeb.Qt;
      switch (this.cursorShape) {
        case Qt.ArrowCursor:
          return "default";
        case Qt.UpArrowCursor:
          return "n-resize";
        case Qt.CrossCursor:
          return "crosshair";
        case Qt.WaitCursor:
          return "wait";
        case Qt.IBeamCursor:
          return "text";
        case Qt.SizeVerCursor:
          return "ew-resize";
        case Qt.SizeHorCursor:
          return "ns-resize";
        case Qt.SizeBDiagCursor:
          return "nesw-resize";
        case Qt.SizeFDiagCursor:
          return "nwse-resize";
        case Qt.SizeAllCursor:
          return "all-scroll";
        case Qt.BlankCursor:
          return "none";
        case Qt.SplitVCursor:
          return "row-resize";
        case Qt.SplitHCursor:
          return "col-resize";
        case Qt.PointingHandCursor:
          return "pointer";
        case Qt.ForbiddenCursor:
          return "not-allowed";
        case Qt.WhatsThisCursor:
          return "help";
        case Qt.BusyCursor:
          return "progress";
        case Qt.OpenHandCursor:
          return "grab";
        case Qt.ClosedHandCursor:
          return "grabbing";
        case Qt.DragCopyCursor:
          return "copy";
        case Qt.DragMoveCursor:
          return "move";
        case Qt.DragLinkCursor:
          return "alias";
        //case Qt.BitmapCursor: return "auto";
        //case Qt.CustomCursor: return "auto";
      }
      return "auto";
    }
  }]);

  return _class48;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "NumberAnimation",
  versions: /.*/,
  baseClass: "PropertyAnimation"
}, function () {
  function _class49(meta) {
    var _this39 = this;

    _classCallCheck(this, _class49);

    QmlWeb.callSuper(this, meta);

    this.$at = 0;
    this.$loop = 0;

    QmlWeb.engine.$addTicker(function () {
      return _this39.$ticker.apply(_this39, arguments);
    });
    this.runningChanged.connect(this, this.$onRunningChanged);
  }

  _createClass(_class49, [{
    key: "$startLoop",
    value: function $startLoop() {
      for (var i in this.$actions) {
        var _action3 = this.$actions[i];
        _action3.from = _action3.from !== undefined ? _action3.from : _action3.target[_action3.property];
      }
      this.$at = 0;
    }
  }, {
    key: "$ticker",
    value: function $ticker(now, elapsed) {
      if (!this.running && this.$loop !== -1 || this.paused) {
        // $loop === -1 is a marker to just finish this run
        return;
      }
      if (this.$at === 0 && this.$loop === 0 && !this.$actions.length) {
        this.$redoActions();
      }
      this.$at += elapsed / this.duration;
      if (this.$at >= 1) {
        this.complete();
        return;
      }
      for (var i in this.$actions) {
        var _action4 = this.$actions[i];
        var value = _action4.from + (_action4.to - _action4.from) * this.easing.$valueForProgress(this.$at);
        var property = _action4.target.$properties[_action4.property];
        property.set(value, QmlWeb.QMLProperty.ReasonAnimation);
      }
    }
  }, {
    key: "$onRunningChanged",
    value: function $onRunningChanged(newVal) {
      if (newVal) {
        this.$startLoop();
        this.paused = false;
      } else if (this.alwaysRunToEnd && this.$at < 1) {
        this.$loop = -1; // -1 is used as a marker to stop
      } else {
        this.$loop = 0;
        this.$actions = [];
      }
    }
  }, {
    key: "complete",
    value: function complete() {
      for (var i in this.$actions) {
        var _action5 = this.$actions[i];
        var property = _action5.target.$properties[_action5.property];
        property.set(_action5.to, QmlWeb.QMLProperty.ReasonAnimation);
      }
      this.$loop++;
      if (this.$loop === this.loops) {
        this.running = false;
      } else if (!this.running) {
        this.$actions = [];
      } else {
        this.$startLoop(this);
      }
    }
  }]);

  return _class49;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "ParallelAnimation",
  versions: /.*/,
  baseClass: "Animation",
  enums: {
    Animation: { Infinite: Math.Infinite }
  },
  properties: {
    animations: "list"
  },
  defaultProperty: "animations"
}, function () {
  function _class50(meta) {
    var _this40 = this;

    _classCallCheck(this, _class50);

    QmlWeb.callSuper(this, meta);

    this.$runningAnimations = 0;

    this.animationsChanged.connect(this, this.$onAnimationsChanged);

    QmlWeb.engine.$registerStart(function () {
      if (!_this40.running) return;
      self.running = false; // toggled back by start();
      self.start();
    });
    QmlWeb.engine.$registerStop(function () {
      return _this40.stop();
    });
  }

  _createClass(_class50, [{
    key: "$onAnimationsChanged",
    value: function $onAnimationsChanged() {
      var flags = QmlWeb.Signal.UniqueConnection;
      for (var i = 0; i < this.animations.length; i++) {
        var animation = this.animations[i];
        animation.runningChanged.connect(this, this.$animationFinished, flags);
      }
    }
  }, {
    key: "$animationFinished",
    value: function $animationFinished(newVal) {
      this.$runningAnimations += newVal ? 1 : -1;
      if (this.$runningAnimations === 0) {
        this.running = false;
      }
    }
  }, {
    key: "start",
    value: function start() {
      if (this.running) return;
      this.running = true;
      for (var i = 0; i < this.animations.length; i++) {
        this.animations[i].start();
      }
    }
  }, {
    key: "stop",
    value: function stop() {
      if (!this.running) return;
      for (var i = 0; i < this.animations.length; i++) {
        this.animations[i].stop();
      }
      this.running = false;
    }
  }, {
    key: "complete",
    value: function complete() {
      this.stop();
    }
  }]);

  return _class50;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Positioner",
  versions: /.*/,
  baseClass: "Item",
  properties: {
    spacing: "int"
  }
}, function () {
  function _class51(meta) {
    _classCallCheck(this, _class51);

    QmlWeb.callSuper(this, meta);

    this.childrenChanged.connect(this, this.$onChildrenChanged);
    this.spacingChanged.connect(this, this.layoutChildren);
    this.childrenChanged.connect(this, this.layoutChildren);
    this.layoutChildren();
  }

  _createClass(_class51, [{
    key: "$onChildrenChanged",
    value: function $onChildrenChanged() {
      var flags = QmlWeb.Signal.UniqueConnection;
      for (var i = 0; i < this.children.length; i++) {
        var child = this.children[i];
        child.widthChanged.connect(this, this.layoutChildren, flags);
        child.heightChanged.connect(this, this.layoutChildren, flags);
        child.visibleChanged.connect(this, this.layoutChildren, flags);
      }
    }
  }]);

  return _class51;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "PropertyAnimation",
  versions: /.*/,
  baseClass: "Animation",
  properties: {
    duration: { type: "int", initialValue: 250 },
    from: "real",
    to: "real",
    properties: "string",
    property: "string",
    target: "QtObject",
    targets: "list"
  }
}, function () {
  function _class52(meta) {
    _classCallCheck(this, _class52);

    QmlWeb.callSuper(this, meta);

    var createProperty = QmlWeb.createProperty;
    this.easing = new QmlWeb.QObject(this);
    createProperty("enum", this.easing, "type", { initialValue: this.Easing.Linear });
    createProperty("real", this.easing, "amplitude", { initialValue: 1 });
    createProperty("real", this.easing, "overshoot", { initialValue: 1.70158 });
    createProperty("real", this.easing, "period", { initialValue: 0.3 });

    this.easing.$valueForProgress = function (t) {
      return QmlWeb.$ease(this.type, this.period, this.amplitude, this.overshoot, t);
    };

    this.$props = [];
    this.$targets = [];
    this.$actions = [];

    this.targetChanged.connect(this, this.$redoTargets);
    this.targetsChanged.connect(this, this.$redoTargets);
    this.propertyChanged.connect(this, this.$redoProperties);
    this.propertiesChanged.connect(this, this.$redoProperties);

    if (meta.object.$on !== undefined) {
      this.property = meta.object.$on;
      this.target = this.$parent;
    }
  }

  _createClass(_class52, [{
    key: "$redoActions",
    value: function $redoActions() {
      this.$actions = [];
      for (var i = 0; i < this.$targets.length; i++) {
        for (var j in this.$props) {
          this.$actions.push({
            target: this.$targets[i],
            property: this.$props[j],
            from: this.from,
            to: this.to
          });
        }
      }
    }
  }, {
    key: "$redoProperties",
    value: function $redoProperties() {
      this.$props = this.properties.split(",");

      // Remove whitespaces
      for (var i = 0; i < this.$props.length; i++) {
        var matches = this.$props[i].match(/\w+/);
        if (matches) {
          this.$props[i] = matches[0];
        } else {
          this.$props.splice(i, 1);
          i--;
        }
      }
      // Merge properties and property
      if (this.property && this.$props.indexOf(this.property) === -1) {
        this.$props.push(this.property);
      }
    }
  }, {
    key: "$redoTargets",
    value: function $redoTargets() {
      this.$targets = this.targets.slice();
      if (this.target && this.$targets.indexOf(this.target) === -1) {
        this.$targets.push(this.target);
      }
    }
  }]);

  return _class52;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "PropertyChanges",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    target: "QtObject",
    explicit: "bool",
    restoreEntryValues: { type: "bool", initialValue: true }
  }
}, function () {
  function _class53(meta) {
    _classCallCheck(this, _class53);

    QmlWeb.callSuper(this, meta);

    this.$actions = [];
  }

  _createClass(_class53, [{
    key: "$setCustomData",
    value: function $setCustomData(property, value) {
      this.$actions.push({ property: property, value: value });
    }
  }]);

  return _class53;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Rectangle",
  versions: /.*/,
  baseClass: "Item",
  properties: {
    color: { type: "color", initialValue: "white" },
    radius: "real"
  }
}, function () {
  function _class54(meta) {
    _classCallCheck(this, _class54);

    QmlWeb.callSuper(this, meta);

    var createProperty = QmlWeb.createProperty;
    this.border = new QmlWeb.QObject(this);
    createProperty("color", this.border, "color", { initialValue: "black" });
    createProperty("int", this.border, "width", { initialValue: 1 });
    this.$borderActive = false;

    var bg = this.impl = document.createElement("div");
    bg.style.pointerEvents = "none";
    bg.style.position = "absolute";
    bg.style.left = bg.style.right = bg.style.top = bg.style.bottom = "0px";
    bg.style.borderWidth = "0px";
    bg.style.borderStyle = "solid";
    bg.style.borderColor = "black";
    bg.style.backgroundColor = "white";
    this.dom.appendChild(bg);

    this.colorChanged.connect(this, this.$onColorChanged);
    this.radiusChanged.connect(this, this.$onRadiusChanged);
    this.border.colorChanged.connect(this, this.border$onColorChanged);
    this.border.widthChanged.connect(this, this.border$onWidthChanged);
    this.widthChanged.connect(this, this.$updateBorder);
    this.heightChanged.connect(this, this.$updateBorder);
  }

  _createClass(_class54, [{
    key: "$onColorChanged",
    value: function $onColorChanged(newVal) {
      this.impl.style.backgroundColor = new QmlWeb.QColor(newVal);
    }
  }, {
    key: "border$onColorChanged",
    value: function border$onColorChanged(newVal) {
      this.$borderActive = true;
      this.impl.style.borderColor = new QmlWeb.QColor(newVal);
      this.$updateBorder();
    }
  }, {
    key: "border$onWidthChanged",
    value: function border$onWidthChanged() {
      this.$borderActive = true;
      this.$updateBorder();
    }
  }, {
    key: "$onRadiusChanged",
    value: function $onRadiusChanged(newVal) {
      this.impl.style.borderRadius = newVal + "px";
    }
  }, {
    key: "$updateBorder",
    value: function $updateBorder() {
      var border = this.$borderActive ? Math.max(0, this.border.width) : 0;
      var style = this.impl.style;
      if (border * 2 > this.width || border * 2 > this.height) {
        // Border is covering the whole background
        style.borderWidth = "0px";
        style.borderTopWidth = this.height + "px";
      } else {
        style.borderWidth = border + "px";
      }
    }
  }]);

  return _class54;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "RegExpValidator",
  versions: /.*/,
  baseClass: "Item",
  properties: {
    regExp: "var"
  }
}, function () {
  function _class55(meta) {
    _classCallCheck(this, _class55);

    QmlWeb.callSuper(this, meta);
  }

  _createClass(_class55, [{
    key: "validate",
    value: function validate(string) {
      if (!this.regExp) return true;
      return this.regExp.test(string);
    }
  }]);

  return _class55;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Repeater",
  versions: /.*/,
  baseClass: "Item",
  properties: {
    delegate: "Component",
    model: { type: "variant", initialValue: 0 },
    count: "int"
  },
  signals: {
    _childrenInserted: []
  },
  defaultProperty: "delegate"
}, function () {
  function _class56(meta) {
    _classCallCheck(this, _class56);

    QmlWeb.callSuper(this, meta);

    this.parent = meta.parent;
    // TODO: some (all ?) of the components including Repeater needs to know own
    // parent at creation time. Please consider this major change.

    this.$completed = false;
    this.$items = []; // List of created items

    this.modelChanged.connect(this, this.$onModelChanged);
    this.delegateChanged.connect(this, this.$onDelegateChanged);
    this.parentChanged.connect(this, this.$onParentChanged);
  }

  _createClass(_class56, [{
    key: "container",
    value: function container() {
      return this.parent;
    }
  }, {
    key: "itemAt",
    value: function itemAt(index) {
      return this.$items[index];
    }
  }, {
    key: "$onModelChanged",
    value: function $onModelChanged() {
      this.$applyModel();
    }
  }, {
    key: "$onDelegateChanged",
    value: function $onDelegateChanged() {
      this.$applyModel();
    }
  }, {
    key: "$onParentChanged",
    value: function $onParentChanged() {
      this.$applyModel();
    }
  }, {
    key: "$getModel",
    value: function $getModel() {
      var QMLListModel = QmlWeb.getConstructor("QtQuick", "2.0", "ListModel");
      return this.model instanceof QMLListModel ? this.model.$model : this.model;
    }
  }, {
    key: "$applyModel",
    value: function $applyModel() {
      if (!this.delegate || !this.parent) {
        return;
      }
      var model = this.$getModel();
      if (model instanceof QmlWeb.JSItemModel) {
        var flags = QmlWeb.Signal.UniqueConnection;
        model.dataChanged.connect(this, this.$_onModelDataChanged, flags);
        model.rowsInserted.connect(this, this.$insertChildren, flags);
        model.rowsMoved.connect(this, this.$_onRowsMoved, flags);
        model.rowsRemoved.connect(this, this.$_onRowsRemoved, flags);
        model.modelReset.connect(this, this.$_onModelReset, flags);

        this.$removeChildren(0, this.$items.length);
        this.$insertChildren(0, model.rowCount());
      } else if (typeof model === "number") {
        // must be more elegant here.. do not delete already created models..
        //this.$removeChildren(0, this.$items.length);
        //this.$insertChildren(0, model);

        if (this.$items.length > model) {
          // have more than we need
          this.$removeChildren(model, this.$items.length);
        } else {
          // need more
          this.$insertChildren(this.$items.length, model);
        }
      } else if (model instanceof Array) {
        this.$removeChildren(0, this.$items.length);
        this.$insertChildren(0, model.length);
      }
    }
  }, {
    key: "$callOnCompleted",
    value: function $callOnCompleted(child) {
      child.Component.completed();
      var QMLBaseObject = QmlWeb.getConstructor("QtQml", "2.0", "QtObject");
      for (var i = 0; i < child.$tidyupList.length; i++) {
        if (child.$tidyupList[i] instanceof QMLBaseObject) {
          this.$callOnCompleted(child.$tidyupList[i]);
        }
      }
    }
  }, {
    key: "$_onModelDataChanged",
    value: function $_onModelDataChanged(startIndex, endIndex, roles) {
      var model = this.$getModel();
      var roleNames = roles || model.roleNames;
      for (var index = startIndex; index <= endIndex; index++) {
        var _item3 = this.$items[index];
        for (var i in roleNames) {
          _item3.$properties[roleNames[i]].set(model.data(index, roleNames[i]), QmlWeb.QMLProperty.ReasonInit, _item3, this.model.$context);
        }
      }
    }
  }, {
    key: "$_onRowsMoved",
    value: function $_onRowsMoved(sourceStartIndex, sourceEndIndex, destinationIndex) {
      var vals = this.$items.splice(sourceStartIndex, sourceEndIndex - sourceStartIndex);
      for (var i = 0; i < vals.length; i++) {
        this.$items.splice(destinationIndex + i, 0, vals[i]);
      }
      var smallestChangedIndex = sourceStartIndex < destinationIndex ? sourceStartIndex : destinationIndex;
      for (var _i10 = smallestChangedIndex; _i10 < this.$items.length; _i10++) {
        this.$items[_i10].index = _i10;
      }
    }
  }, {
    key: "$_onRowsRemoved",
    value: function $_onRowsRemoved(startIndex, endIndex) {
      this.$removeChildren(startIndex, endIndex);
      for (var i = startIndex; i < this.$items.length; i++) {
        this.$items[i].index = i;
      }
      this.count = this.$items.length;
    }
  }, {
    key: "$_onModelReset",
    value: function $_onModelReset() {
      this.$applyModel();
    }
  }, {
    key: "$insertChildren",
    value: function $insertChildren(startIndex, endIndex) {
      if (endIndex <= 0) {
        this.count = 0;
        return;
      }

      var QMLOperationState = QmlWeb.QMLOperationState;
      var createProperty = QmlWeb.createProperty;
      var model = this.$getModel();
      var index = void 0;
      for (index = startIndex; index < endIndex; index++) {
        var newItem = this.delegate.$createObject();
        createProperty("int", newItem, "index", { initialValue: index });

        // To properly import JavaScript in the context of a component
        this.delegate.finalizeImports();

        if (typeof model === "number" || model instanceof Array) {
          if (typeof newItem.$properties.modelData === "undefined") {
            createProperty("variant", newItem, "modelData");
          }
          var value = model instanceof Array ? model[index] : typeof model === "number" ? index : "undefined";
          newItem.$properties.modelData.set(value, QmlWeb.QMLProperty.ReasonInit, newItem, model.$context);
        } else {
          for (var i = 0; i < model.roleNames.length; i++) {
            var roleName = model.roleNames[i];
            if (typeof newItem.$properties[roleName] === "undefined") {
              createProperty("variant", newItem, roleName);
            }
            newItem.$properties[roleName].set(model.data(index, roleName), QmlWeb.QMLProperty.ReasonInit, newItem, this.model.$context);
          }
        }

        this.$items.splice(index, 0, newItem);

        // parent must be set after the roles have been added to newItem scope in
        // case we are outside of QMLOperationState.Init and parentChanged has
        // any side effects that result in those roleNames being referenced.
        newItem.parent = this.parent;

        // TODO debug this. Without check to Init, Completed sometimes called
        // twice.. But is this check correct?
        if (QmlWeb.engine.operationState !== QMLOperationState.Init && QmlWeb.engine.operationState !== QMLOperationState.Idle) {
          // We don't call those on first creation, as they will be called
          // by the regular creation-procedures at the right time.
          this.$callOnCompleted(newItem);
        }
      }
      if (QmlWeb.engine.operationState !== QMLOperationState.Init) {
        // We don't call those on first creation, as they will be called
        // by the regular creation-procedures at the right time.
        QmlWeb.engine.$initializePropertyBindings();
      }

      if (index > 0) {
        this.container().childrenChanged();
      }

      for (var _i11 = endIndex; _i11 < this.$items.length; _i11++) {
        this.$items[_i11].index = _i11;
      }

      this.count = this.$items.length;
    }
  }, {
    key: "$removeChildren",
    value: function $removeChildren(startIndex, endIndex) {
      var removed = this.$items.splice(startIndex, endIndex - startIndex);
      for (var index in removed) {
        removed[index].$delete();
        this.$removeChildProperties(removed[index]);
      }
    }
  }, {
    key: "$removeChildProperties",
    value: function $removeChildProperties(child) {
      var signals = QmlWeb.engine.completedSignals;
      signals.splice(signals.indexOf(child.Component.completed), 1);
      for (var i = 0; i < child.children.length; i++) {
        this.$removeChildProperties(child.children[i]);
      }
    }
  }]);

  return _class56;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Rotation",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    angle: "real"
  }
}, function () {
  function _class57(meta) {
    _classCallCheck(this, _class57);

    QmlWeb.callSuper(this, meta);

    var createProperty = QmlWeb.createProperty;

    this.axis = new QmlWeb.QObject(this);
    createProperty("real", this.axis, "x");
    createProperty("real", this.axis, "y");
    createProperty("real", this.axis, "z", { initialValue: 1 });

    this.origin = new QmlWeb.QObject(this);
    createProperty("real", this.origin, "x");
    createProperty("real", this.origin, "y");

    this.angleChanged.connect(this.$parent, this.$parent.$updateTransform);
    this.axis.xChanged.connect(this.$parent, this.$parent.$updateTransform);
    this.axis.yChanged.connect(this.$parent, this.$parent.$updateTransform);
    this.axis.zChanged.connect(this.$parent, this.$parent.$updateTransform);
    this.origin.xChanged.connect(this, this.$updateOrigin);
    this.origin.yChanged.connect(this, this.$updateOrigin);
    this.$parent.$updateTransform();
  }

  _createClass(_class57, [{
    key: "$updateOrigin",
    value: function $updateOrigin() {
      var style = this.$parent.dom.style;
      style.transformOrigin = this.origin.x + "px " + this.origin.y + "px";
      style.webkitTransformOrigin = this.origin.x + "px " + this.origin.y + "px";
    }
  }]);

  return _class57;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Row",
  versions: /.*/,
  baseClass: "Positioner",
  properties: {
    layoutDirection: "enum"
  }
}, function () {
  function _class58(meta) {
    _classCallCheck(this, _class58);

    QmlWeb.callSuper(this, meta);

    this.layoutDirectionChanged.connect(this, this.layoutChildren);
    this.layoutChildren();
  }

  _createClass(_class58, [{
    key: "layoutChildren",
    value: function layoutChildren() {
      var curPos = 0;
      var maxHeight = 0;
      // When layoutDirection is RightToLeft we need oposite order
      var i = this.layoutDirection === 1 ? this.children.length - 1 : 0;
      var endPoint = this.layoutDirection === 1 ? -1 : this.children.length;
      var step = this.layoutDirection === 1 ? -1 : 1;
      for (; i !== endPoint; i += step) {
        var child = this.children[i];
        if (!(child.visible && child.width && child.height)) {
          continue;
        }
        maxHeight = child.height > maxHeight ? child.height : maxHeight;

        child.x = curPos;
        curPos += child.width + this.spacing;
      }
      this.implicitHeight = maxHeight;
      // We want no spacing at the right side
      this.implicitWidth = curPos - this.spacing;
    }
  }]);

  return _class58;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Scale",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    xScale: "real",
    yScale: "real"
  }
}, function () {
  function _class59(meta) {
    _classCallCheck(this, _class59);

    QmlWeb.callSuper(this, meta);

    var createProperty = QmlWeb.createProperty;
    this.origin = new QmlWeb.QObject(this);
    createProperty("real", this.origin, "x");
    createProperty("real", this.origin, "y");

    this.xScaleChanged.connect(this.$parent, this.$parent.$updateTransform);
    this.yScaleChanged.connect(this.$parent, this.$parent.$updateTransform);
    this.origin.xChanged.connect(this, this.$updateOrigin);
    this.origin.yChanged.connect(this, this.$updateOrigin);

    /* QML default origin is top-left, while CSS default origin is centre, so
     * $updateOrigin must be called to set the initial transformOrigin. */
    this.$updateOrigin();
  }

  _createClass(_class59, [{
    key: "$updateOrigin",
    value: function $updateOrigin() {
      var style = this.$parent.dom.style;
      style.transformOrigin = this.origin.x + "px " + this.origin.y + "px";
      style.webkitTransformOrigin = this.origin.x + "px " + this.origin.y + "px";
    }
  }]);

  return _class59;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "SequentialAnimation",
  versions: /.*/,
  baseClass: "Animation",
  properties: {
    animations: "list"
  },
  defaultProperty: "animations"
}, function () {
  function _class60(meta) {
    var _this41 = this;

    _classCallCheck(this, _class60);

    QmlWeb.callSuper(this, meta);

    this.animationsChanged.connect(this, this.$onAnimatonsChanged);

    QmlWeb.engine.$registerStart(function () {
      if (!_this41.running) return;
      _this41.running = false; // toggled back by start();
      _this41.start();
    });
    QmlWeb.engine.$registerStop(function () {
      return self.stop();
    });
  }

  _createClass(_class60, [{
    key: "$onAnimatonsChanged",
    value: function $onAnimatonsChanged() {
      var flags = QmlWeb.Signal.UniqueConnection;
      for (var i = 0; i < this.animations.length; i++) {
        var animation = this.animations[i];
        animation.runningChanged.connect(this, this.$nextAnimation, flags);
      }
    }
  }, {
    key: "$nextAnimation",
    value: function $nextAnimation(proceed) {
      if (this.running && !proceed) {
        this.$curIndex++;
        if (this.$curIndex < this.animations.length) {
          var anim = this.animations[this.$curIndex];
          console.log("nextAnimation", this, this.$curIndex, anim);
          anim.start();
        } else {
          this.$passedLoops++;
          if (this.$passedLoops >= this.loops) {
            this.complete();
          } else {
            this.$curIndex = -1;
            this.$nextAnimation();
          }
        }
      }
    }
  }, {
    key: "start",
    value: function start() {
      if (this.running) return;
      this.running = true;
      this.$curIndex = -1;
      this.$passedLoops = 0;
      this.$nextAnimation();
    }
  }, {
    key: "stop",
    value: function stop() {
      if (!this.running) return;
      this.running = false;
      if (this.$curIndex < this.animations.length) {
        this.animations[this.$curIndex].stop();
      }
    }
  }, {
    key: "complete",
    value: function complete() {
      if (!this.running) return;
      if (this.$curIndex < this.animations.length) {
        // Stop current animation
        this.animations[this.$curIndex].stop();
      }
      this.running = false;
    }
  }]);

  return _class60;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "State",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    name: "string",
    changes: "list",
    extend: "string",
    when: "bool"
  },
  defaultProperty: "changes"
}, function () {
  function _class61(meta) {
    _classCallCheck(this, _class61);

    QmlWeb.callSuper(this, meta);

    this.$item = this.$parent;

    this.whenChanged.connect(this, this.$onWhenChanged);
  }

  _createClass(_class61, [{
    key: "$getAllChanges",
    value: function $getAllChanges() {
      var _this42 = this;

      if (this.extend) {
        /* ECMAScript 2015. TODO: polyfill Array?
        const base = this.$item.states.find(state => state.name === this.extend);
        */
        var states = this.$item.states;
        var base = states.filter(function (state) {
          return state.name === _this42.extend;
        })[0];
        if (base) {
          return base.$getAllChanges().concat(this.changes);
        }
        console.error("Can't find the state to extend!");
      }
      return this.changes;
    }
  }, {
    key: "$onWhenChanged",
    value: function $onWhenChanged(newVal) {
      if (newVal) {
        this.$item.state = this.name;
      } else if (this.$item.state === this.name) {
        this.$item.state = "";
      }
    }
  }]);

  return _class61;
}());

var platformsDetectors = [
//{ name: "W8", regexp: /Windows NT 6\.2/ },
//{ name: "W7", regexp: /Windows NT 6\.1/ },
//{ name: "Windows", regexp: /Windows NT/ },
{ name: "OSX", regexp: /Macintosh/ }];

var systemPalettes = {};

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "SystemPalette",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  enums: {
    SystemPalette: {
      Active: "active", Inactive: "inactive", Disabled: "disabled"
    }
  },
  properties: {
    alternateBase: { type: "color", readOnly: true },
    base: { type: "color", readOnly: true },
    button: { type: "color", readOnly: true },
    buttonText: { type: "color", readOnly: true },
    dark: { type: "color", readOnly: true },
    highlight: { type: "color", readOnly: true },
    highlightedText: { type: "color", readOnly: true },
    light: { type: "color", readOnly: true },
    mid: { type: "color", readOnly: true },
    midlight: { type: "color", readOnly: true },
    shadow: { type: "color", readOnly: true },
    text: { type: "color", readOnly: true },
    window: { type: "color", readOnly: true },
    windowText: { type: "color", readOnly: true },

    colorGroup: "enum"
  }
}, function () {
  function _class62(meta) {
    _classCallCheck(this, _class62);

    QmlWeb.callSuper(this, meta);

    this.colorGroupChanged.connect(this, this.$onColorGroupChanged);

    this.$platform = "OSX";
    // Detect OS
    for (var i = 0; i < platformsDetectors.length; ++i) {
      if (platformsDetectors[i].regexp.test(navigator.userAgent)) {
        this.$platform = platformsDetectors[i].name;
        break;
      }
    }
  }

  _createClass(_class62, [{
    key: "$onColorGroupChanged",
    value: function $onColorGroupChanged(newVal) {
      var _this43 = this;

      var pallete = systemPalettes[this.$platform][newVal];
      this.$canEditReadOnlyProperties = true;
      Object.keys(pallete).forEach(function (key) {
        _this43[key] = pallete[key];
      });
      delete this.$canEditReadOnlyProperties;
    }
  }]);

  return _class62;
}());

systemPalettes.OSX = {
  active: {
    alternateBase: "#f6f6f6",
    base: "#ffffff",
    button: "#ededed",
    buttonText: "#000000",
    dark: "#bfbfbf",
    highlight: "#fbed73",
    highlightText: "#000000",
    light: "#ffffff",
    mid: "#a9a9a9",
    midlight: "#f6f6f6",
    shadow: "#8b8b8b",
    text: "#000000",
    window: "#ededed",
    windowText: "#000000"
  },
  inactive: {
    alternateBase: "#f6f6f6",
    base: "#ffffff",
    button: "#ededed",
    buttonText: "#000000",
    dark: "#bfbfbf",
    highlight: "#d0d0d0",
    highlightText: "#000000",
    light: "#ffffff",
    mid: "#a9a9a9",
    midlight: "#f6f6f6",
    shadow: "#8b8b8b",
    text: "#000000",
    window: "#ededed",
    windowText: "#000000"
  },
  disabled: {
    alternateBase: "#f6f6f6",
    base: "#ededed",
    button: "#ededed",
    buttonText: "#949494",
    dark: "#bfbfbf",
    highlight: "#d0d0d0",
    highlightText: "#7f7f7f",
    light: "#ffffff",
    mid: "#a9a9a9",
    midlight: "#f6f6f6",
    shadow: "#8b8b8b",
    text: "#7f7f7f",
    window: "#ededed",
    windowText: "#7f7f7f"
  }
};

QmlWeb.systemPalettes = systemPalettes;
QmlWeb.platformsDetectors = platformsDetectors;

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Text",
  versions: /.*/,
  baseClass: "Item",
  enums: {
    Text: {
      NoWrap: 0, WordWrap: 1, WrapAnywhere: 2, Wrap: 3,
      WrapAtWordBoundaryOrAnywhere: 4,
      AlignLeft: 1, AlignRight: 2, AlignHCenter: 4, AlignJustify: 8,
      AlignTop: 32, AlignBottom: 64, AlignVCenter: 128,
      Normal: 0, Outline: 1, Raised: 2, Sunken: 3
    }
  },
  properties: {
    color: { type: "color", initialValue: "black" },
    text: "string",
    lineHeight: "real",
    wrapMode: { type: "enum", initialValue: 0 }, // Text.NoWrap
    horizontalAlignment: { type: "enum", initialValue: 1 }, // Text.AlignLeft
    style: "enum",
    styleColor: "color"
  }
}, function () {
  function _class63(meta) {
    _classCallCheck(this, _class63);

    QmlWeb.callSuper(this, meta);

    var fc = this.impl = document.createElement("span");
    fc.style.pointerEvents = "none";
    fc.style.width = "100%";
    fc.style.height = "100%";
    fc.style.whiteSpace = "pre";
    this.dom.style.textAlign = "left";
    this.dom.appendChild(fc);

    var QMLFont = QmlWeb.getConstructor("QtQuick", "2.0", "Font");
    this.font = new QMLFont(this);

    this.colorChanged.connect(this, this.$onColorChanged);
    this.textChanged.connect(this, this.$onTextChanged);
    this.lineHeightChanged.connect(this, this.$onLineHeightChanged);
    this.wrapModeChanged.connect(this, this.$onWrapModeChanged);
    this.horizontalAlignmentChanged.connect(this, this.$onHorizontalAlignmentChanged);
    this.styleChanged.connect(this, this.$onStyleChanged);
    this.styleColorChanged.connect(this, this.$onStyleColorChanged);

    this.font.family = "sans-serif";
    this.font.pointSize = 10;

    this.widthChanged.connect(this, this.$onWidthChanged);

    this.font.boldChanged.connect(this, this.$onFontChanged);
    this.font.weightChanged.connect(this, this.$onFontChanged);
    this.font.pixelSizeChanged.connect(this, this.$onFontChanged);
    this.font.pointSizeChanged.connect(this, this.$onFontChanged);
    this.font.familyChanged.connect(this, this.$onFontChanged);
    this.font.letterSpacingChanged.connect(this, this.$onFontChanged);
    this.font.wordSpacingChanged.connect(this, this.$onFontChanged);

    this.Component.completed.connect(this, this.Component$onCompleted);
  }

  _createClass(_class63, [{
    key: "$onColorChanged",
    value: function $onColorChanged(newVal) {
      this.impl.style.color = new QmlWeb.QColor(newVal);
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged(newVal) {
      this.impl.innerHTML = newVal;
      this.$updateImplicit();
    }
  }, {
    key: "$onWidthChanged",
    value: function $onWidthChanged() {
      this.$updateImplicit();
    }
  }, {
    key: "$onLineHeightChanged",
    value: function $onLineHeightChanged(newVal) {
      this.impl.style.lineHeight = newVal + "px";
      this.$updateImplicit();
    }
  }, {
    key: "$onStyleChanged",
    value: function $onStyleChanged(newVal) {
      this.$updateShadow(newVal, this.styleColor);
    }
  }, {
    key: "$onStyleColorChanged",
    value: function $onStyleColorChanged(newVal) {
      this.$updateShadow(this.style, new QmlWeb.QColor(newVal));
    }
  }, {
    key: "$onWrapModeChanged",
    value: function $onWrapModeChanged(newVal) {
      var style = this.impl.style;
      switch (newVal) {
        case this.Text.NoWrap:
          style.whiteSpace = "pre";
          break;
        case this.Text.WordWrap:
          style.whiteSpace = "pre-wrap";
          style.wordWrap = "normal";
          break;
        case this.Text.WrapAnywhere:
          style.whiteSpace = "pre-wrap";
          style.wordBreak = "break-all";
          break;
        case this.Text.Wrap:
        case this.Text.WrapAtWordBoundaryOrAnywhere:
          style.whiteSpace = "pre-wrap";
          style.wordWrap = "break-word";
      }
      this.$updateJustifyWhiteSpace();
    }
  }, {
    key: "$onHorizontalAlignmentChanged",
    value: function $onHorizontalAlignmentChanged(newVal) {
      var textAlign = null;
      switch (newVal) {
        case this.Text.AlignLeft:
          textAlign = "left";
          break;
        case this.Text.AlignRight:
          textAlign = "right";
          break;
        case this.Text.AlignHCenter:
          textAlign = "center";
          break;
        case this.Text.AlignJustify:
          textAlign = "justify";
          break;
      }
      this.dom.style.textAlign = textAlign;
      this.$updateJustifyWhiteSpace();
    }
  }, {
    key: "$onFontChanged",
    value: function $onFontChanged() {
      this.$updateImplicit();
    }
  }, {
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.$updateImplicit();
    }
  }, {
    key: "$updateImplicit",
    value: function $updateImplicit() {
      if (!this.text || !this.dom) {
        this.implicitHeight = this.implicitWidth = 0;
        return;
      }

      if (!this.$isUsingImplicitWidth) {
        this.implicitWidth = this.impl.offsetWidth;
        this.implicitHeight = this.impl.offsetHeight;
        return;
      }

      var fc = this.impl;
      var engine = QmlWeb.engine;
      // Need to move the child out of it's parent so that it can properly
      // recalculate it's "natural" offsetWidth/offsetHeight
      if (engine.dom === document.body && engine.dom !== engine.domTarget) {
        // Can't use document.body here, as it could have Shadow DOM inside
        // The root is document.body, though, so it's probably not hidden
        engine.domTarget.appendChild(fc);
      } else {
        document.body.appendChild(fc);
      }
      var height = fc.offsetHeight;
      var width = fc.offsetWidth;
      this.dom.appendChild(fc);

      this.implicitHeight = height;
      this.implicitWidth = width;
    }
  }, {
    key: "$updateShadow",
    value: function $updateShadow(textStyle, styleColor) {
      var style = this.impl.style;
      switch (textStyle) {
        case 0:
          style.textShadow = "none";
          break;
        case 1:
          style.textShadow = ["1px 0 0 " + styleColor, "-1px 0 0 " + styleColor, "0 1px 0 " + styleColor, "0 -1px 0 " + styleColor].join(",");
          break;
        case 2:
          style.textShadow = "1px 1px 0 " + styleColor;
          break;
        case 3:
          style.textShadow = "-1px -1px 0 " + styleColor;
          break;
      }
    }
  }, {
    key: "$updateJustifyWhiteSpace",
    value: function $updateJustifyWhiteSpace() {
      var style = this.impl.style;
      // AlignJustify doesn't work with pre/pre-wrap, so we decide the lesser of
      // the two evils to be ignoring "\n"s inside the text.
      if (this.horizontalAlignment === this.Text.AlignJustify) {
        style.whiteSpace = "normal";
      }
      this.$updateImplicit();
    }
  }]);

  return _class63;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "TextEdit",
  versions: /.*/,
  baseClass: "Item",
  properties: {
    activeFocusOnPress: { type: "bool", initialValue: true },
    baseUrl: "url",
    canPaste: "bool",
    canRedo: "bool",
    canUndo: "bool",
    color: { type: "color", initialValue: "white" },
    contentHeight: "real",
    contentWidth: "real",
    cursorDelegate: "Component",
    cursorPosition: "int",
    cursorRectangle: "rectangle",
    cursorVisible: { type: "bool", initialValue: true },
    effectiveHorizontalAlignment: "enum",
    horizontalAlignment: "enum",
    hoveredLink: "string",
    inputMethodComposing: "bool",
    inputMethodHints: "enum",
    length: "int",
    lineCount: "int",
    mouseSelectionMode: "enum",
    persistentSelection: "bool",
    readOnly: "bool",
    renderType: "enum",
    selectByKeyboard: { type: "bool", initialValue: true },
    selectByMouse: "bool",
    selectedText: "string",
    selectedTextColor: { type: "color", initialValue: "yellow" },
    selectionColor: { type: "color", initialValue: "pink" },
    selectionEnd: "int",
    selectionStart: "int",
    text: "string",
    textDocument: "TextDocument",
    textFormat: "enum",
    textMargin: "real",
    verticalAlignment: "enum",
    wrapMode: "enum"
  },
  signals: {
    linkActivated: [{ type: "string", name: "link" }],
    linkHovered: [{ type: "string", name: "link" }]
  }
}, function () {
  function _class64(meta) {
    var _this44 = this;

    _classCallCheck(this, _class64);

    QmlWeb.callSuper(this, meta);

    var QMLFont = QmlWeb.getConstructor("QtQuick", "2.0", "Font");
    this.font = new QMLFont(this);

    // Undo / Redo stacks;
    this.undoStack = [];
    this.undoStackPosition = -1;
    this.redoStack = [];
    this.redoStackPosition = -1;

    var textarea = this.impl = document.createElement("textarea");
    textarea.style.pointerEvents = "auto";
    textarea.style.width = "100%";
    textarea.style.height = "100%";
    textarea.style.boxSizing = "border-box";
    textarea.style.borderWidth = "0";
    textarea.style.background = "none";
    textarea.style.outline = "none";
    textarea.style.resize = "none";
    textarea.style.padding = "0"; // TODO: padding/*Padding props from Qt 5.6
    // In some browsers text-areas have a margin by default, which distorts
    // the positioning, so we need to manually set it to 0.
    textarea.style.margin = "0";
    textarea.disabled = false;
    this.dom.appendChild(textarea);

    this.Component.completed.connect(this, this.Component$onCompleted);
    this.textChanged.connect(this, this.$onTextChanged);
    this.colorChanged.connect(this, this.$onColorChanged);

    this.impl.addEventListener("input", function () {
      return _this44.$updateValue();
    });
  }

  _createClass(_class64, [{
    key: "append",
    value: function append(text) {
      this.text += text;
    }
  }, {
    key: "copy",
    value: function copy() {
      // TODO
    }
  }, {
    key: "cut",
    value: function cut() {
      this.text = this.text(0, this.selectionStart) + this.text(this.selectionEnd, this.text.length);
      // TODO
    }
  }, {
    key: "deselect",
    value: function deselect() {
      //this.selectionStart = -1;
      //this.selectionEnd = -1;
      //this.selectedText = null;
      // TODO
    }
  }, {
    key: "getFormattedText",
    value: function getFormattedText(start, end) {
      var text = this.text.slice(start, end);
      // TODO
      // process text
      return text;
    }
  }, {
    key: "getText",
    value: function getText(start, end) {
      return this.text.slice(start, end);
    }
  }, {
    key: "insert",
    value: function insert() /*position, text*/{
      // TODO
    }
  }, {
    key: "isRightToLeft",
    value: function isRightToLeft() /*start, end*/{
      // TODO
    }
  }, {
    key: "linkAt",
    value: function linkAt() /*x, y*/{
      // TODO
    }
  }, {
    key: "moveCursorSelection",
    value: function moveCursorSelection() /*x, y*/{
      // TODO
    }
  }, {
    key: "paste",
    value: function paste() {
      // TODO
    }
  }, {
    key: "positionAt",
    value: function positionAt() /*x, y*/{
      // TODO
    }
  }, {
    key: "positionToRectangle",
    value: function positionToRectangle() /*position*/{
      // TODO
    }
  }, {
    key: "redo",
    value: function redo() {
      // TODO
    }
  }, {
    key: "remove",
    value: function remove() /*start, end*/{
      // TODO
    }
  }, {
    key: "select",
    value: function select() /*start, end*/{
      // TODO
    }
  }, {
    key: "selectAll",
    value: function selectAll() {
      // TODO
    }
  }, {
    key: "selectWord",
    value: function selectWord() {
      // TODO
    }
  }, {
    key: "undo",
    value: function undo() {
      // TODO
    }
  }, {
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.selectByKeyboard = !this.readOnly;
      this.$updateValue();
      this.implicitWidth = this.offsetWidth;
      this.implicitHeight = this.offsetHeight;
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged(newVal) {
      this.impl.value = newVal;
    }
  }, {
    key: "$onColorChanged",
    value: function $onColorChanged(newVal) {
      this.impl.style.color = newVal;
    }
  }, {
    key: "$updateValue",
    value: function $updateValue() {
      if (this.text !== this.impl.value) {
        this.text = this.impl.value;
      }
      this.length = this.text.length;
      this.lineCount = this.$getLineCount();
      this.$updateCss();
    }
    // Transfer dom style to firstChild,
    // then clear corresponding dom style

  }, {
    key: "$updateCss",
    value: function $updateCss() {
      var supported = ["border", "borderRadius", "borderWidth", "borderColor", "backgroundColor"];
      var style = this.impl.style;
      for (var n = 0; n < supported.length; n++) {
        var o = supported[n];
        var v = this.css[o];
        if (v) {
          style[o] = v;
          this.css[o] = null;
        }
      }
    }
  }, {
    key: "$getLineCount",
    value: function $getLineCount() {
      return this.text.split(/\n/).length;
    }
  }]);

  return _class64;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "TextInput",
  versions: /.*/,
  baseClass: "Item",
  enums: {
    TextInput: { Normal: 0, Password: 1, NoEcho: 2, PasswordEchoOnEdit: 3 }
  },
  properties: {
    text: "string",
    maximumLength: { type: "int", initialValue: -1 },
    readOnly: "bool",
    validator: "var",
    echoMode: "enum" // TextInput.Normal
  },
  signals: {
    accepted: []
  }
}, function () {
  function _class65(meta) {
    var _this45 = this;

    _classCallCheck(this, _class65);

    QmlWeb.callSuper(this, meta);

    var QMLFont = QmlWeb.getConstructor("QtQuick", "2.0", "Font");
    this.font = new QMLFont(this);

    var input = this.impl = document.createElement("input");
    input.type = "text";
    input.disabled = true;
    input.style.pointerEvents = "auto";
    // In some browsers text-inputs have a margin by default, which distorts
    // the positioning, so we need to manually set it to 0.
    input.style.margin = "0";
    input.style.padding = "0";
    input.style.width = "100%";
    input.style.height = "100%";
    this.dom.appendChild(input);
    this.setupFocusOnDom(input);
    input.disabled = false;

    this.Component.completed.connect(this, this.Component$onCompleted);
    this.textChanged.connect(this, this.$onTextChanged);
    this.echoModeChanged.connect(this, this.$onEchoModeChanged);
    this.maximumLengthChanged.connect(this, this.$onMaximumLengthChanged);
    this.readOnlyChanged.connect(this, this.$onReadOnlyChanged);
    this.Keys.pressed.connect(this, this.Keys$onPressed);

    this.impl.addEventListener("input", function () {
      return _this45.$updateValue();
    });
  }

  _createClass(_class65, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.implicitWidth = this.impl.offsetWidth;
      this.implicitHeight = this.impl.offsetHeight;
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged(newVal) {
      // We have to check if value actually changes.
      // If we do not have this check, then after user updates text input
      // following occurs: user updates gui text -> updateValue gets called ->
      // textChanged gets called -> gui value updates again -> caret position
      // moves to the right!
      if (this.impl.value !== newVal) {
        this.impl.value = newVal;
      }
    }
  }, {
    key: "$onEchoModeChanged",
    value: function $onEchoModeChanged(newVal) {
      var TextInput = this.TextInput;
      var input = this.impl;
      switch (newVal) {
        case TextInput.Normal:
          input.type = "text";
          break;
        case TextInput.Password:
          input.type = "password";
          break;
        case TextInput.NoEcho:
          // Not supported, use password, that's nearest
          input.type = "password";
          break;
        case TextInput.PasswordEchoOnEdit:
          // Not supported, use password, that's nearest
          input.type = "password";
          break;
      }
    }
  }, {
    key: "$onMaximumLengthChanged",
    value: function $onMaximumLengthChanged(newVal) {
      this.impl.maxLength = newVal < 0 ? null : newVal;
    }
  }, {
    key: "$onReadOnlyChanged",
    value: function $onReadOnlyChanged(newVal) {
      this.impl.disabled = newVal;
    }
  }, {
    key: "Keys$onPressed",
    value: function Keys$onPressed(e) {
      var Qt = QmlWeb.Qt;
      var submit = e.key === Qt.Key_Return || e.key === Qt.Key_Enter;
      if (submit && this.$testValidator()) {
        this.accepted();
        e.accepted = true;
      }
    }
  }, {
    key: "$testValidator",
    value: function $testValidator() {
      if (this.validator) {
        return this.validator.validate(this.text);
      }
      return true;
    }
  }, {
    key: "$updateValue",
    value: function $updateValue() {
      if (this.text !== this.impl.value) {
        this.$canEditReadOnlyProperties = true;
        this.text = this.impl.value;
        this.$canEditReadOnlyProperties = false;
      }
    }
  }]);

  return _class65;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Transition",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    animations: "list",
    from: { type: "string", initialValue: "*" },
    to: { type: "string", initialValue: "*" },
    reversible: "bool"
  },
  defaultProperty: "animations"
}, function () {
  function _class66(meta) {
    _classCallCheck(this, _class66);

    QmlWeb.callSuper(this, meta);

    this.$item = this.$parent;
  }

  _createClass(_class66, [{
    key: "$start",
    value: function $start(actions) {
      for (var i = 0; i < this.animations.length; i++) {
        var animation = this.animations[i];
        animation.$actions = [];
        var $targets = animation.$targets,
            $props = animation.$props,
            $actions = animation.$actions;

        for (var j in actions) {
          var _action6 = actions[j];
          if (($targets.length === 0 || $targets.indexOf(_action6.target) !== -1) && ($props.length === 0 || $props.indexOf(_action6.property) !== -1)) {
            $actions.push(_action6);
          }
        }
        animation.start();
      }
    }
  }, {
    key: "$stop",
    value: function $stop() {
      for (var i = 0; i < this.animations.length; i++) {
        this.animations[i].stop();
      }
    }
  }]);

  return _class66;
}());

QmlWeb.registerQmlType({
  module: "QtQuick",
  name: "Translate",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    x: "real",
    y: "real"
  }
}, function () {
  function _class67(meta) {
    _classCallCheck(this, _class67);

    QmlWeb.callSuper(this, meta);

    this.xChanged.connect(this.$parent, this.$parent.$updateTransform);
    this.yChanged.connect(this.$parent, this.$parent.$updateTransform);
  }

  return _class67;
}());

// WARNING: Can have wrong behavior if url is changed while the socket is in
// Connecting state.
// TODO: Recheck everything.

QmlWeb.registerQmlType({
  module: "QtWebSockets",
  name: "WebSocket",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  enums: {
    WebSocket: { Connecting: 0, Open: 1, Closing: 2, Closed: 3, Error: 4 }
  },
  properties: {
    active: "bool",
    status: { type: "enum", initialValue: 3 }, // WebSocket.Closed
    errorString: "string",
    url: "url"
  },
  signals: {
    textMessageReceived: [{ type: "string", name: "message" }]
  }
}, function () {
  function _class68(meta) {
    _classCallCheck(this, _class68);

    QmlWeb.callSuper(this, meta);

    this.$socket = undefined;
    this.$reconnect = false;

    this.statusChanged.connect(this, this.$onStatusChanged);
    this.activeChanged.connect(this, this.$reconnectSocket);
    this.urlChanged.connect(this, this.$reconnectSocket);
  }

  _createClass(_class68, [{
    key: "$onStatusChanged",
    value: function $onStatusChanged(status) {
      if (status !== this.WebSocket.Error) {
        this.errorString = "";
      }
    }
  }, {
    key: "$connectSocket",
    value: function $connectSocket() {
      var _this46 = this;

      this.$reconnect = false;

      if (!this.url || !this.active) {
        return;
      }

      this.status = this.WebSocket.Connecting;
      this.$socket = new WebSocket(this.url);
      this.$socket.onopen = function () {
        _this46.status = _this46.WebSocket.Open;
      };
      this.$socket.onclose = function () {
        _this46.status = _this46.WebSocket.Closed;
        if (_this46.$reconnect) {
          _this46.$connectSocket();
        }
      };
      this.$socket.onerror = function (error) {
        _this46.errorString = error.message;
        _this46.status = _this46.WebSocket.Error;
      };
      this.$socket.onmessage = function (message) {
        _this46.textMessageReceived(message.data);
      };
    }
  }, {
    key: "$reconnectSocket",
    value: function $reconnectSocket() {
      this.$reconnect = true;
      if (this.status === this.WebSocket.Open) {
        this.status = this.WebSocket.Closing;
        this.$socket.close();
      } else if (this.status !== this.WebSocket.Closing) {
        this.$connectSocket();
      }
    }
  }, {
    key: "sendTextMessage",
    value: function sendTextMessage(message) {
      if (this.status === this.WebSocket.Open) {
        this.$socket.send(message);
      }
    }
  }]);

  return _class68;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Accordion",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    expanded: "bool"
  },
  signals: {
    open: [{ type: "int", name: "index" }],
    opening: [{ type: "int", name: "index" }],
    change: [{ type: "int", name: "index" }],
    close: [{ type: "int", name: "index" }],
    closing: [{ type: "int", name: "index" }]
  }
}, function () {
  function _class69(meta) {
    _classCallCheck(this, _class69);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.expandedChanged.connect(this, this.$onExpandedChanged);
    this.baseClassName = "ui accordion";
    this.dom.style.position = "relative";
    this.$accordion = $(this.dom).accordion({
      onOpen: this.onOpen.bind(this),
      onOpening: this.onOpening.bind(this),
      onChange: this.onChange.bind(this),
      onClose: this.onClose.bind(this),
      onClosing: this.onClosing.bind(this)
    });
  }

  _createClass(_class69, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {}
  }, {
    key: "$onExpandedChanged",
    value: function $onExpandedChanged() {
      var _this47 = this;

      $(document).ready(function () {
        if (_this47.expanded) {
          _this47.$accordion.accordion('open', 0);
        } else {
          _this47.$accordion.accordion('close', 0);
        }
      });
    }

    //by default when we wanna call some method on accordion
    //we have to get the accordions by jquery like $('.ui.accordion')
    //above will get all accordions object
    //to open the first accordion in page: $('.ui.accordion').accordion('open', 0)
    //but if we want to reduce the scope to our dom
    //we have to get an accordion by $(this.dom)
    //and the accordion object will only has 1 children
    //so we can open it by $(this.dom).accordion('open', 0)

  }, {
    key: "expand",
    value: function expand() {
      this.$accordion.accordion('open', 0);
    }
  }, {
    key: "collapse",
    value: function collapse() {
      this.$accordion.accordion('close', 0);
    }
  }, {
    key: "toggle",
    value: function toggle() {
      this.$accordion.accordion('toggle', 0);
    }
  }, {
    key: "onOpen",
    value: function onOpen() {
      this.open(this.$accordion.index());
      //work around for fixing dgrid style
      document.body.dispatchEvent(new CustomEvent("resizeDgrid", {
        detail: {
          dom: this.dom
        }
      }));
    }
  }, {
    key: "onOpening",
    value: function onOpening() {
      this.opening(this.$accordion.index());
    }
  }, {
    key: "onChange",
    value: function onChange() {
      this.change(this.$accordion.index());
    }
  }, {
    key: "onClose",
    value: function onClose() {
      this.close(this.$accordion.index());
    }
  }, {
    key: "onClosing",
    value: function onClosing() {
      this.closing(this.$accordion.index());
    }
  }]);

  return _class69;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "AccordionContent",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {}
}, function () {
  function _class70(meta) {
    _classCallCheck(this, _class70);

    QmlWeb.callSuper(this, meta);
    this.baseClassName = "content";
  }

  return _class70;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "AccordionItem",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {}
}, function () {
  function _class71(meta) {
    _classCallCheck(this, _class71);

    QmlWeb.callSuper(this, meta);
    this.baseClassName = "item";
  }

  return _class71;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "AccordionTitle",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    text: "string"
  }
}, function () {
  function _class72(meta) {
    _classCallCheck(this, _class72);

    QmlWeb.callSuper(this, meta);
    this.textChanged.connect(this, this.$onTextChanged);
    this.baseClassName = "title";
  }

  _createClass(_class72, [{
    key: "$onTextChanged",
    value: function $onTextChanged() {
      var iconNode = void 0,
          placeholderNode = document.createElement("div");
      this.children.forEach(function (child) {
        return placeholderNode.appendChild(iconNode = child.dom);
      });
      this.dom.innerHTML = "";
      iconNode && this.dom.appendChild(iconNode);
      this.dom.appendChild(document.createTextNode(this.text));
    }
  }]);

  return _class72;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Agenda",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    events: { type: "var", initialValue: [] },
    views: { type: "var", initialValue: ["month", "agendaWeek", "agendaDay", "listMonth"] },
    selectedView: { type: "string", initialValue: "" },
    size: { type: "int", initialValue: 550 },
    newEvent: "var"
  },
  signals: {
    rendered: []
  }
}, function () {
  function _class73(meta) {
    var _this48 = this;

    _classCallCheck(this, _class73);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.selectedViewChanged.connect(this, this.$onSelectedViewChanged);
    this.eventsChanged.connect(this, this.$onEventsChanged);
    this.timePattern = /^([0-1][0-9]|[2][0-3]):([0-5][0-9])$/;
    this.datePattern = /^\d{1,2}\/\d{1,2}\/\d{4}$/;
    this.$dom = $("\n            <div>\n                <div data-main=\"fullcalendar\" style=\"margin:auto\"></div>\n                <div class=\"ui mini modal\" data-action=\"info\">\n                    <div class=\"header\">\n                        <h3>\u0E19\u0E31\u0E14\u0E2B\u0E21\u0E32\u0E22</h3>\n                    </div>\n                    <div class=\"content\">\n                        <div class=\"ui form\">\n                            <div class=\"inline field\">\n                                <label>\u0E40\u0E23\u0E34\u0E48\u0E21:</label>\n                                <div class=\"ui large blue label\">\n                                    <div class=\"detail\" data-info=\"start\"></div>\n                                </div>\n                            </div>\n                            <div class=\"inline field\">\n                                <label>\u0E16\u0E36\u0E07: </label>\n                                <div class=\"ui large orange label\">\n                                    <div class=\"detail\" data-info=\"end\"></div>\n                                </div>\n                            </div>\n                            <div class=\"ui horizontal divider\">\u0E23\u0E32\u0E22\u0E25\u0E30\u0E40\u0E2D\u0E35\u0E22\u0E14</div>\n                            <div class=\"field\">\n                                <p data-info=\"detail\">\u0E02\u0E49\u0E2D\u0E21\u0E39\u0E25</p>\n                            </div>\n                        </div>\n                    </div>\n                    <div class=\"actions\">\n                        <button class=\"ui small red button\" data-action=\"delete\">\u0E25\u0E1A</button>\n                    </div>\n                </div>\n                <div class=\"ui mini modal\" data-action=\"confirm\">\n                    <div class=\"header\">\n                        <h3>\u0E15\u0E49\u0E2D\u0E07\u0E01\u0E32\u0E23\u0E25\u0E1A\u0E19\u0E31\u0E14\u0E2B\u0E21\u0E32\u0E22\u0E19\u0E35\u0E49\u0E43\u0E0A\u0E48\u0E2B\u0E23\u0E37\u0E2D\u0E44\u0E21\u0E48</h3>\n                    </div>\n                    <div class=\"actions\">\n                        <button class=\"ui small green button\" data-action=\"yes\">\u0E43\u0E0A\u0E48</button>\n                        <button class=\"ui small red button\" data-action=\"no\">\u0E44\u0E21\u0E48</button>\n                    </div>\n                </div>\n            </div>\n        ");

    this.dom = this.$dom[0];
    this.$calendar = this.$dom.find('div[data-main=fullcalendar]');
    this.$infoModal = this.$dom.find('.ui.modal[data-action=info]');
    this.$confirmModal = this.$dom.find('.ui.modal[data-action=confirm]');
    this.$yesButton = this.$dom.find('.ui.button[data-action=yes]');
    this.$noButton = this.$dom.find('.ui.button[data-action=no]');
    this.$delButton = this.$dom.find('.ui.button[data-action=delete]');
    this.$startInfo = this.$infoModal.find('.content div[data-info=start]');
    this.$endInfo = this.$infoModal.find('.content div[data-info=end]');
    this.$detailInfo = this.$infoModal.find('.content p[data-info=detail]');

    this.$infoModal.modal({ dimmerSettings: { opacity: 0.5 }, duration: 270 });
    this.$confirmModal.modal({ dimmerSettings: { opacity: 0.5 }, duration: 270 });

    this.$yesButton.on('click', function () {
      var event = _this48.$infoModal.data("event");
      _this48.$calendar.fullCalendar('removeEvents', event._id);
      _this48.$confirmModal.modal('hide');
    });

    this.$noButton.on('click', function () {
      _this48.$confirmModal.modal('hide');
    });

    this.$delButton.on('click', function () {
      _this48.$confirmModal.modal('show');
    });

    this.setting = {};
    this.setting["locale"] = "th";
    this.setting["navLinks"] = true;
    this.setting["editable"] = true;
    this.setting["selectable"] = true;

    this.setting["header"] = {
      left: 'prevYear prev,next nextYear today',
      center: 'title'
    };

    this.setting["views"] = {
      month: {
        titleFormat: 'MMMM B'
      },
      agendaWeek: {
        allDaySlot: false,
        titleFormat: 'DD MMMM B',
        columnFormat: 'dd D',
        slotLabelFormat: 'H:mm'
      },
      agendaDay: {
        allDaySlot: false,
        slotLabelFormat: 'H:mm',
        titleFormat: 'DD MMMM B'
      }
    };

    //To allow or not allow select overlab
    this.setting["selectOverlap"] = function (event) {
      return !event.disabled;
    };

    //To allow or not allow drag or resize overlap
    this.setting["eventOverlap"] = function (stillEvent, movingEvent) {
      return !stillEvent.disabled;
    };

    this.setting["eventClick"] = function (calEvent, jsEvent, view) {
      var start = "-",
          end = "-";
      if (calEvent.start) start = calEvent.start.format('DD MMMM B HH:mm');
      if (calEvent.end) end = calEvent.end.format('DD MMMM B HH:mm');

      _this48.$startInfo.html(start);
      _this48.$endInfo.html(end);
      _this48.$detailInfo.html(calEvent.title);
      _this48.$infoModal.modal('show');
      _this48.$infoModal.data("event", calEvent);
    };

    this.setting["select"] = function (start, end) {
      var allow = void 0,
          shiftedEnd = start.clone(),
          calendar = _this48.$calendar.data('fullCalendar'),
          viewType = _this48.$calendar.fullCalendar("getView").type;

      if (!_this48.newEvent || viewType === "month") return;

      shiftedEnd.add(parseInt(_this48.newEvent.hour), 'hour');
      shiftedEnd.add(parseInt(_this48.newEvent.minute), 'minute');
      _this48.newEvent.start = start;
      _this48.newEvent.end = shiftedEnd;
      allow = calendar.isSelectionSpanAllowed({ start: start, end: shiftedEnd });

      if (allow) _this48.$calendar.fullCalendar('renderEvent', _this48.newEvent, true);else return;

      _this48.$calendar.fullCalendar('unselect');
      _this48.newEvent = null;
    };
    this.setting["eventAfterAllRender"] = this.onEventAfterAllRender.bind(this);
    this.setting["eventDestroy"] = this.onEventDestroy.bind(this);
  }

  _createClass(_class73, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.setting["events"] = this.getAgendarEvents();
      this.setting["header"]["right"] = this.views.join(',');
      this.setting["defaultView"] = this.selectedView ? this.selectedView : this.views[0];
      this.$calendar.width(parseInt(this.size));
      this.$calendar.fullCalendar(this.setting);
      this.completed = true;
    }
  }, {
    key: "$onSelectedViewChanged",
    value: function $onSelectedViewChanged() {
      if (this.completed) {
        this.$calendar.fullCalendar('changeView', selectedView);
      }
    }

    /* !!!!!!! DO NOT !!!!!!!!!!!! set the events to any rendered events   */

  }, {
    key: "$onEventsChanged",
    value: function $onEventsChanged() {
      if (this.bySystem || !this.events instanceof Array) {
        return;
      }
      if (this.completed) {
        var calEvents = this.getAgendarEvents.call({
          events: this.events.slice(),
          timePattern: this.timePattern,
          datePattern: this.datePattern
        });

        this.$calendar.fullCalendar("removeEvents");
        this.$calendar.fullCalendar("renderEvents", calEvents, true);
      }
    }
  }, {
    key: "onEventAfterAllRender",
    value: function onEventAfterAllRender(view) {
      //Change happens to event
      this.updateEventsObject();
      this.rendered();
    }
  }, {
    key: "onEventDestroy",
    value: function onEventDestroy(event, element, view) {
      //After event is destroy
      this.updateEventsObject();
    }
  }, {
    key: "updateEventsObject",
    value: function updateEventsObject() {
      this.bySystem = true;
      var events = this.$calendar.fullCalendar('clientEvents');
      events.forEach(function (item) {
        if (item.start) {
          item.startDate = item.start.format("DD/MM/B");
          item.startTime = item.start.format("HH:mm");
        }
        if (item.end) {
          item.endDate = item.end.format("DD/MM/B");
          item.endTime = item.end.format("HH:mm");
        }
      });
      this.events = events;
      this.bySystem = false;
    }
  }, {
    key: "getAgendarEvents",
    value: function getAgendarEvents() {
      var _this49 = this;

      this.events.forEach(function (item) {
        var startValid = void 0,
            endValid = void 0,
            start = void 0,
            end = void 0,
            day = void 0,
            month = void 0,
            year = void 0;
        startValid = _this49.datePattern.test(item.startDate);
        startValid = startValid && _this49.timePattern.test(item.startTime);
        endValid = _this49.datePattern.test(item.endDate);
        endValid = endValid && _this49.timePattern.test(item.endTime);

        if (startValid) {
          var _item$startDate$split = item.startDate.split("/");

          var _item$startDate$split2 = _slicedToArray(_item$startDate$split, 3);

          day = _item$startDate$split2[0];
          month = _item$startDate$split2[1];
          year = _item$startDate$split2[2];

          year = Math.max(0, Number(year) - 543);
          start = year + "-" + month + "-" + day + "T" + item.startTime + ":00";
        }

        if (endValid) {
          var _item$endDate$split = item.endDate.split("/");

          var _item$endDate$split2 = _slicedToArray(_item$endDate$split, 3);

          day = _item$endDate$split2[0];
          month = _item$endDate$split2[1];
          year = _item$endDate$split2[2];

          year = Math.max(0, Number(year) - 543);
          end = year + "-" + month + "-" + day + "T" + item.endTime + ":00";
        };

        delete item.startDate;
        delete item.startTime;
        delete item.endDate;
        delete item.endTime;

        item["start"] = start;
        item["end"] = end;
      });
      return this.events;
    }

    /* This method won't check if a new event overlap a disabled event or not   *
     * !!!!!!! DO NOT !!!!!!!!!!!! pass a rendered event                        */

  }, {
    key: "addEvent",
    value: function addEvent(event) {
      var calEvent = this.getAgendarEvents.call({
        events: [event],
        timePattern: this.timePattern,
        datePattern: this.datePattern
      })[0];

      this.$calendar.fullCalendar('renderEvent', calEvent, true);
    }

    /*  param: id            *
     *  get it by event._id  */

  }, {
    key: "removeEvent",
    value: function removeEvent(id) {
      id && this.$calendar.fullCalendar('removeEvents', id);
    }
  }, {
    key: "removeAllEvents",
    value: function removeAllEvents() {
      this.$calendar.fullCalendar('removeEvents');
    }

    // param: the rendered event that has an id

  }, {
    key: "updateEvent",
    value: function updateEvent(event) {
      event && this.$calendar.fullCalendar('updateEvent', event);
    }
  }, {
    key: "gotoDate",
    value: function gotoDate(date) {
      var day = void 0,
          month = void 0,
          year = void 0;
      if (!this.completed) return;
      if (this.datePattern.test(date)) {
        var _date$split = date.split("/");

        var _date$split2 = _slicedToArray(_date$split, 3);

        day = _date$split2[0];
        month = _date$split2[1];
        year = _date$split2[2];

        year = Math.max(0, Number(year) - 543);
        this.$calendar.fullCalendar('gotoDate', moment(year + "-" + month + "-" + day));
      }
    }
  }, {
    key: "refresh",
    value: function refresh() {
      this.$calendar.fullCalendar('render', event);
    }
  }]);

  return _class73;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Br",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    text: "string"
  }
}, function () {
  function _class74(meta) {
    _classCallCheck(this, _class74);

    meta.object.tagName = "br";
    QmlWeb.callSuper(this, meta);
  }

  return _class74;
}());
{

  var _BACKGROUNDCOLOR = ['red', 'orange', 'yellow', 'olive', 'green', 'teal', 'blue', 'violet', 'purple', 'pink', 'brown', 'grey', 'black'];

  // Button.size = [
  //     'mini', 
  //     'tiny', 
  //     'small', 
  //     'medium', 
  //     'large', 
  //     'big', 
  //     'huge', 
  //     'massive' 
  // ];


  QmlWeb.registerQmlType({
    module: "Semantic.Html",
    name: "Button",
    versions: /.*/,
    baseClass: "Semantic.Html.Dom",
    properties: {
      text: "string",
      backgroundColor: { type: "string", initialValue: "" },
      size: { type: "string", initialValue: "" },
      fluid: "bool",
      circular: "bool",
      basic: "bool",
      inverted: "bool",
      icon: "string",
      loading: "bool",
      active: "bool",
      enabled: { type: "bool", initialValue: true }
    },
    signals: {
      clicked: []
    }
  }, function () {
    function _class75(meta) {
      var _this50 = this;

      _classCallCheck(this, _class75);

      meta.object.tagName = "button";
      QmlWeb.callSuper(this, meta);
      this.backgroundColorChanged.connect(this, this.$onBackgroundColorChanged);
      this.sizeChanged.connect(this, this.$onSizeChanged);
      this.textChanged.connect(this, this.$onTextChanged);
      this.fluidChanged.connect(this, this.$onFluidChanged);
      this.circularChanged.connect(this, this.$onCircularChanged);
      this.enabledChanged.connect(this, this.$onEnabledChanged);
      this.loadingChanged.connect(this, this.$onLoadingChanged);
      this.basicChanged.connect(this, this.$onBasicChanged);
      this.invertedChanged.connect(this, this.$onInvertedChanged);
      this.iconChanged.connect(this, this.$onIconChanged);
      this.activeChanged.connect(this, this.$onActiveChanged);

      this._size = "medium";
      this.suffixClassName = "button";

      this.dom.onclick = function () {
        _this50.clicked();
      };
    }

    _createClass(_class75, [{
      key: "setIconAndText",
      value: function setIconAndText() {
        var icon = this.icon || "",
            text = this.text || "";

        this.dom.innerHTML = "";

        this.addClass("icon");
        this.iconNode = document.createElement("i");
        this.iconNode.className = icon + " icon";
        icon && this.dom.appendChild(this.iconNode);
        text && this.dom.appendChild(document.createTextNode(text));
      }
    }, {
      key: "$onTextChanged",
      value: function $onTextChanged() {
        this.setIconAndText();
      }
    }, {
      key: "$onBackgroundColorChanged",
      value: function $onBackgroundColorChanged() {
        this.dom.style.backgroundColor = "";
        this.removeClass(this._backgroundColor);
        if (_BACKGROUNDCOLOR.includes(this.backgroundColor)) {
          this.addClass(this.backgroundColor);
        } else {
          this.dom.style.backgroundColor = this.backgroundColor;
        }
        this._backgroundColor = this.backgroundColor;
      }
    }, {
      key: "$onSizeChanged",
      value: function $onSizeChanged() {
        this.removeClass(this._size);
        this.addClass(this.size);
        this._size = this.size;
      }
    }, {
      key: "$onFluidChanged",
      value: function $onFluidChanged() {
        this.addClass("fluid");
        if (!this.fluid) this.removeClass("fluid");
      }
    }, {
      key: "$onCircularChanged",
      value: function $onCircularChanged() {
        this.addClass("circular");
        if (!this.circular) this.removeClass("circular");
      }
    }, {
      key: "$onEnabledChanged",
      value: function $onEnabledChanged() {
        this.addClass("disabled");
        if (this.enabled) this.removeClass("disabled");
      }
    }, {
      key: "$onLoadingChanged",
      value: function $onLoadingChanged() {
        this.addClass("loading");
        if (!this.loading) this.removeClass("loading");
      }
    }, {
      key: "$onBasicChanged",
      value: function $onBasicChanged() {
        this.addClass("basic");
        if (!this.basic) this.removeClass("basic");
      }
    }, {
      key: "$onInvertedChanged",
      value: function $onInvertedChanged() {
        this.addClass("inverted");
        if (!this.inverted) this.removeClass("inverted");
      }
    }, {
      key: "$onIconChanged",
      value: function $onIconChanged() {
        this.setIconAndText();
      }
    }, {
      key: "$onActiveChanged",
      value: function $onActiveChanged() {
        this.addClass("active");
        if (!this.active) this.removeClass("active");
      }
    }]);

    return _class75;
  }());
}
{

  var ButtonGroup = function () {
    function ButtonGroup(meta) {
      _classCallCheck(this, ButtonGroup);

      QmlWeb.callSuper(this, meta);
      this.fluidChanged.connect(this, this.$onFluidChanged);
      this.verticalChanged.connect(this, this.$onVerticalChanged);
      this.sizeChanged.connect(this, this.$onSizeChanged);
      this.backgroundColorChanged.connect(this, this.$onBackgroundColorChanged);
      this.basicChanged.connect(this, this.$onBasicChanged);
      this.equalWidthChanged.connect(this, this.$onEqualwidthChanged);

      this.suffixClassName = "buttons";
    }

    _createClass(ButtonGroup, [{
      key: "validateProperty",
      value: function validateProperty(prop) {
        prop = prop.toLowerCase();
        if (ButtonGroup.backgroundColor.includes(prop)) return [true, "" + prop];
        if (ButtonGroup.size.includes(prop)) return [true, "" + prop];
        if (ButtonGroup.equalWidth.includes(prop)) return [true, "" + prop];
        return [false, ""];
      }
    }, {
      key: "$onBackgroundColorChanged",
      value: function $onBackgroundColorChanged() {
        var _validateProperty = this.validateProperty(this.backgroundColor),
            _validateProperty2 = _slicedToArray(_validateProperty, 2),
            pass = _validateProperty2[0],
            css = _validateProperty2[1];

        if (!pass) return;
        this.dom.classList.remove("" + this._backgroundColor);
        this.dom.classList.add(css);
        this._backgroundColor = this.backgroundColor;
      }
    }, {
      key: "$onSizeChanged",
      value: function $onSizeChanged() {
        var _validateProperty3 = this.validateProperty(this.size),
            _validateProperty4 = _slicedToArray(_validateProperty3, 2),
            pass = _validateProperty4[0],
            css = _validateProperty4[1];

        if (!pass) return;
        this.dom.classList.remove("" + this._size);
        this.dom.classList.add(css);
        this._size = this.size;
      }
    }, {
      key: "$onEqualwidthChanged",
      value: function $onEqualwidthChanged() {
        var _validateProperty5 = this.validateProperty(this.equalWidth),
            _validateProperty6 = _slicedToArray(_validateProperty5, 2),
            pass = _validateProperty6[0],
            css = _validateProperty6[1];

        if (!pass) return;
        this.dom.classList.remove("" + this._equalWidth);
        this.dom.classList.add(css);
        this._equalWidth = this.equalWidth;
      }
    }, {
      key: "$onFluidChanged",
      value: function $onFluidChanged() {
        this.dom.classList.remove("fluid");
        if (this.fluid) this.dom.classList.add("fluid");
      }
    }, {
      key: "$onVerticalChanged",
      value: function $onVerticalChanged() {
        this.dom.classList.remove("vertical");
        if (this.vertical) this.dom.classList.add("vertical");
      }
    }, {
      key: "$onBasicChanged",
      value: function $onBasicChanged() {
        this.dom.classList.remove("basic");
        if (this.basic) this.dom.classList.add("basic");
      }
    }]);

    return ButtonGroup;
  }();

  ButtonGroup.backgroundColor = ["red", "orange", "yellow", "olive", "green", "teal", "blue", "violet", "purple", "pink", "brown", "grey", "black"];

  ButtonGroup.size = ["mini", "tiny", "small", "medium", "large", "big", "huge", "massive"];

  ButtonGroup.equalWidth = ["two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"];

  QmlWeb.registerQmlType({
    module: "Semantic.Html",
    name: "ButtonGroup",
    versions: /.*/,
    baseClass: "Semantic.Html.Dom",
    properties: {
      text: "string",
      vertical: "bool",
      size: "string",
      backgroundColor: "string",
      equalWidth: "string",
      basic: "bool",
      fluid: { type: "bool", initialValue: true },
      enabled: { type: "bool", initialValue: true }
    },
    signals: {
      clicked: []
    }
  }, ButtonGroup);
}
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Calendar",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    startDate: { type: "string", initialValue: "" },
    endDate: { type: "string", initialValue: "" },
    firstDayOfWeek: { type: "int", initialValue: 0 },
    multipleSelection: 'bool',
    selectedDate: 'var'
  },
  signals: {
    selected: [{ type: "string", name: "value" }]
  }
}, function () {
  function _class76(meta) {
    var _this51 = this;

    _classCallCheck(this, _class76);

    QmlWeb.callSuper(this, meta);

    this.Component.completed.connect(this, this.Component$onCompleted);
    this.startDateChanged.connect(this, this.$onStartDateChanged);
    this.endDateChanged.connect(this, this.$onEndDateChanged);
    this.selectedDateChanged.connect(this, this.$onSelectedDateChanged);
    this.multipleSelectionChanged.connect(this, this.$onMultipleSelectionChanged);

    var template = "<div class=\"vccalendar dropdown-menu\">\n                            <div class=\"ranges\"></div>\n                            <div class=\"calendar first left\"></div>\n                        </div>";

    this.dom = $(template)[0];

    $(this.dom).on("selectDate", function (evt, value) {
      _this51.bySystem = true;
      _this51.selectedDate = value;
      _this51.bySystem = false;
      _this51.selected(value);
    });

    $(this.dom).on("selectDates", function (evt, value) {
      _this51.bySystem = true;
      _this51.selectedDate = value;
      _this51.bySystem = false;
      _this51.selected(value);
    });
  }

  _createClass(_class76, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var _this52 = this;

      $(document).ready(function () {
        !_this52.setting && _this52.ThaiStyleSetting();
        _this52.refreshCalendar();

        //Do the thing that can't do before component is completed
        //Set selectedDate 
        _this52.selectedDate && _this52.$onSelectedDateChanged();
      });
    }
  }, {
    key: "$onSelectedDateChanged",
    value: function $onSelectedDateChanged() {
      if (this.bySystem) return;
      if (!this.calendar) return;
      if (!this.multipleSelection && typeof this.selectedDate !== "string") {
        console.error("Selected Date is not a string type");
        return;
      }
      if (this.multipleSelection && !(this.selectedDate instanceof Array)) {
        console.error("Selected Date is not an Array type");
        return;
      }

      if (!this.multipleSelection) {
        this.calendar.setCalendarDate(this.selectedDate);
      }
      if (this.multipleSelection) {
        this.calendar.setCalendarDates(this.selectedDate);
      }
    }
  }, {
    key: "getDate",
    value: function getDate() {
      if (!this.calendar) return;
      if (!this.multipleSelection) {
        return this.calendar.getCalendarDate(this.selectedDate);
      }
      if (this.multipleSelection) {
        return this.calendar.getCalendarDates(this.selectedDate);
      }
    }
  }, {
    key: "$onMultipleSelectionChanged",
    value: function $onMultipleSelectionChanged() {
      this.ThaiStyleSetting();
      this.setting["multipleSelect"] = this.multipleSelection;
      this.calendar && this.refreshCalendar();
    }
  }, {
    key: "$onStartDateChanged",
    value: function $onStartDateChanged() {
      this.ThaiStyleSetting();
      Reflect.deleteProperty(this.setting, "startDate");
      if (this.startDate !== "") this.setting["startDate"] = this.startDate;
      this.calendar && this.refreshCalendar();
    }
  }, {
    key: "$onEndDateChanged",
    value: function $onEndDateChanged() {
      this.ThaiStyleSetting();
      Reflect.deleteProperty(this.setting, "endDate");
      if (this.endDate !== "") this.setting["endDate"] = this.endDate;
      this.calendar && this.refreshCalendar();
    }
  }, {
    key: "refreshCalendar",
    value: function refreshCalendar() {
      this.calendar = $(this.dom).calendar(this.setting);
    }
  }, {
    key: "ThaiStyleSetting",
    value: function ThaiStyleSetting() {
      this.setting = {};
      this.setting["singleDatePicker"] = true;
      this.setting["separator"] = " - ";
      this.setting["showDropdowns"] = true;
      this.setting["multipleSelect"] = false;
      this.setting["ranges"] = {};
      this.setting["ranges"]["Today"] = [moment(), moment()];
      this.setting["locale"] = {};
      this.setting["locale"]["weekLabel"] = "W";
      this.setting["locale"]["daysOfWeek"] = ["อ.", "จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส."];
      this.setting["locale"]["firstDay"] = 0;
      this.setting["locale"]["monthNames"] = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม "];

      if (this.startDate !== "") this.setting["startDate"] = this.startDate;
      if (this.endDate !== "") this.setting["endDate"] = this.endDate;
    }
  }]);

  return _class76;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Card",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    group: "bool"
  },
  signals: {}
}, function () {
  function _class77(meta) {
    _classCallCheck(this, _class77);

    QmlWeb.callSuper(this, meta);
    this.groupChanged.connect(this, this.$onGroupChanged);

    this.suffixClassName = "card";
  }

  _createClass(_class77, [{
    key: "$onGroupChanged",
    value: function $onGroupChanged() {
      if (this.group) this.suffixClassName = "cards";else this.suffixClassName = "card";
    }
  }]);

  return _class77;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "CheckBox",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    checked: "bool",
    value: "var",
    readOnly: "bool",
    text: "string",
    color: "string",
    toggleColor: "string",
    fitted: "bool",
    type: "string",
    dataValidate: "string",
    enabled: { type: "bool", initialValue: true }
  },
  signals: {
    changed: [{ name: "event", type: "var" }, { name: "value", type: "var" }, { name: "bySystem", type: "var" }]
  }
}, function () {
  function _class78(meta) {
    var _this53 = this;

    _classCallCheck(this, _class78);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.checkedChanged.connect(this, this.$onCheckedChanged);
    this.valueChanged.connect(this, this.$onValueChanged);
    this.textChanged.connect(this, this.$onTextChanged);
    this.enabledChanged.connect(this, this.$onEnabledChanged);
    this.readOnlyChanged.connect(this, this.$onReadOnlyChanged);
    this.colorChanged.connect(this, this.$onColorChanged);
    this.fittedChanged.connect(this, this.$onFittedChanged);
    this.typeChanged.connect(this, this.$onTypeChanged);
    this.dataValidateChanged.connect(this, this.$onDataValidateChanged);
    this.toggleColorChanged.connect(this, this.$onToggleColorChanged);

    this.checkbox = document.createElement("input");
    this.label = document.createElement("label");
    this.checkbox.type = "checkbox";
    this.dom.appendChild(this.checkbox);
    this.dom.appendChild(this.label);
    this.suffixClassName = "checkbox";

    this.checkbox.onchange = function (event) {
      _this53.onCheckedChanged();
      _this53.changed(event, _this53.checkbox.checked, _this53.bySystem);
    };
  }

  _createClass(_class78, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var _this54 = this;

      $(document).ready(function () {
        return $(_this54.dom).checkbox();
      });
    }

    //override

  }, {
    key: "$onHtmlIDChanged",
    value: function $onHtmlIDChanged() {
      this.checkbox.id = this.htmlID;
    }
  }, {
    key: "$onDataValidateChanged",
    value: function $onDataValidateChanged() {
      this.checkbox.setAttribute("data-validate", this.dataValidate);
    }
  }, {
    key: "$onCheckedChanged",
    value: function $onCheckedChanged() {
      if (!this.bySystem) {
        this.checkbox.checked = this.checked;
        this.changed(null, this.checked, this.bySystem);
      }
    }
  }, {
    key: "onCheckedChanged",
    value: function onCheckedChanged() {
      this.bySystem = true;
      this.checked = this.checkbox.checked;
      this.bySystem = false;
    }
  }, {
    key: "$onValueChanged",
    value: function $onValueChanged() {
      this.checkbox.value = this.value;
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged() {
      this.label.innerHTML = this.text;
    }
  }, {
    key: "$onEnabledChanged",
    value: function $onEnabledChanged() {
      this.dom.classList.remove("disabled");
      if (!this.enabled) this.dom.classList.add("disabled");
    }
  }, {
    key: "$onReadOnlyChanged",
    value: function $onReadOnlyChanged() {
      this.dom.classList.remove("read-only");
      if (this.readOnly) this.dom.classList.add("read-only");
    }
  }, {
    key: "$onColorChanged",
    value: function $onColorChanged() {
      this.label.style.color = this.color;
    }
  }, {
    key: "$onToggleColorChanged",
    value: function $onToggleColorChanged() {
      var _validateProperty7 = this.validateProperty(this.toggleColor),
          _validateProperty8 = _slicedToArray(_validateProperty7, 2),
          pass = _validateProperty8[0],
          css = _validateProperty8[1];

      if (!pass) return;
      this.dom.classList.remove("" + this._color);
      if (!css) return; // return if css is "" prevent error when call classList.add with ""
      this.dom.classList.add(css);
      this._color = this.color;
    }
  }, {
    key: "$onFittedChanged",
    value: function $onFittedChanged() {
      this.dom.classList.remove("fitted");
      if (this.fitted) this.dom.classList.add("fitted");
    }
  }, {
    key: "$onTypeChanged",
    value: function $onTypeChanged() {
      if (this._lastType) this.dom.classList.remove(this._lastType);

      this.dom.classList.add(this.type);
      this._lastType = this.type;
    }
  }, {
    key: "validateProperty",
    value: function validateProperty(prop) {
      var colorList = ["", "red", "orange", "yellow", "olive", "green", "teal", "blue", "violet", "purple", "pink", "brown", "grey", "black"];

      if (prop || prop === "") {
        // prevent error from undefined prop and allow property ""
        prop = prop.toLowerCase();
        if (colorList.includes(prop)) {
          return [true, "" + prop];
        }
      }
      return [false, ""];
    }
  }]);

  return _class78;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Column",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {}
}, function () {
  function _class79(meta) {
    _classCallCheck(this, _class79);

    QmlWeb.callSuper(this, meta);
    this.baseClassName = "ui";
    this.suffixClassName = "column";
  }

  return _class79;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "ComboBox",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    inputName: "string",
    text: "string",
    search: "bool",
    focused: "bool",
    error: "bool",
    fluid: "bool",
    multipleSelection: "bool",
    compact: "bool",
    allowAdditions: { type: "bool", initialValue: true },
    maxSelections: "int",
    items: "var",
    dataValidate: "string",
    enabled: { type: "bool", initialValue: true },
    forceSelection: { type: "bool", initialValue: false },
    value: "string",
    searchText: "string",
    fullTextSearch: "var",
    optionTextField: "string"
  },
  signals: {
    changed: [],
    keyup: [{ type: "string", name: "event" }]
  }
}, function () {
  function _class80(meta) {
    _classCallCheck(this, _class80);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.focusedChanged.connect(this, this.$onFocusChanged);
    this.textChanged.connect(this, this.$onTextChanged);
    this.inputNameChanged.connect(this, this.$onInputNameChanged);
    this.searchChanged.connect(this, this.$onSearchChanged);
    this.fluidChanged.connect(this, this.$onFluidChanged);
    this.allowAdditionsChanged.connect(this, this.$onAllowAdditionsChanged);
    this.multipleSelectionChanged.connect(this, this.$onMultipleSelectionChanged);
    this.enabledChanged.connect(this, this.$onEnabledChanged);
    this.maxSelectionsChanged.connect(this, this.$onMaxSelectionsChanged);
    this.compactChanged.connect(this, this.$onCompactChanged);
    this.itemsChanged.connect(this, this.$onItemsChanged);
    this.valueChanged.connect(this, this.$onValueChanged);
    this.searchTextChanged.connect(this, this.$onSearchTextChanged);
    this.dataValidateChanged.connect(this, this.$onDataValidateChanged);
    this.fullTextSearchChanged.connect(this, this.$onFullTextSearchChanged);
    this.forceSelectionChanged.connect(this, this.$onForceSelectionChanged);

    this.baseClassName = "ui";
    this.suffixClassName = "selection dropdown";
    this.input = document.createElement("input");
    this.input.type = "hidden";
    this.defaultText = document.createElement("div");
    this.defaultText.classList.add("default", "text");
    this.icon = document.createElement("i");
    this.icon.classList.add("dropdown", "icon");
    this.menu = document.createElement("div");
    this.menu.classList.add("menu");

    this.dom.appendChild(this.input);
    this.dom.appendChild(this.defaultText);
    this.dom.appendChild(this.icon);
    this.dom.appendChild(this.menu);

    this.$dropdown = $(this.dom);

    this.changeBySystem = false;
    this.dropdown_setting = {
      allowAdditions: true,
      forceSelection: false,
      keys: {
        delimiter: false
      },
      onAdd: this.onAdd.bind(this),
      onChange: this.onChange.bind(this)
    };
  }

  _createClass(_class80, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var _this55 = this;

      this.children.forEach(function (child) {
        var comboItem = child.dom.children[0];
        _this55.menu.appendChild(comboItem);
        child.dom.remove();
      });

      //start semantic component
      this.$dropdown = $(this.dom);
      $(document).ready(function () {
        _this55.$dropdown.dropdown(_this55.dropdown_setting);
        _this55.$searchInput = _this55.$dropdown.find('input.search');
        _this55.$searchInput.on('keyup', function (event) {
          _this55.bySystem = true;
          _this55.searchText = _this55.$searchInput.val();
          _this55.keyup(event);
          _this55.bySystem = false;
        });
        _this55.completed = true;
        _this55.$onValueChanged();
        _this55.$onSearchTextChanged();
      });
    }

    //override

  }, {
    key: "$onHtmlIDChanged",
    value: function $onHtmlIDChanged() {
      this.input.id = this.htmlID;
    }
  }, {
    key: "$onValueChanged",
    value: function $onValueChanged() {
      if (this.bySystem && !this.completed) return;

      if (!this.value) {
        this.clear();
      } else {
        this.setSelected(this.value.split(","));
      }
    }
  }, {
    key: "$onSearchTextChanged",
    value: function $onSearchTextChanged() {
      if (this.bySystem && !this.completed) return;
      if (this.search) {
        this.$searchInput.val(this.searchText);
      }
    }
  }, {
    key: "$onDataValidateChanged",
    value: function $onDataValidateChanged() {
      this.input.setAttribute("data-validate", this.dataValidate);
    }
  }, {
    key: "$onFocusChanged",
    value: function $onFocusChanged() {
      if (this.focused) this.setFocus();
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged() {
      if (this.bySystem) return;

      this.defaultText.innerHTML = this.text;
    }
  }, {
    key: "$onInputNameChanged",
    value: function $onInputNameChanged() {
      this.input.name = this.inputName;
    }
  }, {
    key: "$onSearchChanged",
    value: function $onSearchChanged() {
      this.dom.classList.remove("search");
      if (this.search) this.dom.classList.add("search");
    }
  }, {
    key: "$onFluidChanged",
    value: function $onFluidChanged() {
      this.dom.classList.remove("fluid");
      if (this.fluid) this.dom.classList.add("fluid");
    }
  }, {
    key: "$onMultipleSelectionChanged",
    value: function $onMultipleSelectionChanged() {
      this.dom.classList.remove("multiple");
      if (this.multipleSelection) this.dom.classList.add("multiple");
    }
  }, {
    key: "$onEnabledChanged",
    value: function $onEnabledChanged() {
      this.dom.classList.remove("disabled");
      if (!this.enabled) this.dom.classList.add("disabled");
    }
  }, {
    key: "$onCompactChanged",
    value: function $onCompactChanged() {
      this.dom.classList.remove("compact");
      if (this.compact) this.dom.classList.add("compact");
    }
  }, {
    key: "$onMaxSelectionsChanged",
    value: function $onMaxSelectionsChanged() {
      this.dropdown_setting.maxSelections = this.maxSelections;
      this.$dropdown && this.$dropdown.dropdown(this.dropdown_setting);
    }
  }, {
    key: "$onAllowAdditionsChanged",
    value: function $onAllowAdditionsChanged() {
      this.dropdown_setting.allowAdditions = this.allowAdditions;
      this.$dropdown && this.$dropdown.dropdown(this.dropdown_setting);
    }
  }, {
    key: "$onFullTextSearchChanged",
    value: function $onFullTextSearchChanged() {
      this.dropdown_setting.fullTextSearch = this.fullTextSearch;
      this.$dropdown && this.$dropdown.dropdown(this.dropdown_setting);
    }
  }, {
    key: "$onForceSelectionChanged",
    value: function $onForceSelectionChanged() {
      this.dropdown_setting.forceSelection = this.forceSelection;
      this.$dropdown && this.$dropdown.dropdown(this.dropdown_setting);
    }
  }, {
    key: "$onItemsChanged",
    value: function $onItemsChanged() {
      this.menu.innerHTML = "";
      var foundValueInItems = false;
      if (!this.items) return;
      var _iteratorNormalCompletion4 = true;
      var _didIteratorError4 = false;
      var _iteratorError4 = undefined;

      try {
        for (var _iterator4 = this.items[Symbol.iterator](), _step4; !(_iteratorNormalCompletion4 = (_step4 = _iterator4.next()).done); _iteratorNormalCompletion4 = true) {
          var item = _step4.value;

          if (item.id == this.value) {
            foundValueInItems = true;
            break;
          }
        }
      } catch (err) {
        _didIteratorError4 = true;
        _iteratorError4 = err;
      } finally {
        try {
          if (!_iteratorNormalCompletion4 && _iterator4.return) {
            _iterator4.return();
          }
        } finally {
          if (_didIteratorError4) {
            throw _iteratorError4;
          }
        }
      }

      if (!foundValueInItems) {
        this.$dropdown && this.clear();
      }
      this.addItems(this.items);
    }
  }, {
    key: "onAdd",
    value: function onAdd(addedValue, addedText, $addedChoice) {
      if ($addedChoice[0].classList.contains("addition")) {
        $(this.dom).dropdown("remove visible");
      }
    }
  }, {
    key: "onChange",
    value: function onChange(value, text, $choice) {
      this.bySystem = true;
      this.value = this.getValue();
      this.text = this.defaultText.innerHTML;
      this.bySystem = false;

      //fire change signal
      this.changed();

      if (this.dom.classList.contains("multiple")) return;
      if ($choice && $choice[0].classList.contains("addition")) {
        $(this.dom).dropdown("remove visible");
      }
    }
  }, {
    key: "setFocus",
    value: function setFocus() {
      var _this56 = this;

      requestAnimationFrame(function () {
        return _this56.dom.focus();
      });
    }
  }, {
    key: "getValue",
    value: function getValue() {
      return this.$dropdown.dropdown("get value");
    }
  }, {
    key: "clear",
    value: function clear() {
      // Clear selection (preserve items)
      this.$dropdown && this.$dropdown.dropdown("clear");
    }
  }, {
    key: "setSelected",
    value: function setSelected(value) {
      this.$dropdown.dropdown("set selected", value);
    }
  }, {
    key: "getIndex",
    value: function getIndex() {
      var selected = this.getValue();
      for (var i = 0; i < this.items.length; i++) {
        if (this.items[i].id == selected) return i;
      }
      return -1;
    }
  }, {
    key: "getText",
    value: function getText() {
      var values = this.$dropdown.dropdown("get value");
      var result = [];
      if (values) {
        var _iteratorNormalCompletion5 = true;
        var _didIteratorError5 = false;
        var _iteratorError5 = undefined;

        try {
          for (var _iterator5 = this.$dropdown.dropdown("get item", values.split(","))[Symbol.iterator](), _step5; !(_iteratorNormalCompletion5 = (_step5 = _iterator5.next()).done); _iteratorNormalCompletion5 = true) {
            selected = _step5.value;

            result.push(selected.innerText);
          }
        } catch (err) {
          _didIteratorError5 = true;
          _iteratorError5 = err;
        } finally {
          try {
            if (!_iteratorNormalCompletion5 && _iterator5.return) {
              _iterator5.return();
            }
          } finally {
            if (_didIteratorError5) {
              throw _iteratorError5;
            }
          }
        }
      }
      return result.join(",");
    }
  }, {
    key: "addItems",
    value: function addItems(items) {
      var _this57 = this;

      items.forEach(function (item, i) {
        var classList = item.disabled ? "disabled item" : "item";
        if (_this57.optionTextField) {
          item.name = item[_this57.optionTextField];
        }
        _this57.menu.appendChild($("<div>", {
          class: classList,
          text: item.name || item.text,
          "data-value": item.id
        })[0]);
      }, this);

      //re-initialize dropdown after add new items
      this.$dropdown.dropdown(this.dropdown_setting);
      if (this.value) {
        this.setSelected(this.value);
      }
    }
  }]);

  return _class80;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Container",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {},
  signals: {}
}, function () {
  function _class81(meta) {
    _classCallCheck(this, _class81);

    QmlWeb.callSuper(this, meta);
    this.baseClassName = "ui container";
  }

  return _class81;
}());
// DateTextBox.size = [
//     "mini",
//     "small",
//     "large",
//     "big",
//     "huge",
//     "massive"
// ];

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "DateTextBox",
  versions: /.*/,
  baseClass: "Semantic.Html.TextBox",
  properties: {
    buttons: "var",
    thai: "bool",
    startDate: { type: "string", initialValue: "" },
    endDate: { type: "string", initialValue: "" },
    firstDayOfWeek: { type: "int", initialValue: 0 },
    //if this property is set
    //the DateTextBox will set its position relative to this property
    boundary: "var",
    //TODO check why these props is not inherited from baseItem
    doc_label: "string",
    doc_mandatory: "bool",
    doc_auto_input: "bool",
    doc_condition: "string",
    doc_remark: "string"
  },
  signals: {
    changed: [{ type: "string", name: "value" }]
  }
}, function () {
  function DateTextBox(meta) {
    var _this58 = this;

    _classCallCheck(this, DateTextBox);

    var icon = document.createElement("i");
    QmlWeb.callSuper(this, meta);

    this.Component.completed.connect(this, this.Component$onCompleted);
    this.buttonsChanged.connect(this, this.$onButtonsChanged);
    this.thaiChanged.connect(this, this.$onThaiChanged);
    this.startDateChanged.connect(this, this.$onStartDateChanged);
    this.endDateChanged.connect(this, this.$onEndDateChanged);
    this.boundaryChanged.connect(this, this.$onBoundaryChanged);

    this.singleMode = true;
    this.thai = true;

    this.addClass("icon");
    icon.classList.add("calendar", "icon");
    this.dom.appendChild(icon);

    $(this.input).on("dateChange", function (evt, val) {
      _this58.bySystem = true;
      _this58.text = val;
      _this58.bySystem = false;
      _this58.changed(val);
    });

    $(this.input).on("blur", function (evt) {
      if (_this58.error) _this58.text = "";
    });

    $(this.input).on("keydown", function (evt) {
      if (_this58.error && evt.keyCode === 13) _this58.text = "";
    });
  }

  _createClass(DateTextBox, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var _this59 = this;

      $(document).ready(function () {
        _this59.refreshCalendar();
        _this59.datePicker.data('daterangepicker').updateDateText();
      });
    }
  }, {
    key: "toDashFormat",
    value: function toDashFormat() {
      if (this.input.value === "") return "";

      var _input$value$split = this.input.value.split("/"),
          _input$value$split2 = _slicedToArray(_input$value$split, 3),
          day = _input$value$split2[0],
          month = _input$value$split2[1],
          year = _input$value$split2[2];

      return year + "-" + month + "-" + day;
    }
  }, {
    key: "toSlashFormat",
    value: function toSlashFormat() {
      if (this.input.value === "") return "";

      var _input$value$split3 = this.input.value.split("-"),
          _input$value$split4 = _slicedToArray(_input$value$split3, 3),
          day = _input$value$split4[0],
          month = _input$value$split4[1],
          year = _input$value$split4[2];

      return day + "/" + month + "/" + year;
    }
  }, {
    key: "$onBoundaryChanged",
    value: function $onBoundaryChanged() {
      this.thai ? this.ThaiStyleSetting() : this.EnglishStyleSetting();
      if (this.boundary && this.boundary.dom) this.setting["parentEl"] = this.boundary.dom;
      if (this.boundary && typeof this.boundary === "string") this.setting["parentEl"] = this.boundary;
      this.datePicker && this.refreshCalendar();
    }
  }, {
    key: "$onThaiChanged",
    value: function $onThaiChanged() {
      this.thai ? this.ThaiStyleSetting() : this.EnglishStyleSetting();
      this.datePicker && this.refreshCalendar();
    }
  }, {
    key: "$onStartDateChanged",
    value: function $onStartDateChanged() {
      this.thai ? this.ThaiStyleSetting() : this.EnglishStyleSetting();
      Reflect.deleteProperty(this.setting, "startDate");
      if (this.startDate !== "") this.setting["startDate"] = this.startDate;
      this.datePicker && this.refreshCalendar();
    }
  }, {
    key: "$onEndDateChanged",
    value: function $onEndDateChanged() {
      this.thai ? this.ThaiStyleSetting() : this.EnglishStyleSetting();
      Reflect.deleteProperty(this.setting, "endDate");
      if (this.endDate !== "") this.setting["endDate"] = this.endDate;
      this.datePicker && this.refreshCalendar();
    }
  }, {
    key: "$onButtonsChanged",
    value: function $onButtonsChanged() {
      var _this60 = this;

      this.thai ? this.ThaiStyleSetting() : this.EnglishStyleSetting();

      if (this.buttons.length > 0) this.setting["ranges"] = {};

      this.buttons.forEach(function (button) {
        if (typeof button.date === "number") {
          var date = moment();

          if (_this60.thai) {
            date.add(button.date, 'day');
            var year = date.year() + 543,
                month = date.month() + 1,
                day = date.date();
            date = day + "/" + month + "/" + year;
          }

          if (!_this60.thai) {
            date.add(button.date, 'day');
          }

          _this60.setting["ranges"][button.text] = [date, date];
        }
      });

      this.datePicker && this.refreshCalendar();
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged() {
      if (this.bySystem) return;
      this.input.value = this.text;
      this.datePicker && this.datePicker.data('daterangepicker').updateDateText();
    }
  }, {
    key: "notValidDate",
    value: function notValidDate() {
      this.error = this.text.length === 0 ? false : true;
    }
  }, {
    key: "validDate",
    value: function validDate() {
      this.error = false;
    }
  }, {
    key: "refreshCalendar",
    value: function refreshCalendar() {
      this.datePicker = $(this.input).daterangepicker(this.setting, null, this.validDate.bind(this), this.notValidDate.bind(this));
    }
  }, {
    key: "ThaiStyleSetting",
    value: function ThaiStyleSetting() {
      this.setting = {};
      this.setting["singleDatePicker"] = this.singleMode ? true : false;
      this.setting["singleModeRange"] = this.singleMode ? true : false;
      this.setting["thai"] = this.thai ? true : false;
      this.setting["separator"] = " - ";
      this.setting["showDropdowns"] = true;
      this.setting["locale"] = {};
      this.setting["locale"]["applyLabel"] = "ยืนยัน";
      this.setting["locale"]["cancelLabel"] = "ยกเลิก";
      this.setting["locale"]["fromLabel"] = "จาก";
      this.setting["locale"]["toLabel"] = "ถึง";
      this.setting["locale"]["customRangeLabel"] = "เพิ่มเติม";
      this.setting["locale"]["weekLabel"] = "W";
      this.setting["locale"]["daysOfWeek"] = ["อ.", "จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส."];
      this.setting["locale"]["firstDay"] = 0;
      this.setting["locale"]["monthNames"] = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม "];

      if (this.startDate !== "") this.setting["startDate"] = this.startDate;
      if (this.endDate !== "") this.setting["endDate"] = this.endDate;
    }
  }, {
    key: "EnglishStyleSetting",
    value: function EnglishStyleSetting() {
      this.setting = {};
      this.setting["singleDatePicker"] = this.singleMode ? true : false;
      this.setting["singleModeRange"] = this.singleMode ? true : false;
      this.setting["thai"] = this.thai ? true : false;
      this.setting["separator"] = " - ";
      this.setting["showDropdowns"] = true;
      if (this.startDate !== "") this.setting["startDate"] = this.startDate;
      if (this.endDate !== "") this.setting["endDate"] = this.endDate;
    }
  }]);

  return DateTextBox;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Divider",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    text: "string"
  }
}, function () {
  function _class82(meta) {
    _classCallCheck(this, _class82);

    QmlWeb.callSuper(this, meta);
    this.textChanged.connect(this, this.$onTextChanged);
    this.baseClassName = "ui";
    this.suffixClassName = "divider";
  }

  _createClass(_class82, [{
    key: "$onTextChanged",
    value: function $onTextChanged() {
      if (this.text !== "" && !this.dom.classList.contains("horizontal")) this.dom.classList.add("horizontal");
      this.dom.innerHTML = this.text;
    }
  }]);

  return _class82;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Dom",
  versions: /.*/,
  baseClass: "QtQml.QtObject",
  properties: {
    $opacity: { type: "real", initialValue: 1 },
    parent: "Item",
    htmlID: "string",
    htmlAttr: "var",
    data: "list",
    children: "list",
    resources: "list",
    visible: { type: "bool", initialValue: true },
    displayNone: { type: "bool", initialValue: false },
    tagName: { type: "string", initialValue: "div" },
    baseClassName: { type: "string", initialValue: "ui" },
    suffixClassName: { type: "string", initialValue: "" },
    className: { type: "string", initialValue: "" },
    customClass: { type: "string", initialValue: "" },
    text: { type: "string", initialValue: "" },
    style: { type: "var", initialValue: null },

    // property for ui2doc
    doc_label: "string",
    doc_mandatory: "bool",
    doc_auto_input: "bool",
    doc_condition: "string",
    doc_remark: "string",
    doc_read_only: "bool",
    doc_skip: "var", // "me", "all", "child"
    doc_type: "string"
  },
  defaultProperty: "data"
}, function () {
  function _class83(meta) {
    _classCallCheck(this, _class83);

    QmlWeb.callSuper(this, meta);

    if (this.$parent === null) {
      // This is the root element. Initialize it.
      this.dom = QmlWeb.engine.rootElement || document.body.appendChild(document.createElement("div"));
      this.dom.innerHTML = "";
    }
    this.baseClassNameChanged.connect(this, this.$onClassNameChanged);
    this.suffixClassNameChanged.connect(this, this.$onClassNameChanged);
    this.classNameChanged.connect(this, this.$onClassNameChanged);
    this.customClassChanged.connect(this, this.$onClassNameChanged);

    this.parentChanged.connect(this, this.$onParentChanged_);
    this.dataChanged.connect(this, this.$onDataChanged);
    this.textChanged.connect(this, this.$onTextChanged);
    this.styleChanged.connect(this, this.$onStyleChanged);
    this.htmlIDChanged.connect(this, this.$onHtmlIDChanged);
    this.htmlAttrChanged.connect(this, this.$onHtmlAttrChanged);
    this.visibleChanged.connect(this, this.$onVisibleChanged);
    this.displayNoneChanged.connect(this, this.$onDisplayNoneChanged);

    if (!this.dom) {
      // Create a dom element for this item.
      var tagName = meta.object.tagName || "div";
      var node = document.createElement(tagName);
      this.dom = node;
    }
    // TODO: support properties, styles, perhaps changing the tagName
  }

  _createClass(_class83, [{
    key: "$onClassNameChanged",
    value: function $onClassNameChanged() {
      var classList = [];
      classList.push(this.baseClassName);
      classList.push(this.className);
      classList.push(this.suffixClassName);
      classList.push(this.customClass);

      this.dom.className = classList.join(" ").trim();
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged() {
      this.dom.innerHTML = this.text;
    }
  }, {
    key: "$onStyleChanged",
    value: function $onStyleChanged() {
      if (typeof this.style === "string") this.dom.style = this.style;
      if (_typeof(this.style) === "object") $(this.dom).css(this.style);
    }
  }, {
    key: "$onHtmlIDChanged",
    value: function $onHtmlIDChanged() {
      this.dom.id = this.htmlID;
    }
  }, {
    key: "$onHtmlAttrChanged",
    value: function $onHtmlAttrChanged() {
      var newVal = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};

      $(this.dom).attr(newVal);
    }
  }, {
    key: "$onVisibleChanged",
    value: function $onVisibleChanged() {
      if (this.visible) this.dom.style.visibility = "visible";else this.dom.style.visibility = "hidden";
    }
  }, {
    key: "$onDisplayNoneChanged",
    value: function $onDisplayNoneChanged() {
      if (this.displayNone) this.dom.style.display = "none";else this.dom.style.display = "";
    }
  }, {
    key: "$onParentChanged_",
    value: function $onParentChanged_(newParent, oldParent, propName) {
      if (oldParent) {
        oldParent.children.splice(oldParent.children.indexOf(this), 1);
        oldParent.childrenChanged();

        //Workaround for removing node error in DCustomColumn
        var hasParentNode = this.dom.parentNode !== null;
        var sameParentNode = hasParentNode && this.dom.parentNode.isSameNode(oldParent.dom);

        if (hasParentNode && sameParentNode) {
          oldParent.dom.removeChild(this.dom);
        }
        if (hasParentNode && !sameParentNode) {
          this.dom.parentNode.removeChild(this.dom);
        }
      }
      if (newParent && newParent.children.indexOf(this) === -1) {
        newParent.children.push(this);
        newParent.childrenChanged();
      }
      if (newParent) {
        //set repeater's items position
        if (this._placeAfter === "first") {
          newParent.dom.insertAdjacentElement("afterbegin", this.dom);
        } else if (this._placeAfter) {
          $(this.dom).insertAfter(this._placeAfter);
        } else {
          newParent.dom.appendChild(this.dom);
        }
      }
    }
  }, {
    key: "addClass",
    value: function addClass(str) {
      this.customClass += " " + str;
    }
  }, {
    key: "removeClass",
    value: function removeClass(str) {
      var classList = this.className.split(" ");
      classList = classList.filter(function (item) {
        return item !== str ? item : null;
      });
      this.className = classList.join(" ");
      classList = this.customClass.split(" ");
      classList = classList.filter(function (item) {
        return item !== str ? item : null;
      });
      this.customClass = classList.join(" ");
    }
  }, {
    key: "$onDataChanged",
    value: function $onDataChanged(newData) {
      var HtmlDom = QmlWeb.getConstructor("Semantic.Html", "1.0", "Dom");
      for (var i in newData) {
        var child = newData[i];
        if (child instanceof HtmlDom) {
          child.parent = this; // This will also add it to children.
        } else {
          this.resources.push(child);
        }
      }
    }
  }, {
    key: "transition",
    value: function transition(value) {
      $(this.dom).transition(value);
    }
  }]);

  return _class83;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Field",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    label: { type: "string", initialValue: "&nbsp;" },
    skipInline: { type: "bool", initialValue: false },
    labelColor: "string",
    enabled: { type: "bool", initialValue: true },
    labelAlign: "string"
  },
  signals: {
    clicked: []
  }
}, function () {
  function _class84(meta) {
    var _this61 = this;

    _classCallCheck(this, _class84);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.baseClassName = "";
    this.suffixClassName = "field";
    this.labelChanged.connect(this, this.$onLabelChanged);
    this.labelColorChanged.connect(this, this.$onLabelColorChanged);
    this.enabledChanged.connect(this, this.$onEnabledChanged);
    this.labelAlignChanged.connect(this, this.$onLabelAlignChanged);
    this.$onLabelChanged();

    this.dom.onclick = function () {
      _this61.clicked();
    };
  }

  _createClass(_class84, [{
    key: "$onLabelChanged",
    value: function $onLabelChanged() {
      if (!this.labelNode) {
        this.labelNode = document.createElement("label");
        this.dom.insertBefore(this.labelNode, this.dom.firstChild);
      }
      this.labelNode.innerHTML = this.label;
    }
  }, {
    key: "$onLabelColorChanged",
    value: function $onLabelColorChanged() {
      this.labelNode.style.color = this.labelColor;
    }
  }, {
    key: "$onEnabledChanged",
    value: function $onEnabledChanged() {
      this.removeClass("disabled");
      if (!this.enabled) this.addClass("disabled");
    }
  }, {
    key: "$onLabelAlignChanged",
    value: function $onLabelAlignChanged() {
      if (this.labelAlign) {
        this.labelNode.style.width = "100%";
      } else {
        this.labelNode.style.width = "";
      }

      this.labelNode.style.textAlign = this.labelAlign;
    }
  }, {
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var isInline = this.dom.classList.contains("inline") || this.parent.dom.classList.contains("inline");
      var containsNBSP = this.label === "&nbsp;";
      var hasChildLabel = this.labelNode.parentNode && this.labelNode.parentNode.isSameNode(this.dom);

      if (isInline && containsNBSP && hasChildLabel) {
        this.dom.removeChild(this.labelNode);
      }
    }
  }]);

  return _class84;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Fields",
  versions: /.*/,
  baseClass: "Semantic.Html.Field", // inherited from Field
  properties: {
    skipInline: { type: "bool", initialValue: false }
  }
}, function () {
  function _class85(meta) {
    _classCallCheck(this, _class85);

    QmlWeb.callSuper(this, meta);
    this.baseClassName = "";
    this.suffixClassName = "fields";
  }

  return _class85;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Form",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    inline: "bool",
    inlineWidth: "int",
    textAlign: "string",
    validateSetting: "var"
  },
  signals: {
    valid: [],
    invalid: [],
    success: [{ type: "var", name: "event" }, { type: "var", name: "fields" }],
    failure: [{ type: "var", name: "formErrors" }, { type: "var", name: "fields" }]
  }
}, function () {
  function _class86(meta) {
    _classCallCheck(this, _class86);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.validateSettingChanged.connect(this, this.$onValidateSettingChanged);
    this.suffixClassName = "form";
    this.setting = {
      onValid: this._onValid.bind(this),
      onInvalid: this._onInvalid.bind(this),
      onSuccess: this._onSuccess.bind(this),
      onFailure: this._onFailure.bind(this)
    };

    this.validateSetting = {};
  }

  _createClass(_class86, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var child_fields = this.$findChildField(this.children);
      this.$applyLabelInline(child_fields);
      $(this.dom).form(this.setting);
    }
  }, {
    key: "_onValid",
    value: function _onValid() {
      this.valid();
    }
  }, {
    key: "_onInvalid",
    value: function _onInvalid() {
      this.invalid();
    }
  }, {
    key: "_onSuccess",
    value: function _onSuccess(event, fields) {
      this.success.apply(this, arguments);
    }
  }, {
    key: "_onFailure",
    value: function _onFailure(formErrors, fields) {
      this.failure.apply(this, arguments);
    }
  }, {
    key: "$onValidateSettingChanged",
    value: function $onValidateSettingChanged() {
      Object.assign(this.setting, this.validateSetting);
      $(this.dom).form(this.setting);
    }
  }, {
    key: "$findChildField",
    value: function $findChildField(children) {
      return children.filter(function (child) {
        return child.dom.classList.contains("field") || child.dom.classList.contains("fields");
      });
    }
  }, {
    key: "$applyLabelInline",
    value: function $applyLabelInline(fields) {
      if (this.inline) {
        var _iteratorNormalCompletion6 = true;
        var _didIteratorError6 = false;
        var _iteratorError6 = undefined;

        try {
          for (var _iterator6 = fields[Symbol.iterator](), _step6; !(_iteratorNormalCompletion6 = (_step6 = _iterator6.next()).done); _iteratorNormalCompletion6 = true) {
            var f = _step6.value;

            if (f.skipInline) {
              continue;
            } else {
              f.dom.classList.add("inline");
            }

            var label = $(f.dom).find("label");

            if (this.inlineWidth && f.dom.classList.contains("inline") && label && label[0].innerHTML != "&nbsp;") {
              label[0].style.width = this.inlineWidth + "px";
              label[0].style.textAlign = this.textAlign;
            }

            this.$applyLabelInline(this.$findChildField(f.children));
          }
        } catch (err) {
          _didIteratorError6 = true;
          _iteratorError6 = err;
        } finally {
          try {
            if (!_iteratorNormalCompletion6 && _iterator6.return) {
              _iterator6.return();
            }
          } finally {
            if (_didIteratorError6) {
              throw _iteratorError6;
            }
          }
        }
      }
    }

    //**************************** public method *******************************

    // Returns true/false whether a form passes its validation rules

  }, {
    key: "isValid",
    value: function isValid() {
      return $(this.dom).form('is valid');
    }

    // Validates form and calls onSuccess or onFailure

  }, {
    key: "validateForm",
    value: function validateForm() {
      $(this.dom).form('validate form');
    }

    // Returns element with matching name, id, or data- validate metadata to ID

  }, {
    key: "getField",
    value: function getField(identifier) {
      return $(this.dom).form('get field', identifier);
    }

    // Returns value of element with id

  }, {
    key: "getValue",
    value: function getValue(id) {
      return $(this.dom).form('get value', id);
    }

    // Returns object of element values that match array of ids.If no IDS are passed will return all fields

  }, {
    key: "getValues",
    value: function getValues(ids) {
      return $(this.dom).form('get values', ids);
    }

    // Sets value of element with id

  }, {
    key: "setValue",
    value: function setValue(id) {
      $(this.dom).form('set value', id);
    }

    // Sets key/ value pairs from passed values object to matching ids

  }, {
    key: "setValues",
    value: function setValues(target) {
      $(this.dom).form('set values', target);
    }

    // Returns validation rules for a given jQuery- referenced input field

  }, {
    key: "getValidation",
    value: function getValidation(target) {
      var $target = target.dom ? $(target.dom) : target;
      return $(this.dom).form('get validation', $target);
    }

    // Returns whether a field exists

  }, {
    key: "hasField",
    value: function hasField(target) {
      return $(this.dom).form('has field', $target);
    }
  }, {
    key: "getFieldLabel",
    value: function getFieldLabel(name, ctx, props) {
      var $field = this.getField(name);
      var $label = $field.closest('.field').find('label').eq(0);
      var label = $label.length == 1 ? $label.text() : $field.prop('placeholder');
      if (label == '') {
        var prop = props[name];
        if (prop && prop.type == "alias") {
          var qmlField = ctx[prop.val.objectName];
          label = qmlField.doc_label;
        }
      }
      return label;
    }

    /** Auto set `dataValidate` to all fields inside Form that are alias in RestModel
        this should be called from `Component.onCompleted` of RestModel
         Example:
        RestModel {
            property alias first_name: txtFirstName.text
            Component.onCompleted: {
                form.setupValidate($context, $properties);
            }
            onFailed: {
                form.showError(error, $context, $properties);
            }
        }
        Form {
            id: form
            TextBox {
                id: txtFirstName
            }
        }
    **/

  }, {
    key: "setupValidate",
    value: function setupValidate(ctx, props) {
      for (var key in props) {
        var prop = props[key];
        if (prop.type == "alias") {
          var field = ctx[prop.val.objectName];
          field.dataValidate = key;
        }
      }
    }

    // Set error state to field
    //param - err = {
    //   'identifier': { ['Error message 1', 'Error message 2'],
    //   'identifier2': ['Error message 1', 'Error message 2'],
    // }
    // identifier = value from dataValidate

  }, {
    key: "showError",
    value: function showError() {
      var err = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
      var ctx = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
      var props = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {};

      var message = void 0,
          allErrors = [],
          $form = $(this.dom),
          keys = Object.keys(err);

      var _iteratorNormalCompletion7 = true;
      var _didIteratorError7 = false;
      var _iteratorError7 = undefined;

      try {
        for (var _iterator7 = keys[Symbol.iterator](), _step7; !(_iteratorNormalCompletion7 = (_step7 = _iterator7.next()).done); _iteratorNormalCompletion7 = true) {
          var name = _step7.value;

          messages = err[name];
          if (this.validateSetting.inline) {
            messages = messages.join(".<br>");
          } else {
            var label = this.getFieldLabel(name, ctx, props) || name;
            var list = "<ul><b>" + label + "</b>";
            var _iteratorNormalCompletion8 = true;
            var _didIteratorError8 = false;
            var _iteratorError8 = undefined;

            try {
              for (var _iterator8 = messages[Symbol.iterator](), _step8; !(_iteratorNormalCompletion8 = (_step8 = _iterator8.next()).done); _iteratorNormalCompletion8 = true) {
                message = _step8.value;

                list += "<li>" + message + "</li>";
              }
            } catch (err) {
              _didIteratorError8 = true;
              _iteratorError8 = err;
            } finally {
              try {
                if (!_iteratorNormalCompletion8 && _iterator8.return) {
                  _iterator8.return();
                }
              } finally {
                if (_didIteratorError8) {
                  throw _iteratorError8;
                }
              }
            }

            list += '</ul>';
            allErrors.push(list);
          }

          $form.form("add prompt", name, messages);
        }
      } catch (err) {
        _didIteratorError7 = true;
        _iteratorError7 = err;
      } finally {
        try {
          if (!_iteratorNormalCompletion7 && _iterator7.return) {
            _iterator7.return();
          }
        } finally {
          if (_didIteratorError7) {
            throw _iteratorError7;
          }
        }
      }

      $form.form("add errors", allErrors);
    }
  }, {
    key: "clear",
    value: function clear() {
      $(this.dom).form("set success");
      $(this.dom).find(".error:not(.ui.message)").removeClass('error');
    }
  }]);

  return _class86;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Grid",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {}
}, function () {
  function _class87(meta) {
    _classCallCheck(this, _class87);

    QmlWeb.callSuper(this, meta);
    this.baseClassName = "ui";
    this.suffixClassName = "grid";
  }

  return _class87;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Icon",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    icon: "string"
  },
  signals: {
    clicked: []
  }
}, function () {
  function _class88(meta) {
    var _this62 = this;

    _classCallCheck(this, _class88);

    QmlWeb.callSuper(this, meta);
    this.baseClassName = "icon";
    this.dom = document.createElement("i");
    this.iconChanged.connect(this, this.$onIconChanged);
    this.dom.onclick = function () {
      _this62.clicked();
    };
  }

  _createClass(_class88, [{
    key: "$onIconChanged",
    value: function $onIconChanged() {
      this.className = this.icon;
    }
  }]);

  return _class88;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Image",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    source: "string",
    cursor: "string"
  },
  signals: {
    clicked: []
  }
}, function () {
  function _class89(meta) {
    var _this63 = this;

    _classCallCheck(this, _class89);

    QmlWeb.callSuper(this, meta);
    this.sourceChanged.connect(this, this.$onSourceChanged);
    this.cursorChanged.connect(this, this.$onCursorChanged);
    this.suffixClassName = "image";
    this.imageContainer = document.createElement("img");

    this.dom.appendChild(this.imageContainer);
    this.dom.addEventListener('click', function () {
      _this63.clicked();
    });
  }

  _createClass(_class89, [{
    key: "$onCursorChanged",
    value: function $onCursorChanged() {
      this.dom.style.cursor = this.cursor;
    }
  }, {
    key: "$onSourceChanged",
    value: function $onSourceChanged() {
      this.imageContainer.src = this.source;
    }
  }]);

  return _class89;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "ImageButton",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    source: "string",
    text: "string"
  },
  signals: {
    clicked: []
  }
}, function () {
  function _class90(meta) {
    var _this64 = this;

    _classCallCheck(this, _class90);

    QmlWeb.callSuper(this, meta);
    this.sourceChanged.connect(this, this.$onSourceChanged);
    this.textChanged.connect(this, this.$onTextChanged);
    this.classNameChanged.connect(this, this.$onClassNameChanged);
    this.Component.completed.connect(this, this.Component$onCompleted);

    this.$container = $("\n            <div class=\"card\">\n                <div class=\"blurring dimmable image\">\n                    <div class=\"ui dimmer\">\n                        <div class=\"content\">\n                            <div class=\"center\">\n                                <div class=\"ui inverted button\">Upload</div>\n                            </div>\n                        </div>\n                    </div>\n                </div>\n            </div>\n            ");
    this.$imageContainer = $("<div><img></div>");
    this.$imageNode = $(this.$imageContainer).find('img');
    this.$buttonNode = $(this.$container).find('.ui.button');
    this.$dimmableNode = $(this.$container).find('.blurring.dimmable.image');
    this.$dimmableNode.append(this.$imageContainer);
    this.dom.className = "ui special cards";
    this.$container.css('width', 'auto');
    $(this.dom).append(this.$container);

    this.$buttonNode.on('click', function () {
      _this64.clicked();
    });
  }

  _createClass(_class90, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.$dimmableNode.dimmer({
        on: 'hover'
      });
    }
  }, {
    key: "$onSourceChanged",
    value: function $onSourceChanged() {
      this.$imageNode.attr('src', this.source);
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged() {
      this.$buttonNode.html(this.text);
    }

    //override

  }, {
    key: "$onClassNameChanged",
    value: function $onClassNameChanged() {
      this.$imageContainer[0].className = "ui " + this.className + " image";
    }
  }]);

  return _class90;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "InnerMenu",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {},
  signals: {}
}, function () {
  function _class91(meta) {
    _classCallCheck(this, _class91);

    QmlWeb.callSuper(this, meta);
    this.baseClassName = "";
    this.suffixClassName = "menu";
  }

  return _class91;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Item",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom"
}, function () {
  function _class92(meta) {
    _classCallCheck(this, _class92);

    QmlWeb.callSuper(this, meta);
    this.suffixClassName = "item";
  }

  return _class92;
}());

{
  var LabelTag = function () {
    function LabelTag(meta) {
      var _this65 = this;

      _classCallCheck(this, LabelTag);

      QmlWeb.callSuper(this, meta);
      this.Component.completed.connect(this, this.Component$onCompleted);
      this.textChanged.connect(this, this.$onTextChanged);
      this.iconChanged.connect(this, this.$onIconChanged);
      this.backgroundColorChanged.connect(this, this.$onBackgroundColorChanged);
      this.sizeChanged.connect(this, this.$onSizeChanged);
      this.tagChanged.connect(this, this.$onTagChanged);
      this.basicChanged.connect(this, this.$onBasicChanged);
      this.circularChanged.connect(this, this.$onCircularChanged);
      this.linkChanged.connect(this, this.$onLinkChanged);
      this.floatingChanged.connect(this, this.$onFloatingChanged);

      this.suffixClassName = "label";
      this.dom.style.pointerEvents = "auto";
      this.dom = this.dom;

      this.dom.onclick = function () {
        _this65.clicked();
      };
    }

    _createClass(LabelTag, [{
      key: "Component$onCompleted",
      value: function Component$onCompleted() {
        this.implicitWidth = this.dom.offsetWidth;
        this.implicitHeight = this.dom.offsetHeight;
      }
    }, {
      key: "validateProperty",
      value: function validateProperty(prop) {
        if (prop || prop === "") {
          // prevent error from undefined prop and allow property ""
          prop = prop.toLowerCase();
          if (LabelTag.backgroundColor.includes(prop) || LabelTag.size.includes(prop)) {
            return [true, "" + prop];
          }
        }
        return [false, ""];
      }
    }, {
      key: "$onTextChanged",
      value: function $onTextChanged() {
        this.dom.innerHTML = this.text;
        this.changed();
      }
    }, {
      key: "$onIconChanged",
      value: function $onIconChanged() {
        this.iconNode = document.createElement("i");
        this.iconNode.classList.add("" + this.icon, "icon");
        this.dom.innerHTML = "";
        this.dom.insertAdjacentElement("beforeend", this.iconNode);
        if (this.text !== "") this.dom.insertAdjacentText("afterbegin", this.text);
      }
    }, {
      key: "$onBackgroundColorChanged",
      value: function $onBackgroundColorChanged() {
        var _validateProperty9 = this.validateProperty(this.backgroundColor),
            _validateProperty10 = _slicedToArray(_validateProperty9, 2),
            pass = _validateProperty10[0],
            css = _validateProperty10[1];

        if (!pass) return;
        this.dom.classList.remove("" + this._backgroundColor);
        if (!css) return; // return if css is "" prevent error when call classList.add with ""
        this.dom.classList.add(css);
        this._backgroundColor = this.backgroundColor;
      }
    }, {
      key: "$onSizeChanged",
      value: function $onSizeChanged() {
        var _validateProperty11 = this.validateProperty(this.size),
            _validateProperty12 = _slicedToArray(_validateProperty11, 2),
            pass = _validateProperty12[0],
            css = _validateProperty12[1];

        if (!pass) return;
        this.dom.classList.remove("" + this._size);
        this.dom.classList.add(css);
        this._size = this.size;
      }
    }, {
      key: "$onTagChanged",
      value: function $onTagChanged() {
        this.dom.classList.remove("tag");
        if (this.tag) this.dom.classList.add("tag");
      }
    }, {
      key: "$onBasicChanged",
      value: function $onBasicChanged() {
        this.dom.classList.remove("basic");
        if (this.basic) this.dom.classList.add("basic");
      }
    }, {
      key: "$onCircularChanged",
      value: function $onCircularChanged() {
        this.dom.classList.remove("circular");
        if (this.circular) this.dom.classList.add("circular");
      }
    }, {
      key: "$onLinkChanged",
      value: function $onLinkChanged() {
        var _this66 = this;

        var old_label = this.dom;
        this.dom = document.createElement("a");
        this.dom.classList = old_label.classList;
        this.dom.innerHTML = old_label.innerHTML;
        old_label.remove();
        this.dom.onclick = function () {
          _this66.clicked();
        };
      }
    }, {
      key: "$onFloatingChanged",
      value: function $onFloatingChanged() {
        this.dom.classList.remove("floating");
        if (this.floating) this.dom.classList.add("floating");
      }
    }]);

    return LabelTag;
  }();

  LabelTag.backgroundColor = ["", "red", "orange", "yellow", "olive", "green", "teal", "blue", "violet", "purple", "pink", "brown", "grey", "black"];

  LabelTag.size = ["mini", "tiny", "small", "medium", "large", "big", "huge", "massive"];

  QmlWeb.registerQmlType({
    module: "Semantic.Html",
    name: "LabelTag",
    versions: /.*/,
    baseClass: "Semantic.Html.Dom",
    properties: {
      text: "string",
      icon: "string",
      size: "string",
      backgroundColor: "string",
      basic: "bool",
      tag: "bool",
      circular: "bool",
      link: "bool",
      floating: "bool"
    },
    signals: {
      clicked: [],
      changed: []
    }
  }, LabelTag);
}

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Link",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    href: "string",
    text: "string"
  },
  signals: {
    clicked: []
  }
}, function () {
  function _class93(meta) {
    _classCallCheck(this, _class93);

    meta.object.tagName = "a";
    QmlWeb.callSuper(this, meta);
    this.textChanged.connect(this, this.$onTextChanged);
    this.dom.style.cursor = "pointer";
    $(this.dom).on('click', this.onClick.bind(this));
  }

  _createClass(_class93, [{
    key: "onClick",
    value: function onClick() {
      this.clicked();
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged() {
      $(this.dom).html(this.text);
    }
  }]);

  return _class93;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "ListElement",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom"
}, function () {
  function _class94(meta) {
    _classCallCheck(this, _class94);

    QmlWeb.callSuper(this, meta);

    var createProperty = QmlWeb.createProperty;
    for (var i in meta.object) {
      if (i[0] !== "$") {
        createProperty("variant", this, i);
      }
    }
    QmlWeb.applyProperties(meta.object, this, this, this.$context);
  }

  return _class94;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "ListModel",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    count: "int",
    $items: "list",
    model: "var"
  },
  defaultProperty: "$items",
  signals: {
    changed: []
  }
}, function () {
  function _class95(meta) {
    var _this67 = this;

    _classCallCheck(this, _class95);

    QmlWeb.callSuper(this, meta);

    this.$firstItem = true;
    this.$itemsChanged.connect(this, this.$on$itemsChanged);
    this.modelChanged.connect(this, this.$onModelChanged);
    this.$model = new QmlWeb.JSItemModel();
    this.$model.data = function (index, role) {
      return _this67.$items[index][role];
    };
    this.$model.rowCount = function () {
      return _this67.$items.length;
    };
  }

  _createClass(_class95, [{
    key: "$onModelChanged",
    value: function $onModelChanged() {
      // Use ListModel with property model
      this.$items = [];
      if (this.model.length > 0) {
        var c = 0;
        var roleNames = [];
        if (this.model instanceof Array) {
          for (var key in this.model) {
            this.$items.push(this.model[key]);
            c++;
          }
        } else {
          this.$items.push(this.model);
          c = 1;
        }
        for (var i in this.model[0]) {
          if (i !== "index") {
            roleNames.push(i);
          }
        }
        this.$model.setRoleNames(roleNames);
      }
      this.count = this.$items.length;
      this.changed();
    }
  }, {
    key: "$on$itemsChanged",
    value: function $on$itemsChanged(newVal) {
      // Use ListModel with ListElement
      this.count = this.$items.length;
      if (this.$firstItem && newVal.length > 0) {
        var QMLListElement = QmlWeb.getConstructor("Semantic.Html", "2.0", "ListElement");
        this.$firstItem = false;
        var roleNames = [];
        var dict = newVal[0];
        if (dict instanceof QMLListElement) {
          dict = dict.$properties;
        }
        for (var i in dict) {
          if (i !== "index") {
            roleNames.push(i);
          }
        }
        this.$model.setRoleNames(roleNames);
      }
    }
  }, {
    key: "append",
    value: function append(dict) {
      var index = this.$items.length;
      var c = 0;

      if (dict instanceof Array) {
        for (var key in dict) {
          this.$items.push(dict[key]);
          this.model.push(dict[key]);
          c++;
        }
      } else {
        this.$items.push(dict);
        this.model.push(dict);
        c = 1;
      }
      this.$itemsChanged(this.$items);
      this.$model.rowsInserted(index, index + c);
    }
  }, {
    key: "clear",
    value: function clear() {
      this.$items.length = 0;
      this.count = 0;
      this.$model.modelReset();
    }
  }, {
    key: "get",
    value: function get(index) {
      return this.$items[index];
    }
  }, {
    key: "insert",
    value: function insert(index, dict) {
      this.$items.splice(index, 0, dict);
      this.$itemsChanged(this.$items);
      this.$model.rowsInserted(index, index + 1);
    }
  }, {
    key: "move",
    value: function move(from, to, n) {
      var vals = this.$items.splice(from, n);
      for (var i = 0; i < vals.length; i++) {
        this.$items.splice(to + i, 0, vals[i]);
      }
      this.$model.rowsMoved(from, from + n, to);
    }
  }, {
    key: "remove",
    value: function remove(index) {
      this.$items.splice(index, 1);
      this.model.splice(index, 1);
      this.$model.rowsRemoved(index, index + 1);
      this.count = this.$items.length;
    }
  }, {
    key: "set",
    value: function set(index, dict) {
      this.$items[index] = dict;
      this.model[index] = dict;
      this.$model.dataChanged(index, index);
    }
  }, {
    key: "updateItem",
    value: function updateItem(index, property, value) {
      this.setProperty(index, property, value);
    }
  }, {
    key: "setProperty",
    value: function setProperty(index, property, value) {
      this.$items[index][property] = value;
      this.$model.dataChanged(index, index);
    }
  }]);

  return _class95;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Loader",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    active: { type: "bool", initialValue: false },
    asynchronous: "bool",
    item: "var",
    progress: "real",
    source: "url",
    sourceComponent: "Component",
    status: { type: "enum", initialValue: 1 }
  },
  defaultProperty: "sourceComponent",
  signals: {
    loaded: []
  }
}, function () {
  function _class96(meta) {
    _classCallCheck(this, _class96);

    QmlWeb.callSuper(this, meta);
    this.meta = meta;
    this.$sourceUrl = "";

    this.activeChanged.connect(this, this.$onActiveChanged);
    this.sourceChanged.connect(this, this.$onSourceChanged);
    this.sourceComponentChanged.connect(this, this.$onSourceComponentChanged);
  }

  _createClass(_class96, [{
    key: "$onActiveChanged",
    value: function $onActiveChanged() {
      if (!this.active) {
        this.$unload();
        return;
      }
      if (this.$sourceUrl) {
        this.$onSourceChanged(this.source);
      } else if (this.sourceComponent) {
        this.$onSourceComponentChanged(this.sourceComponent);
      }
    }
  }, {
    key: "$onSourceChanged",
    value: function $onSourceChanged(fileName) {
      // TODO
      // if (fileName == this.$sourceUrl && this.item !== undefined) return;
      if (!this.active) return;
      this.$unload();

      var tree = QmlWeb.engine.loadComponent(fileName);
      var QMLComponent = QmlWeb.getConstructor("QtQml", "2.0", "Component");
      var meta = { object: tree, context: this, parent: this };
      var qmlComponent = new QMLComponent(meta);
      qmlComponent.$basePath = QmlWeb.engine.extractBasePath(tree.$file);
      qmlComponent.$imports = tree.$imports;
      qmlComponent.$file = tree.$file;
      QmlWeb.engine.loadImports(tree.$imports, qmlComponent.$basePath, qmlComponent.importContextId);
      var loadedComponent = this.$createComponentObject(qmlComponent, this);
      this.$sourceUrl = fileName;
      this.sourceComponent = loadedComponent;
    }
  }, {
    key: "$onSourceComponentChanged",
    value: function $onSourceComponentChanged() {
      var _this68 = this;

      if (!this.active) return;
      this.$unload();

      var newItem = this.sourceComponent.$createObject();

      // Prevent id of item from sourceUrl included on rootComtext
      if (!this.$sourceUrl) {
        // To add newItem to rootComtext
        var rootContext = QmlWeb.engine.rootContext();
        rootContext[newItem.id] = newItem;
      }

      // To properly import JavaScript in the context of a component
      this.sourceComponent.finalizeImports();

      this.item = newItem;

      if (QmlWeb.engine.operationState !== QMLOperationState.Init && QmlWeb.engine.operationState !== QMLOperationState.Idle) {
        this.$callOnCompleted(newItem);
      }

      if (QmlWeb.engine.operationState !== QMLOperationState.Init) {
        QmlWeb.engine.$initializePropertyBindings();
      }

      newItem.parent = this;
      $(document).ready(function () {
        return _this68.loaded();
      });
    }
  }, {
    key: "setSource",
    value: function setSource(url, options) {
      this.$sourceUrl = url;
      this.props = options;
      this.source = url;
    }
    // Handle with Modal to load and show

  }, {
    key: "loadAndShowModal",
    value: function loadAndShowModal() {
      if (typeof this.item !== "undefined") this.item.show();
      this.active = true;
      // TODO: Add this.item.show() to this.loaded
    }
  }, {
    key: "$unload",
    value: function $unload() {
      if (!this.item) return;
      var rootContext = QmlWeb.engine.rootContext();
      rootContext[this.item.id] = null;
      this.item.$delete();
      this.item.parent = undefined;
      this.item = undefined;
    }
  }, {
    key: "$callOnCompleted",
    value: function $callOnCompleted(child) {
      child.Component.completed();
      var QMLBaseObject = QmlWeb.getConstructor("QtQml", "2.0", "QtObject");
      for (var i = 0; i < child.$tidyupList.length; i++) {
        if (child.$tidyupList[i] instanceof QMLBaseObject) {
          this.$callOnCompleted(child.$tidyupList[i]);
        }
      }
    }
  }, {
    key: "$createComponentObject",
    value: function $createComponentObject(qmlComponent, parent) {
      var newComponent = qmlComponent.createObject(parent);
      qmlComponent.finalizeImports();
      if (QmlWeb.engine.operationState !== QmlWeb.QMLOperationState.Init) {
        // We don't call those on first creation, as they will be called
        // by the regular creation-procedures at the right time.
        QmlWeb.engine.$initializePropertyBindings();
        this.$callOnCompleted(newComponent);
      }
      return newComponent;
    }
  }]);

  return _class96;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Menu",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    selectedTab: "string"
  },
  signals: {
    changed: [{ type: "string", name: "selected" }]
  }
}, function () {
  function _class97(meta) {
    _classCallCheck(this, _class97);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.selectedTabChanged.connect(this, this.$onSelectedTabChanged);
    this.baseClassName = "ui";
    this.suffixClassName = "menu";
  }

  _createClass(_class97, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.$menuItem = $(this.dom).find("a.item, .link.item");
      this.handler = {
        activate: function activate(evt) {
          this.selectedTab = evt.target.getAttribute("data-tab");
          var activeAll = $(evt.target).attr("data-active-all");
          if (activeAll) {
            $(this.dom).parent().find(".ui.tab").addClass("active");

            $(this.dom).find(".item").not($(evt.target)).removeClass("active");
          }
          this.changed(this.selectedTab);
        }
      };
      this.enableBinding = true;
      this.bindClickEvent();
      //call method that can't do until component complete
      this.$onSelectedTabChanged();
    }
  }, {
    key: "refresh",
    value: function refresh() {
      this.bindClickEvent();
      this.$onSelectedTabChanged();
    }
  }, {
    key: "bindClickEvent",
    value: function bindClickEvent() {
      if (!this.enableBinding) return;

      this.$menuItem.off("click", this.handler.activate.bind(this));
      this.$menuItem = $(this.dom).find("a.item, .link.item");
      this.$menuItem.on("click", this.handler.activate.bind(this));
    }
  }, {
    key: "$onSelectedTabChanged",
    value: function $onSelectedTabChanged() {
      if (this.bySystem) return;

      if (!this.selectedTab) return;

      var activeMenu = "a.item[data-tab=\"" + this.selectedTab + "\"], .link.item[data-tab=\"" + this.selectedTab + "\"]";
      $(this.dom).find("a.item, .link.item").removeClass("active");
      $(this.dom).parent().find(".ui.tab").removeClass("active");
      $(this.dom).find(activeMenu).addClass("active");
      $(this.dom).parent().find(".ui.tab[data-tab=\"" + this.selectedTab + "\"]").addClass('active');

      var tabContent = $(".ui.segment[data-tab=\"" + this.selectedTab + "\"],\n                        .ui.segments[data-tab=\"" + this.selectedTab + "\"]");

      if (tabContent.get(0)) {
        $(document.body).trigger("resizeDgrid", [{ dom: tabContent }]);
      }
    }
  }]);

  return _class97;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "MenuItem",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    dataTab: "string",
    activeAll: "bool"
  },
  signals: {
    clicked: []
  }
}, function () {
  function _class98(meta) {
    var _this69 = this;

    _classCallCheck(this, _class98);

    meta.object.tagName = "a";
    QmlWeb.callSuper(this, meta);
    this.dataTabChanged.connect(this, this.$onDataTabChanged);
    this.activeAllChanged.connect(this, this.$onActiveAllChanged);
    this.baseClassName = "";
    this.suffixClassName = "item";

    this.dom.addEventListener("click", function () {
      return _this69.clicked();
    });
  }

  _createClass(_class98, [{
    key: "$onDataTabChanged",
    value: function $onDataTabChanged() {
      this.dom.setAttribute("data-tab", this.dataTab);
    }
  }, {
    key: "$onActiveAllChanged",
    value: function $onActiveAllChanged() {
      $(this.dom).attr('data-active-all', this.activeAll);
    }
  }]);

  return _class98;
}());

{
  var _BACKGROUNDCOLOR2 = ['red', 'orange', 'yellow', 'olive', 'green', 'teal', 'blue', 'violet', 'purple', 'pink', 'brown', 'grey', 'black'];

  QmlWeb.registerQmlType({
    module: "Semantic.Html",
    name: "Message",
    versions: /.*/,
    baseClass: "Semantic.Html.Dom",
    properties: {
      icon: "string",
      spinning: "bool",
      dismissable: "bool",
      backgroundColor: "string"
    }
  }, function () {
    function _class99(meta) {
      _classCallCheck(this, _class99);

      QmlWeb.callSuper(this, meta);
      this.Component.completed.connect(this, this.Component$onCompleted);
      this.iconChanged.connect(this, this.$onIconChanged);
      this.spinningChanged.connect(this, this.$onSpinningChanged);
      this.dismissableChanged.connect(this, this.$onDismissableChanged);
      this.backgroundColorChanged.connect(this, this.$onBackgroundColorChanged);
      this.suffixClassName = "message";
      this.contentNode = document.createElement("div");
      this.contentNode.classList.add("content");
      this.iconNode = document.createElement("i");
    }

    _createClass(_class99, [{
      key: "Component$onCompleted",
      value: function Component$onCompleted() {
        //Move all dom's childNodes to contentNode 
        while (this.dom.childNodes.length > 0) {
          this.contentNode.appendChild(this.dom.childNodes[0]);
        }

        this.dom.appendChild(this.iconNode);
        this.dom.appendChild(this.contentNode);
      }
    }, {
      key: "$onIconChanged",
      value: function $onIconChanged() {
        var icon = this.icon.split(" ");
        this.iconNode.className = "";
        this.iconNode.classList.add("icon");

        if (this.dismissable) {
          this.iconNode.classList.add("close");
        } else {
          var _iconNode$classList;

          (_iconNode$classList = this.iconNode.classList).add.apply(_iconNode$classList, _toConsumableArray(icon));
        }

        this.spinning && this.iconNode.classList.add("loading");
        this.icon && this.dom.classList.add("icon");
      }
    }, {
      key: "$onSpinningChanged",
      value: function $onSpinningChanged() {
        var iconClassList = this.iconNode.classList;
        if (this.spinning) {
          !iconClassList.contains("loading") && iconClassList.add("loading");
        } else {
          iconClassList.remove("loading");
        }
      }
    }, {
      key: "$onDismissableChanged",
      value: function $onDismissableChanged() {
        //there is a bug here
        //when set dismissable to true it can't be set to false
        this.iconNode.className = "";
        this.iconNode.classList.add("close", "icon");

        $(document).ready(function () {
          $('.message .close').on('click', function () {
            $(this).closest('.message').transition('fade');
          });
        });
      }
    }, {
      key: "$onBackgroundColorChanged",
      value: function $onBackgroundColorChanged() {
        var classList = this.dom.classList;

        this.dom.style.backgroundColor = "";
        this._backgroundColor && classList.remove(this._backgroundColor);
        if (_BACKGROUNDCOLOR2.includes(this.backgroundColor)) {
          classList.add(this.backgroundColor);
        } else {
          this.dom.style.backgroundColor = this.backgroundColor;
        }
        this._backgroundColor = this.backgroundColor;
      }
    }]);

    return _class99;
  }());
}
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Modal",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    autofocus: { type: "bool", initialValue: false },
    allowMultiple: { type: "bool", initialValue: true },
    duration: { type: "int", initialValue: 200 },
    closable: { type: "bool", initialValue: true }
  },
  signals: {
    hidden: [],
    showed: []
  }
}, function () {
  function _class100(meta) {
    _classCallCheck(this, _class100);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.suffixClassName = "modal";
  }

  _createClass(_class100, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var _this70 = this;

      $(document).ready(function () {
        $(_this70.dom).modal({
          onVisible: _this70.onVisible.bind(_this70),
          onHidden: _this70.hidden,
          autofocus: _this70.autofocus,
          allowMultiple: _this70.allowMultiple,
          duration: _this70.duration,
          closable: _this70.closable
        });
      });
    }
  }, {
    key: "onVisible",
    value: function onVisible() {
      document.body.dispatchEvent(new CustomEvent("resizeDgrid", {
        detail: {
          dom: this.dom
        }
      }));
      this.showed();
    }
  }, {
    key: "show",
    value: function show() {
      $(this.dom).modal("show");
    }
  }, {
    key: "hide",
    value: function hide() {
      $(this.dom).modal("hide");
    }
  }, {
    key: "setActive",
    value: function setActive() {
      $(this.dom).model("set active");
    }
  }, {
    key: "isActive",
    value: function isActive() {
      return $(this.dom).modal("is active");
    }
  }, {
    key: "refresh",
    value: function refresh() {
      $(this.dom).modal("refresh");
    }
  }]);

  return _class100;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Popup",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    text: "string",
    inline: "bool",
    target: "var",
    position: "string",
    boundary: "var",
    hoverable: { type: "bool", initialValue: false },
    activeEvent: { type: "string", initialValue: "hover" }
  }
}, function () {
  function _class101(meta) {
    _classCallCheck(this, _class101);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.textChanged.connect(this, this.$onTextChanged);
    this.targetChanged.connect(this, this.$onTargetChanged);
    this.boundaryChanged.connect(this, this.$onBoundaryChanged);
    this.positionChanged.connect(this, this.$onPositionChanged);
    this.activeEventChanged.connect(this, this.$onActiveEventChanged);
    this.suffixClassName = "popup";

    this.settings = {
      popup: $(this.dom),
      onUnplaceable: this.onUnplaceable.bind(this)
    };
  }

  _createClass(_class101, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var _this71 = this;

      this.settings.hoverable = this.hoverable;
      $(document).ready(function () {
        return $(_this71.getTarget()).popup(_this71.settings);
      });
    }
  }, {
    key: "onUnplaceable",
    value: function onUnplaceable() {
      console.error("Plaese increase the height of grid (if you are using DGrid)");
    }
  }, {
    key: "$onTargetChanged",
    value: function $onTargetChanged() {
      var _this72 = this;

      $(document).ready(function () {
        var target = _this72.getTarget();
        if (!target) return;
        $(target).popup(_this72.settings);
      });
    }
  }, {
    key: "$onBoundaryChanged",
    value: function $onBoundaryChanged() {
      var target = this.getTarget();
      var notNull = !!this.boundary;
      var hasDom = notNull && this.boundary.hasOwnProperty("dom");
      var isGrid = hasDom && this.boundary.dom.classList.contains("dgrid-grid");

      if (notNull) {
        this.settings.boundary = this.boundary.dom || window;
      }
      if (notNull && hasDom && isGrid) {
        this.settings.boundary = $(this.boundary.dom).find('.dgrid-scroller');
      }
      target && $(target).popup(this.settings);
    }
  }, {
    key: "getTarget",
    value: function getTarget() {
      if (this.target && this.target.hasOwnProperty("dom")) return this.target.dom;
      if (this.parent && this.parent.hasOwnProperty("dom")) return this.parent.dom;
    }
  }, {
    key: "show",
    value: function show() {
      $(this.getTarget()).popup("show");
    }
  }, {
    key: "show",
    value: function show() {
      $(this.getTarget()).popup("hide");
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged() {
      this.dom.appendChild(document.createTextNode(this.text));
    }
  }, {
    key: "$onPositionChanged",
    value: function $onPositionChanged() {
      var _this73 = this;

      $(document).ready(function () {
        var target = _this73.getTarget();
        var availablePositions = ["top left", "top center", "top right", "bottom left", "bottom center", "bottom right", "right center", "left center"];
        if (!target) return;
        if (!availablePositions.includes(_this73.position)) return;
        target.setAttribute("data-position", _this73.position);
        $(document).ready(function () {
          return $(target).popup(_this73.settings);
        });
      });
    }
  }, {
    key: "$onActiveEventChanged",
    value: function $onActiveEventChanged() {
      var _this74 = this;

      $(document).ready(function () {
        //workaround for fixing couldn't find parent
        var target = _this74.getTarget();
        if (!target) return;
        var availableEvents = ["focus", "click", "hover", "manual"];
        if (availableEvents.includes(_this74.activeEvent)) {
          _this74.settings.on = _this74.activeEvent;
          $(target).popup(_this74.settings);
        }
      });
    }
  }]);

  return _class101;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "RadioButton",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    value: "var",
    checked: "bool",
    readOnly: "bool",
    text: "string",
    color: "string",
    group: "string",
    fitted: "bool",
    type: "string",
    dataValidate: "string",
    enabled: { type: "bool", initialValue: true }
  },
  signals: {
    changed: [{ name: "event", type: "var" }, { name: "value", type: "var" }]
  }
}, function () {
  function _class102(meta) {
    var _this75 = this;

    _classCallCheck(this, _class102);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.valueChanged.connect(this, this.$onValueChanged);
    this.checkedChanged.connect(this, this.$onCheckedChanged);
    this.textChanged.connect(this, this.$onTextChanged);
    this.enabledChanged.connect(this, this.$onEnabledChanged);
    this.readOnlyChanged.connect(this, this.$onReadOnlyChanged);
    this.colorChanged.connect(this, this.$onColorChanged);
    this.groupChanged.connect(this, this.$onGroupChanged);
    this.fittedChanged.connect(this, this.$onFittedChanged);
    this.typeChanged.connect(this, this.$onTypeChanged);
    this.dataValidateChanged.connect(this, this.$onDataValidateChanged);

    this._lastType = "radio";
    this.radioContainer = document.createElement("div");
    this.radio = document.createElement("input");
    this.label = document.createElement("label");
    this.radioContainer.classList.add("ui", this._lastType, "checkbox");
    this.radio.type = "radio";
    this.radio.value = null;
    this.radioContainer.appendChild(this.radio);
    this.radioContainer.appendChild(this.label);
    this.dom = this.radioContainer;

    $(this.radio).on("checkedChanged", function () {
      return _this75.onCheckChanged();
    });
    $(this.radio).on("readonlyChanged", function (evt, readonly) {
      _this75.readOnly = readonly;
    });
    $(this.radio).on("enabledChanged", function (evt, enabled) {
      _this75.enabled = enabled;
    });
    $(this.radio).on("onRadioClear", function () {
      _this75.checked = false;
    });

    this.radio.onchange = function (event) {
      $.each($("input[name=" + _this75.group + "]:radio"), function (index, dom) {
        if (!_this75.dom.contains(dom)) {
          $(dom).trigger("checkedChanged");
        }
      });
      _this75.onCheckChanged();
      _this75.changed(event, _this75.radio.value);
    };
  }

  _createClass(_class102, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      $(document).ready(function () {
        return $(".ui.radio.checkbox").checkbox();
      });
    }

    //override

  }, {
    key: "$onHtmlIDChanged",
    value: function $onHtmlIDChanged() {
      this.radio.id = this.htmlID;
    }
  }, {
    key: "$onDataValidateChanged",
    value: function $onDataValidateChanged() {
      this.radio.setAttribute("data-validate", this.dataValidate);
    }
  }, {
    key: "$onValueChanged",
    value: function $onValueChanged() {
      this.radio.value = this.value;
    }
  }, {
    key: "$onCheckedChanged",
    value: function $onCheckedChanged() {
      if (!this.bySystem) this.radio.checked = this.checked;
    }
  }, {
    key: "onCheckChanged",
    value: function onCheckChanged() {
      this.bySystem = true;
      this.checked = this.radio.checked;
      this.bySystem = false;
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged() {
      this.label.innerHTML = this.text;
    }
  }, {
    key: "$onEnabledChanged",
    value: function $onEnabledChanged() {
      this.radioContainer.classList.remove("disabled");
      if (!this.enabled) this.radioContainer.classList.add("disabled");
    }
  }, {
    key: "$onReadOnlyChanged",
    value: function $onReadOnlyChanged() {
      this.radioContainer.classList.remove("read-only");
      if (this.readOnly) this.radioContainer.classList.add("read-only");
    }
  }, {
    key: "$onColorChanged",
    value: function $onColorChanged() {
      this.label.style.color = this.color;
    }
  }, {
    key: "$onGroupChanged",
    value: function $onGroupChanged() {
      this.radio.name = this.group;
    }
  }, {
    key: "$onFittedChanged",
    value: function $onFittedChanged() {
      this.radioContainer.classList.remove("fitted");
      if (this.fitted) this.radioContainer.classList.add("fitted");
    }
  }, {
    key: "$onTypeChanged",
    value: function $onTypeChanged() {
      this.radioContainer.classList.remove(this._lastType);
      this.radioContainer.classList.add(this.type);
      this._lastType = this.type;
    }
  }]);

  return _class102;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "RadioGroup",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    value: "var",
    group: "var",
    readOnly: 'bool',
    enabled: { type: "bool", initialValue: true },
    dataValidate: "string"
  },
  signals: {
    changed: [{ name: "value", type: "var" }, { name: "text", type: "var" }, { name: "bySystem", type: "var" }]
  }
}, function () {
  function _class103(meta) {
    _classCallCheck(this, _class103);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.valueChanged.connect(this, this.$onValueChanged);
    this.groupChanged.connect(this, this.$onGroupChanged);
    this.enabledChanged.connect(this, this.$onEnabledChanged);
    this.readOnlyChanged.connect(this, this.$onReadOnlyChanged);
    this.dataValidateChanged.connect(this, this.$onDataValidateChanged);

    this.input = document.createElement("input");
    this.input.style.display = "none";
    this.dom.appendChild(this.input);
  }

  _createClass(_class103, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.completed = true;
      this.$onGroupChanged();
      this.$onReadOnlyChanged();
      this.$onEnabledChanged();
      this.$onValueChanged();
    }
  }, {
    key: "$onReadOnlyChanged",
    value: function $onReadOnlyChanged() {
      var _this76 = this;

      if (!this.completed) return;

      this.loopThroughRadio(function (index, ele) {
        $(ele).trigger("readonlyChanged", [_this76.readOnly]);
      });
    }
  }, {
    key: "$onEnabledChanged",
    value: function $onEnabledChanged() {
      var _this77 = this;

      if (!this.completed) return;

      this.loopThroughRadio(function (index, ele) {
        $(ele).trigger("enabledChanged", [_this77.enabled]);
      });
    }
  }, {
    key: "$onValueChanged",
    value: function $onValueChanged() {
      if (!this.completed) return;

      if (this.bySystem) return;

      if (!this.group) return;

      var $target = $("input[name='" + this.group + "'][value='" + this.value + "']:radio");
      this.input.value = this.value;

      if (!$target[0]) {
        console.warn("Can't find RadioButton with value: " + this.value + ".");
        return;
      }

      $target[0].checked = true;

      this.loopThroughRadio(function (index, ele) {
        $(ele).trigger("checkedChanged");
      });

      this.changed(this.value, this.text, this.bySystem);
    }
  }, {
    key: "$onGroupChanged",
    value: function $onGroupChanged() {
      var _this78 = this;

      if (!this.completed) return;

      if (!this.group) return;

      this.$radios = this.loopThroughRadio(function (index, ele) {
        if (ele.checked) {
          _this78.bySystem = true;
          _this78.value = ele.value;
          _this78.bySystem = false;
        }
      });

      this.$radios.off('change', this.onRadioCheckedChange.bind(this));
      this.$radios.on('change', this.onRadioCheckedChange.bind(this));
    }
  }, {
    key: "$onDataValidateChanged",
    value: function $onDataValidateChanged() {
      this.input.setAttribute("data-validate", this.dataValidate);
    }
  }, {
    key: "clear",
    value: function clear() {
      this.bySystem = true;
      this.value = "";
      this.loopThroughRadio(function (index, ele) {
        $(ele).trigger("onRadioClear");
      });
      this.bySystem = false;
    }
  }, {
    key: "onRadioCheckedChange",
    value: function onRadioCheckedChange(evt) {
      this.bySystem = true;
      this.value = evt.target.value;
      this.bySystem = false;

      var text = $(evt.target.parentElement).find('label').html();
      this.changed(this.value, text, this.bySystem);
    }
  }, {
    key: "loopThroughRadio",
    value: function loopThroughRadio(cb) {
      var $radios = $("input[name=" + this.group + "]:radio");
      $.each($radios, cb);
      return $radios;
    }
  }]);

  return _class103;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Repeater",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    delegate: "Component",
    model: { type: "variant", initialValue: 0 },
    count: "int",
    placeAfter: "var", // if "first" it will be the first child
    useItemModel: { type: "bool", initialValue: false }
  },
  signals: {
    renderCompleted: []
  },
  defaultProperty: "delegate"
}, function () {
  function _class104(meta) {
    _classCallCheck(this, _class104);

    QmlWeb.callSuper(this, meta);

    this.parent = meta.parent;
    // TODO: some (all ?) of the components including Repeater needs to know own
    // parent at creation time. Please consider this major change.

    this.$completed = false;
    this.$items = []; // List of created items

    this.modelChanged.connect(this, this.$onModelChanged);
    this.delegateChanged.connect(this, this.$onDelegateChanged);
    this.parentChanged.connect(this, this.$onParentChanged);
    this.Component.completed.connect(this, this.Component$onCompleted);

    this.dom.parentNode.removeChild(this.dom);
  }

  _createClass(_class104, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var QMLListModel = QmlWeb.getConstructor("Semantic.Html", "2.0", "ListModel");
      if (this.model instanceof QMLListModel) {
        this.model.changed.connect(this, this.$onModelChanged);
      }
      if (!(this.model || this.$properties['model'].binding)) {
        this.model = new QmlWeb.ItemModel([]);
      }
    }
  }, {
    key: "container",
    value: function container() {
      return this.parent;
    }
  }, {
    key: "itemAt",
    value: function itemAt(index) {
      return this.$items[index];
    }
  }, {
    key: "$onModelChanged",
    value: function $onModelChanged() {
      this.$applyModel();
    }
  }, {
    key: "$onDelegateChanged",
    value: function $onDelegateChanged() {
      this.$applyModel();
    }
  }, {
    key: "$onParentChanged",
    value: function $onParentChanged() {
      this.$applyModel();
    }
  }, {
    key: "$getModel",
    value: function $getModel() {
      var QMLListModel = QmlWeb.getConstructor("Semantic.Html", "2.0", "ListModel");
      if (this.model instanceof Array && this.useItemModel) {
        var newMod = new QmlWeb.ItemModel(this.model);
        var roleNames = [];
        for (var i in this.model[0]) {
          if (i !== "index") {
            roleNames.push(i);
          }
        }
        newMod.setRoleNames(roleNames);
        this.model = newMod;
      }
      return this.model instanceof QMLListModel ? this.model.$model : this.model;
    }
  }, {
    key: "$applyModel",
    value: function $applyModel() {
      if (!this.delegate || !this.parent) {
        return;
      }
      var model = this.$getModel();
      if (model instanceof QmlWeb.JSItemModel || model instanceof QmlWeb.ItemModel) {
        var flags = QmlWeb.Signal.UniqueConnection;
        model.dataChanged.connect(this, this.$_onModelDataChanged, flags);
        model.rowsInserted.connect(this, this.$insertChildren, flags);
        model.rowsMoved.connect(this, this.$_onRowsMoved, flags);
        model.rowsRemoved.connect(this, this.$_onRowsRemoved, flags);
        model.modelReset.connect(this, this.$_onModelReset, flags);

        this.$removeChildren(0, this.$items.length);
        this.$insertChildren(0, model.rowCount());
      } else if (typeof model === "number") {
        // must be more elegant here.. do not delete already created models..
        //this.$removeChildren(0, this.$items.length);
        //this.$insertChildren(0, model);

        if (this.$items.length > model) {
          // have more than we need
          this.$removeChildren(model, this.$items.length);
        } else {
          // need more
          this.$insertChildren(this.$items.length, model);
        }
      } else if (model instanceof Array) {
        this.$removeChildren(0, this.$items.length);
        this.$insertChildren(0, model.length);
      }
    }
  }, {
    key: "$callOnCompleted",
    value: function $callOnCompleted(child) {
      child.Component.completed();
      var QMLBaseObject = QmlWeb.getConstructor("QtQml", "2.0", "QtObject");
      for (var i = 0; i < child.$tidyupList.length; i++) {
        if (child.$tidyupList[i] instanceof QMLBaseObject) {
          this.$callOnCompleted(child.$tidyupList[i]);
        }
      }
    }
  }, {
    key: "$_onModelDataChanged",
    value: function $_onModelDataChanged(startIndex, endIndex, roles) {
      var model = this.$getModel();
      var roleNames = roles || model.roleNames;
      for (var index = startIndex; index <= endIndex; index++) {
        var _item4 = this.$items[index];
        for (var i in roleNames) {
          _item4.$properties[roleNames[i]].set(model.data(index, roleNames[i]), QmlWeb.QMLProperty.ReasonInit, _item4, this.model.$context);
        }
      }
    }
  }, {
    key: "$_onRowsMoved",
    value: function $_onRowsMoved(sourceStartIndex, sourceEndIndex, destinationIndex) {
      var vals = this.$items.splice(sourceStartIndex, sourceEndIndex - sourceStartIndex);
      for (var i = 0; i < vals.length; i++) {
        this.$items.splice(destinationIndex + i, 0, vals[i]);
      }
      var smallestChangedIndex = sourceStartIndex < destinationIndex ? sourceStartIndex : destinationIndex;
      for (var _i12 = smallestChangedIndex; _i12 < this.$items.length; _i12++) {
        this.$items[_i12].index = _i12;
      }
    }
  }, {
    key: "$_onRowsRemoved",
    value: function $_onRowsRemoved(startIndex, endIndex) {
      this.$removeChildren(startIndex, endIndex);
      for (var i = startIndex; i < this.$items.length; i++) {
        this.$items[i].index = i;
      }
      this.count = this.$items.length;
    }
  }, {
    key: "$_onModelReset",
    value: function $_onModelReset() {
      this.$applyModel();
    }
  }, {
    key: "$insertChildren",
    value: function $insertChildren(startIndex, endIndex) {
      if (endIndex <= 0) {
        this.count = 0;
        return;
      }
      var RestModel = QmlWeb.getConstructor("QmlWeb", "2.0", "RestModel");
      var QMLOperationState = QmlWeb.QMLOperationState;
      var createProperty = QmlWeb.createProperty;
      var model = this.$getModel();
      var index = void 0;
      for (index = startIndex; index < endIndex; index++) {
        var newItem = this.delegate.$createObject();
        createProperty("int", newItem, "index", { initialValue: index });

        // To properly import JavaScript in the context of a component
        this.delegate.finalizeImports();

        if (typeof model === "number" || model instanceof Array) {
          if (typeof newItem.$properties.modelData === "undefined") {
            createProperty("variant", newItem, "modelData");
          }
          var value = model instanceof Array ? model[index] : typeof model === "number" ? index : "undefined";
          newItem.$properties.modelData.set(value, QmlWeb.QMLProperty.ReasonInit, newItem, model.$context);
        } else if (model instanceof QmlWeb.ItemModel) {
          if (newItem.model && newItem.model instanceof RestModel) {
            var itemModel = newItem.model;
            itemModel.$updatePropertiesFromResponseObject(model.get(index));
          } else {
            // หัว tab , เราจะเอาอะรใส่เข้าไปใน property บ้าง 
            for (var i = 0; i < model.roleNames.length; i++) {
              var roleName = model.roleNames[i];
              if (typeof newItem.$properties[roleName] === "undefined") {
                createProperty("variant", newItem, roleName);
                newItem.$properties[roleName].set(model.data(index, roleName), QmlWeb.QMLProperty.ReasonInit, newItem, this.model.$context);
              }
            }
          }
        } else {
          for (var _i13 = 0; _i13 < model.roleNames.length; _i13++) {
            var _roleName = model.roleNames[_i13];
            if (typeof newItem.$properties[_roleName] === "undefined") {
              createProperty("variant", newItem, _roleName);
              newItem.$properties[_roleName].set(model.data(index, _roleName), QmlWeb.QMLProperty.ReasonInit, newItem, this.model.$context);
            }
          }
        }
        this.$items.splice(index, 0, newItem);

        //use for setting the position of items
        if (typeof this.placeAfter === "string") {
          newItem._placeAfter = this.placeAfter;
        } else {
          newItem._placeAfter = this.placeAfter && this.placeAfter.dom;
        }

        newItem._repeaterID = this.$Component.objectId;

        // parent must be set after the roles have been added to newItem scope in
        // case we are outside of QMLOperationState.Init and parentChanged has
        // any side effects that result in those roleNames being referenced.
        newItem.parent = this.parent;

        // TODO debug this. Without check to Init, Completed sometimes called
        // twice.. But is this check correct?
        if (QmlWeb.engine.operationState !== QMLOperationState.Init && QmlWeb.engine.operationState !== QMLOperationState.Idle) {
          // We don't call those on first creation, as they will be called
          // by the regular creation-procedures at the right time.
          this.$callOnCompleted(newItem);
        }
      }
      if (QmlWeb.engine.operationState !== QMLOperationState.Init) {
        // We don't call those on first creation, as they will be called
        // by the regular creation-procedures at the right time.
        QmlWeb.engine.$initializePropertyBindings();
      }

      if (index > 0) {
        this.container().childrenChanged();
      }

      for (var _i14 = endIndex; _i14 < this.$items.length; _i14++) {
        this.$items[_i14].index = _i14;
      }

      this.count = this.$items.length;
      this.renderCompleted();
    }
  }, {
    key: "$removeChildren",
    value: function $removeChildren(startIndex, endIndex) {
      var removed = this.$items.splice(startIndex, endIndex - startIndex);
      for (var index in removed) {
        removed[index].$delete();
        this.$removeChildProperties(removed[index]);
      }
    }
  }, {
    key: "$removeChildProperties",
    value: function $removeChildProperties(child) {
      var signals = QmlWeb.engine.completedSignals;
      signals.splice(signals.indexOf(child.Component.completed), 1);
      for (var i = 0; i < child.children.length; i++) {
        this.$removeChildProperties(child.children[i]);
      }
    }
  }]);

  return _class104;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Row",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {}
}, function () {
  function _class105(meta) {
    _classCallCheck(this, _class105);

    QmlWeb.callSuper(this, meta);
    this.baseClassName = "ui";
    this.suffixClassName = "row";
  }

  return _class105;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Schedule",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    events: { type: "var", initialValue: [] },
    size: { type: "int", initialValue: 550 },
    resources: { type: "var", initialValue: [] },
    newEvent: "var"
  },
  signals: {
    rendered: [],
    clicked: [{ type: 'var', name: 'calEvent' }, { type: 'var', name: 'jsEvent' }]
  }
}, function () {
  function _class106(meta) {
    var _this79 = this;

    _classCallCheck(this, _class106);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.eventsChanged.connect(this, this.$onEventsChanged);
    this.resourcesChanged.connect(this, this.$onResourcesChanged);
    this.timePattern = /^([0-1][0-9]|[2][0-3]):([0-5][0-9])$/;
    this.datePattern = /^\d{1,2}\/\d{1,2}\/\d{4}$/;
    this.$calendar = $(this.dom);

    this.setting = {};
    this.setting["locale"] = "th";

    this.setting["header"] = {
      left: 'prevYear prev,next nextYear',
      center: 'title',
      right: 'today'
    };

    this.setting["views"] = {
      scheduleView: {
        titleFormat: 'DD MMMM B',
        resourceHeight: 100,
        slotEventOverlap: true
      }
    };

    this.setting["eventClick"] = function (calEvent, jsEvent, view) {
      _this79.clicked(calEvent, jsEvent);
    };

    this.setting["defaultView"] = "scheduleView";
    this.setting["eventAfterAllRender"] = this.onEventAfterAllRender.bind(this);
    this.setting["eventDestroy"] = this.onEventDestroy.bind(this);
  }

  _createClass(_class106, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.setting["events"] = this._getScheduleEvents();
      this.setting["views"]["scheduleView"]["resources"] = this.resources;
      this.$calendar.width(parseInt(this.size));
      this.$calendar.fullCalendar(this.setting);
      this.completed = true;
    }

    /* !!!!!!! DO NOT !!!!!!!!!!!! set the events to any rendered events   */

  }, {
    key: "$onEventsChanged",
    value: function $onEventsChanged() {
      if (this.bySystem || !this.events instanceof Array) {
        return;
      }
      if (this.completed) {
        var calEvents = this._getScheduleEvents.call({
          events: this.events.slice(),
          timePattern: this.timePattern,
          datePattern: this.datePattern,
          _containsResourceID: this._containsResourceID.bind(this)
        });

        this.$calendar.fullCalendar("removeEvents");
        this.$calendar.fullCalendar("renderEvents", calEvents, true);
      }
    }
  }, {
    key: "$onResourcesChanged",
    value: function $onResourcesChanged() {
      if (this.completed) {
        this.$calendar.fullCalendar('destroy');
        this.completed = false;
        this.Component$onCompleted();
      }
    }
  }, {
    key: "onEventAfterAllRender",
    value: function onEventAfterAllRender(view) {
      //Change happens to event
      this._updateEventsObject();
      this.rendered();
    }
  }, {
    key: "onEventDestroy",
    value: function onEventDestroy(event, element, view) {
      //After event is destroy
      this._updateEventsObject();
    }
  }, {
    key: "_updateEventsObject",
    value: function _updateEventsObject() {
      this.bySystem = true;
      var events = this.$calendar.fullCalendar('clientEvents');
      events.forEach(function (item) {
        if (item.start) {
          item.startDate = item.start.format("DD/MM/B");
          item.startTime = item.start.format("HH:mm");
        }
        if (item.end) {
          item.endDate = item.end.format("DD/MM/B");
          item.endTime = item.end.format("HH:mm");
        }
      });
      this.events = events;
      this.bySystem = false;
    }
  }, {
    key: "_getScheduleEvents",
    value: function _getScheduleEvents() {
      var _this80 = this;

      this.events.forEach(function (item) {
        var startValid = void 0,
            endValid = void 0,
            start = void 0,
            end = void 0,
            day = void 0,
            month = void 0,
            year = void 0;
        startValid = _this80.datePattern.test(item.startDate);
        startValid = startValid && _this80.timePattern.test(item.startTime);
        endValid = _this80.datePattern.test(item.endDate);
        endValid = endValid && _this80.timePattern.test(item.endTime);

        if (startValid) {
          var _item$startDate$split3 = item.startDate.split("/");

          var _item$startDate$split4 = _slicedToArray(_item$startDate$split3, 3);

          day = _item$startDate$split4[0];
          month = _item$startDate$split4[1];
          year = _item$startDate$split4[2];

          year = Math.max(0, Number(year) - 543);
          start = year + "-" + month + "-" + day + "T" + item.startTime + ":00";
        }

        if (endValid) {
          var _item$endDate$split3 = item.endDate.split("/");

          var _item$endDate$split4 = _slicedToArray(_item$endDate$split3, 3);

          day = _item$endDate$split4[0];
          month = _item$endDate$split4[1];
          year = _item$endDate$split4[2];

          year = Math.max(0, Number(year) - 543);
          end = year + "-" + month + "-" + day + "T" + item.endTime + ":00";
        };

        delete item.startDate;
        delete item.startTime;
        delete item.endDate;
        delete item.endTime;

        item["start"] = start;
        item["end"] = end;
      });

      //Warn user if they put resourceID that doesn't exist
      this.events.forEach(function (item) {
        if (!item.resourceID) {
          console.error('There is no resourceID provide');
          return false;
        }
        if (!_this80._containsResourceID(item.resourceID)) {
          console.error("resourceID: " + item.resourceID + " not found");
        }
      });

      return this.events;
    }
  }, {
    key: "_containsResourceID",
    value: function _containsResourceID(id) {
      var res = void 0;
      this.resources.filter(function (item) {
        if (item.id === id) {
          res = true;
        }
      });
      return res;
    }

    /* This method won't check if a new event overlap a disabled event or not   *
     * !!!!!!! DO NOT !!!!!!!!!!!! pass a rendered event                        */

  }, {
    key: "addEvent",
    value: function addEvent(event) {
      var calEvent = this._getScheduleEvents.call({
        events: [event],
        timePattern: this.timePattern,
        datePattern: this.datePattern,
        _containsResourceID: this._containsResourceID.bind(this)
      })[0];

      this.$calendar.fullCalendar('renderEvent', calEvent, true);
    }

    /*  param: id            *
     *  get it by event._id  */

  }, {
    key: "removeEvent",
    value: function removeEvent(id) {
      id && this.$calendar.fullCalendar('removeEvents', id);
    }
  }, {
    key: "removeAllEvents",
    value: function removeAllEvents() {
      this.$calendar.fullCalendar('removeEvents');
    }

    // param: the rendered event that has an id

  }, {
    key: "updateEvent",
    value: function updateEvent(event) {
      event && this.$calendar.fullCalendar('updateEvent', event);
    }
  }, {
    key: "gotoDate",
    value: function gotoDate(date) {
      var day = void 0,
          month = void 0,
          year = void 0;
      if (!this.completed) return;
      if (this.datePattern.test(date)) {
        var _date$split3 = date.split("/");

        var _date$split4 = _slicedToArray(_date$split3, 3);

        day = _date$split4[0];
        month = _date$split4[1];
        year = _date$split4[2];

        year = Math.max(0, Number(year) - 543);
        this.$calendar.fullCalendar('gotoDate', moment(year + "-" + month + "-" + day));
      }
    }
  }, {
    key: "refresh",
    value: function refresh() {
      this.$calendar.fullCalendar('render', event);
    }
  }]);

  return _class106;
}());

{
  var SearchBox = function () {
    function SearchBox(meta) {
      var _this81 = this;

      _classCallCheck(this, SearchBox);

      QmlWeb.callSuper(this, meta);
      this.textChanged.connect(this, this.$onTextChanged);
      this.sizeChanged.connect(this, this.$onSizeChanged);
      this.placeholderChanged.connect(this, this.$onPlaceholderChanged);
      this.dataValidateChanged.connect(this, this.$onDataValidateChanged);

      this.input = document.createElement("input");
      this.button = document.createElement("button");
      this.icon = document.createElement("i");

      this.button.classList.add("ui", "icon", "button");
      this.icon.classList.add("search", "icon");

      this.suffixClassName = "action input";

      this.button.appendChild(this.icon);
      this.dom.appendChild(this.input);
      this.dom.appendChild(this.button);

      this.dom.style.pointerEvents = "auto";
      this.input.style.pointerEvents = "auto";
      this.button.style.pointerEvents = "auto";

      this.input.onkeyup = function (event) {
        if (event.keyCode === Qt.Key_Enter) _this81.entered();
      };
      this.input.addEventListener("change", function () {
        return _this81.updateValue();
      });

      this.button.onclick = function () {
        return _this81.searchClicked();
      };
    }

    _createClass(SearchBox, [{
      key: "updateValue",
      value: function updateValue() {
        this.bySystem = true;
        this.text = this.input.value;
        this.bySystem = false;
        this.changed();
      }
      //override

    }, {
      key: "$onHtmlIDChanged",
      value: function $onHtmlIDChanged() {
        this.input.id = this.htmlID;
      }
    }, {
      key: "validateProperty",
      value: function validateProperty(prop) {
        prop = prop.toLowerCase();
        if (SearchBox.size.includes(prop)) return [true, "" + prop];
        return [false, ""];
      }
    }, {
      key: "$onDataValidateChanged",
      value: function $onDataValidateChanged() {
        this.input.setAttribute("data-validate", this.dataValidate);
      }
    }, {
      key: "$onTextChanged",
      value: function $onTextChanged() {
        if (!this.bySystem) this.input.value = this.text;
      }
    }, {
      key: "$onSizeChanged",
      value: function $onSizeChanged() {
        var _validateProperty13 = this.validateProperty(this.size),
            _validateProperty14 = _slicedToArray(_validateProperty13, 2),
            pass = _validateProperty14[0],
            css = _validateProperty14[1];

        if (!pass) return;
        if (this._size) this.dom.classList.remove("" + this._size);
        this.dom.classList.add(css);
        this._size = this.size;
      }
    }, {
      key: "$onPlaceholderChanged",
      value: function $onPlaceholderChanged() {
        this.input.placeholder = this.placeholder;
      }
    }]);

    return SearchBox;
  }();

  SearchBox.size = ["mini", "small", "large", "big", "huge", "massive"];

  QmlWeb.registerQmlType({
    module: "Semantic.Html",
    name: "SearchBox",
    versions: /.*/,
    baseClass: "Semantic.Html.Dom",
    properties: {
      text: "string",
      placeholder: "string",
      size: "string",
      dataValidate: "string",
      valueID: "string"
    },
    signals: {
      searchClicked: [],
      entered: [],
      changed: []
    }
  }, SearchBox);
}

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Segment",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    dataTab: "string",
    color: "string",
    closable: { type: "bool", initialValue: false }
  }
}, function () {
  function _class107(meta) {
    _classCallCheck(this, _class107);

    QmlWeb.callSuper(this, meta);
    this.dataTabChanged.connect(this, this.$onDataTabChanged);
    this.closableChanged.connect(this, this.$onClosableChanged);
    this.colorChanged.connect(this, this.$onColorChanged);
    this.displayNoneChanged.connect(this, this.$onDisplayNoneChanged);
    this.baseClassName = "ui";
    this.suffixClassName = "segment";
  }

  _createClass(_class107, [{
    key: "$onClosableChanged",
    value: function $onClosableChanged() {
      if (this.closable) {
        this.$linkTag = $("\n        <a href=\"javascript:void(0)\" style=\"float: right; color: red; fontSize:x-large;\">\n          &#10006\n        </a>\n      ");
        this.$linkTag.on('click', this.onCloseClick.bind(this));
      } else {
        this.dom.removeChild(this.$linktag[0]);
        this.$linkTag.off('click', this.onCloseClick.bind(this));
      }
      this.dom.insertBefore(this.$linkTag[0], this.dom.childNodes[0]);
    }
  }, {
    key: "$onColorChanged",
    value: function $onColorChanged() {
      var _validateProperty15 = this.validateProperty(this.color),
          _validateProperty16 = _slicedToArray(_validateProperty15, 2),
          pass = _validateProperty16[0],
          css = _validateProperty16[1];

      if (!pass) return;
      this.dom.classList.remove("" + this._color);
      if (!css) return; // return if css is "" prevent error when call classList.add with ""
      this.dom.classList.add(css);
      this._color = this.color;
    }
  }, {
    key: "validateProperty",
    value: function validateProperty(prop) {
      var colorList = ["", "red", "orange", "yellow", "olive", "green", "teal", "blue", "violet", "purple", "pink", "brown", "grey", "black"];

      if (prop || prop === "") {
        // prevent error from undefined prop and allow property ""
        prop = prop.toLowerCase();
        if (colorList.includes(prop)) {
          return [true, "" + prop];
        }
      }
      return [false, ""];
    }
  }, {
    key: "onCloseClick",
    value: function onCloseClick() {
      this.dom.remove();
    }
  }, {
    key: "$onDataTabChanged",
    value: function $onDataTabChanged() {
      this.dom.setAttribute("data-tab", this.dataTab);
      if (this.dataTab) {
        this.suffixClassName = "tab" + " " + this.suffixClassName;
      } else {
        this.suffixClassName = this.suffixClassName.replace("tab", "").trim();
      }
    }
  }, {
    key: "$onDisplayNoneChanged",
    value: function $onDisplayNoneChanged() {
      if (this.displayNone) this.dom.style.display = "none";else this.dom.style.display = "";

      // fix header of dgrid when displayNone changed
      document.body.dispatchEvent(new CustomEvent("resizeDgrid", {
        detail: {
          dom: this.dom
        }
      }));
    }
  }]);

  return _class107;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Segments",
  versions: /.*/,
  baseClass: "Semantic.Html.Segment", // inherited from Segment
  properties: {}
}, function () {
  function _class108(meta) {
    _classCallCheck(this, _class108);

    QmlWeb.callSuper(this, meta);
    this.baseClassName = "ui";
    this.suffixClassName = "segments";
  }

  return _class108;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Sidebar",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    content: "var"
  },
  signal: {}
}, function () {
  function _class109(meta) {
    _classCallCheck(this, _class109);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.contentChanged.connect(this, this.$onContentChanged);

    this.suffixClassName = "sidebar";
  }

  _createClass(_class109, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var _this82 = this;

      $(document).ready(function () {
        return $(_this82.dom).sidebar({
          transition: "overlay"
        });
      });
    }
  }, {
    key: "$onContentChanged",
    value: function $onContentChanged() {
      this.content.dom.classList.add("pusher");
      document.body.appendChild(this.content.dom);
    }
  }, {
    key: "toggle",
    value: function toggle() {
      $(this.dom).sidebar('toggle');
    }
  }]);

  return _class109;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Sticky",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    context: "string",
    mannualRefresh: "bool"
  }
}, function () {
  function _class110(meta) {
    _classCallCheck(this, _class110);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.mannualRefreshChanged.connect(this, this.$onMannualRefreshChanged);
    this.contextChanged.connect(this, this.$onContextChanged);
    this.baseClassName = "ui";
    this.suffixClassName = "sticky";
  }

  _createClass(_class110, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {}
  }, {
    key: "$onContextChanged",
    value: function $onContextChanged() {
      var _this83 = this;

      $(document).ready(function () {
        _this83.context = !_this83.context.dom ? _this83.context : _this83.context.dom, _this83.sticky = $(_this83.dom).sticky({
          context: _this83.context
        });
        _this83.$onMannualRefreshChanged();
      });
    }
  }, {
    key: "$onMannualRefreshChanged",
    value: function $onMannualRefreshChanged() {
      var _this84 = this;

      if (!this.context) return;
      $(document).ready(function () {
        if (_this84.mannualRefresh && _this84.observer) {
          _this84.observer.disconnect();
          _this84.observer = null;
        }
        if (!_this84.mannualRefresh && !_this84.observer) {
          _this84.observer = new MutationObserver(_this84.refreshSticky.bind(_this84));
          _this84.observer.observe($(_this84.context)[0], {
            childList: true, //observe adding and removing
            subtree: true, //observe mutation
            attributeFilter: ["style", "class"]
          });
        }
      });
    }
  }, {
    key: "refreshSticky",
    value: function refreshSticky(mutations) {
      var _this85 = this;

      //disconnect observer before refresh sticky
      //to prevent observing sticky's style changes
      //and making infinity observing loop
      this.observer.disconnect();
      this.observer = null;
      //wait for animation complete and refresh sticky
      setTimeout(function () {
        return _this85.sticky.sticky("refresh");
      }, 200);
      //after refresh sticky
      //observe this context for any change again
      setTimeout(function () {
        return _this85.$onMannualRefreshChanged();
      }, 300);
    }
  }]);

  return _class110;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Tab",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    headerStyle: { type: "string", initialValue: "default" },
    height: { type: "int", initialValue: "-1" }
  },
  signals: {}
}, function () {
  function _class111(meta) {
    _classCallCheck(this, _class111);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.headerStyleChanged.connect(this, this.$onHeaderStyleChanged);
    this.heightChanged.connect(this, this.$onHeightChanged);
    this.headerNode = document.createElement("div");
    this.headerNode.classList.add("ui", "top", "attached", "menu", "tabular");
    this.dom.appendChild(this.headerNode);
  }

  _createClass(_class111, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      var _this86 = this;

      var aNode = void 0,
          headerList = [];
      //create tab header
      this.children.forEach(function (child) {
        aNode = document.createElement("a");
        aNode.classList.add("item");
        aNode.innerHTML = child.text;
        aNode.setAttribute("data-tab", child.timestamp);
        aNode.onclick = child.onUserSelect.bind(child);

        _this86.headerNode.appendChild(aNode);
        child.jObject = $(aNode);
        headerList.push(aNode);
      });

      $(document).ready(function () {
        var index = headerList.length - 1;
        var _iteratorNormalCompletion9 = true;
        var _didIteratorError9 = false;
        var _iteratorError9 = undefined;

        try {
          for (var _iterator9 = headerList.reverse()[Symbol.iterator](), _step9; !(_iteratorNormalCompletion9 = (_step9 = _iterator9.next()).done); _iteratorNormalCompletion9 = true) {
            var _aNode = _step9.value;

            $(_aNode).tab({
              context: 'parent',
              onVisible: _this86.onVisible.bind(null, _this86.children[index--].dom)
            });
            $(_aNode).tab("change tab", _aNode.getAttribute("data-tab"));
          }
        } catch (err) {
          _didIteratorError9 = true;
          _iteratorError9 = err;
        } finally {
          try {
            if (!_iteratorNormalCompletion9 && _iterator9.return) {
              _iterator9.return();
            }
          } finally {
            if (_didIteratorError9) {
              throw _iteratorError9;
            }
          }
        }
      });
    }
  }, {
    key: "onVisible",
    value: function onVisible(dom) {
      document.body.dispatchEvent(new CustomEvent("resizeDgrid", {
        detail: {
          dom: dom
        }
      }));
    }
  }, {
    key: "$onHeightChanged",
    value: function $onHeightChanged() {
      var _this87 = this;

      if (this.height > 0) {
        this.children.forEach(function (child) {
          child.dom.style.overflowY = "auto";
          child.dom.style.height = _this87.height + "px";
        });
      }
    }
  }, {
    key: "$onHeaderStyleChanged",
    value: function $onHeaderStyleChanged() {
      if (!this.headerNode) return;

      this.headerNode.classList.remove("pointing", "secondary", "top", "attached");

      if (this.headerStyle === "line") {
        this.headerNode.classList.add("pointing", "secondary");
        this.headerNode.style.marginBottom = "0px";
      } else {
        this.headerNode.classList.add("top", "attached");
      }
    }
  }]);

  return _class111;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "TabContent",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    text: "string"
  },
  signals: {
    selected: [{ type: "bool", name: "bySystem" }]
  }
}, function () {
  function _class112(meta) {
    _classCallCheck(this, _class112);

    QmlWeb.callSuper(this, meta);
    this.textChanged.connect(this, this.$onTextChanged);
    this.dom.classList.add("ui", "bottom", "attached", "tab", "segment");
    //Fix segment style bug
    this.dom.style.marginBottom = "0px";
    this.timestamp = "" + Date.now();
  }

  _createClass(_class112, [{
    key: "$onTextChanged",
    value: function $onTextChanged() {
      this.dom.setAttribute("data-tab", this.timestamp);
    }
  }, {
    key: "loading",
    value: function loading() {
      this.select();
      this.jObject.tab('set loading', this.timestamp);
    }
  }, {
    key: "select",
    value: function select() {
      this.jObject.tab('change tab', this.timestamp);
      this.selected(true);
    }
  }, {
    key: "onUserSelect",
    value: function onUserSelect() {
      this.selected(false);
    }
  }]);

  return _class112;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "Text",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {}
}, function () {
  function _class113(meta) {
    _classCallCheck(this, _class113);

    meta.object.tagName = "span";
    QmlWeb.callSuper(this, meta);
  }

  return _class113;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "TextArea",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    text: "string",
    placeholder: "string",
    focused: "bool",
    rows: "int",
    maxLength: "int",
    dataValidate: "string",
    readOnly: { type: "bool", initialValue: false }
  },
  signals: {
    clicked: [],
    entered: [], // user press [Enter]
    changed: [],
    blured: [],
    keyUped: [{ type: "string", name: "keyCode" }],
    keyDowned: [{ type: "string", name: "event" }]
  }
}, function () {
  function _class114(meta) {
    _classCallCheck(this, _class114);

    QmlWeb.callSuper(this, meta);
    this.focusedChanged.connect(this, this.$onFocusChanged);
    this.placeholderChanged.connect(this, this.$onPlaceholderChanged);
    this.rowsChanged.connect(this, this.$onRowsChanged);
    this.textChanged.connect(this, this.$onTextChanged);
    this.maxLengthChanged.connect(this, this.$onMaxLengthChanged);
    this.readOnlyChanged.connect(this, this.$onReadOnlyChanged);
    this.dataValidateChanged.connect(this, this.$onDataValidateChanged);

    this.textarea = document.createElement("textarea");
    this.textarea.style = "resize: none";
    if (this.rows) {
      this.textarea.rows = this.rows;
    }
    this.textarea.addEventListener("keyup", this.updateValue.bind(this));
    this.textarea.addEventListener("change", this.updateValue.bind(this));

    this.dom = this.textarea;
  }

  _createClass(_class114, [{
    key: "updateValue",
    value: function updateValue() {
      this.bySystem = true;
      this.text = this.textarea.value;
      this.bySystem = false;
    }
  }, {
    key: "setFocus",
    value: function setFocus() {
      var _this88 = this;

      if (this.focused) requestAnimationFrame(function () {
        return _this88.textarea.focus();
      });
    }

    //override

  }, {
    key: "$onHtmlIDChanged",
    value: function $onHtmlIDChanged() {
      this.textarea.id = this.htmlID;
    }
  }, {
    key: "$onDataValidateChanged",
    value: function $onDataValidateChanged() {
      this.textarea.setAttribute("data-validate", this.dataValidate);
    }
  }, {
    key: "$onReadOnlyChanged",
    value: function $onReadOnlyChanged() {
      if (this.readOnly) $(this.textarea).prop("readonly", true);else $(this.textarea).prop("readonly", false);
    }
  }, {
    key: "$onFocusChanged",
    value: function $onFocusChanged() {
      this.setFocus();
    }
  }, {
    key: "$onPlaceholderChanged",
    value: function $onPlaceholderChanged() {
      this.textarea.placeholder = this.placeholder;
    }
  }, {
    key: "$onRowsChanged",
    value: function $onRowsChanged() {
      this.textarea.rows = this.rows;
    }
  }, {
    key: "$onTextChanged",
    value: function $onTextChanged() {
      if (!this.bySystem) this.textarea.innerHTML = this.text;
    }
  }, {
    key: "$onMaxLengthChanged",
    value: function $onMaxLengthChanged() {
      this.textarea.maxLength = this.maxLength;
    }
  }]);

  return _class114;
}());

{
  var TEXTBOX_SIZE = ["mini", "small", "large", "big", "huge", "massive"];

  QmlWeb.registerQmlType({
    module: "Semantic.Html",
    name: "TextBox",
    versions: /.*/,
    baseClass: "Semantic.Html.Dom",
    properties: {
      text: "string",
      size: "string",
      state: "string",
      placeholder: "string",
      focused: "bool",
      loading: "bool",
      error: "bool",
      textLength: "string",
      inputType: "string",
      inputName: "string",
      dataValidate: "string",
      readOnly: { type: "bool", initialValue: false },
      enabled: { type: "bool", initialValue: true },
      inputStyle: "string"
    },
    signals: {
      clicked: [],
      entered: [], // user press [Enter]
      changed: [],
      blured: [],
      keyUped: [{ type: "string", name: "keyCode" }],
      keyDowned: [{ type: "string", name: "event" }]
    }
  }, function () {
    function TextBox(meta) {
      var _this89 = this;

      _classCallCheck(this, TextBox);

      QmlWeb.callSuper(this, meta);
      this.Component.completed.connect(this, this.Component$onCompleted);
      this.textChanged.connect(this, this.$onTextChanged);
      this.enabledChanged.connect(this, this.$onEnabledChanged);
      this.focusedChanged.connect(this, this.$onFocusChanged);
      this.sizeChanged.connect(this, this.$onSizeChanged);
      this.readOnlyChanged.connect(this, this.$onReadOnlyChanged);
      this.loadingChanged.connect(this, this.$onLoadingChanged);
      this.errorChanged.connect(this, this.$onErrorChanged);
      this.placeholderChanged.connect(this, this.$onPlaceholderChanged);
      this.textLengthChanged.connect(this, this.$onTextLengthChanged);
      this.inputTypeChanged.connect(this, this.$onInputTypeChanged);
      this.inputNameChanged.connect(this, this.$onInputNameChanged);
      this.dataValidateChanged.connect(this, this.$onDataValidateChanged);
      this.inputStyleChanged.connect(this, this.$onInputStyleChanged);

      this.inputContainer = document.createElement("div");
      this.inputContainer.classList.add("ui", "input");
      this.input = document.createElement("input");
      this.input.type = "text";
      this.input.addEventListener("click", function () {
        return _this89.clicked();
      });
      this.input.addEventListener("blur", function () {
        return _this89.blured();
      });
      this.input.addEventListener("focus", function () {
        return _this89.input.select();
      });
      this.input.addEventListener("change", function () {
        return _this89.updateValue();
      });
      this.input.addEventListener("keyup", function (evt) {
        _this89.updateValue();
        evt.keyCode === 13 && _this89.entered();
        _this89.keyUped(evt.keyCode);
      });
      this.input.addEventListener("keydown", function (evt) {
        _this89.keyDowned(evt);
      });
      this.inputContainer.appendChild(this.input);
      this.dom = this.inputContainer;

      this.suffixClassName = "input";
    }

    _createClass(TextBox, [{
      key: "Component$onCompleted",
      value: function Component$onCompleted() {
        var _this90 = this;

        if (!this.dom.classList.contains("right")) {
          this.children.forEach(function (child) {
            if (child.dom.classList.contains("label")) {
              _this90.dom.insertBefore(child.dom, _this90.input);
            }
          });
        }
      }

      //override

    }, {
      key: "$onHtmlIDChanged",
      value: function $onHtmlIDChanged() {
        this.input.id = this.htmlID;
      }
    }, {
      key: "$onDataValidateChanged",
      value: function $onDataValidateChanged() {
        this.input.setAttribute("data-validate", this.dataValidate);
      }
    }, {
      key: "$onTextChanged",
      value: function $onTextChanged() {
        if (!this.bySystem) this.input.value = this.text;
      }
    }, {
      key: "$onReadOnlyChanged",
      value: function $onReadOnlyChanged() {
        if (this.readOnly) $(this.input).prop("readonly", true);else $(this.input).prop("readonly", false);
      }
    }, {
      key: "updateValue",
      value: function updateValue() {
        this.bySystem = true;
        this.text = this.input.value;
        this.bySystem = false;
        this.changed();
      }
    }, {
      key: "$onEnabledChanged",
      value: function $onEnabledChanged() {
        this.inputContainer.classList.remove("disabled");
        if (!this.enabled) this.inputContainer.classList.add("disabled");
      }
    }, {
      key: "setFocus",
      value: function setFocus() {
        var _this91 = this;

        if (this.focused) requestAnimationFrame(function () {
          return _this91.input.focus();
        });
      }
    }, {
      key: "$onFocusChanged",
      value: function $onFocusChanged() {
        this.setFocus();
      }
    }, {
      key: "validateProperty",
      value: function validateProperty(prop) {
        prop = prop.toLowerCase();
        if (TEXTBOX_SIZE.includes(prop)) return [true, "" + prop];
        return [false, ""];
      }
    }, {
      key: "$onSizeChanged",
      value: function $onSizeChanged() {
        var _validateProperty17 = this.validateProperty(this.size),
            _validateProperty18 = _slicedToArray(_validateProperty17, 2),
            pass = _validateProperty18[0],
            css = _validateProperty18[1];

        if (!pass) return;
        if (this._size) this.inputContainer.classList.remove("" + this._size);
        this.inputContainer.classList.add(css);
        this._size = this.size;
      }
    }, {
      key: "$onPlaceholderChanged",
      value: function $onPlaceholderChanged() {
        this.input.placeholder = this.placeholder;
      }
    }, {
      key: "$onLoadingChanged",
      value: function $onLoadingChanged() {
        if (this.loading) {
          this.icon = document.createElement("i");
          this.icon.classList.add("refresh", "icon");
          this.inputContainer.classList.add("icon", "loading");
          this.inputContainer.appendChild(this.icon);
        } else {
          this.inputContainer.classList.remove("icon", "loading");
          this.inputContainer.removeChild(this.icon);
          this.icon = null;
        }
      }
    }, {
      key: "$onErrorChanged",
      value: function $onErrorChanged() {
        this.inputContainer.classList.remove("error");
        if (this.error) this.inputContainer.classList.add("error");
      }
    }, {
      key: "$onTextLengthChanged",
      value: function $onTextLengthChanged() {
        this.input.size = this.textLength;
      }
    }, {
      key: "$onInputTypeChanged",
      value: function $onInputTypeChanged() {
        this.input.type = this.inputType;
      }
    }, {
      key: "$onInputNameChanged",
      value: function $onInputNameChanged() {
        this.input.name = this.inputName;
      }
    }, {
      key: "$onInputStyleChanged",
      value: function $onInputStyleChanged() {
        this.input.style = this.inputStyle;
      }
    }]);

    return TextBox;
  }());
}

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "TextBoxIcon",
  versions: /.*/,
  baseClass: "Semantic.Html.TextBox",
  properties: {
    icon: "string"
  },
  signals: {
    iconClicked: []
  }
}, function () {
  function _class115(meta) {
    _classCallCheck(this, _class115);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.iconChanged.connect(this, this.$onIconChanged);
  }

  _createClass(_class115, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.completed = true;
      this.addOrRemoveIcon();
    }
  }, {
    key: "$onIconChanged",
    value: function $onIconChanged() {
      if (this.completed) {
        this.addOrRemoveIcon();
      }
    }
  }, {
    key: "addOrRemoveIcon",
    value: function addOrRemoveIcon() {
      if (this.icon !== "") {
        this.removeIcon();
        this.addIcon();
      } else {
        this.removeIcon();
      }
    }
  }, {
    key: "removeIcon",
    value: function removeIcon() {
      this.inputContainer.classList.remove("icon");
      $(this.inputContainer).find('i.icon').off('click', this.iconClick.bind(this));
      $(this.inputContainer).find('i.icon').remove();
    }
  }, {
    key: "addIcon",
    value: function addIcon() {
      this.inputContainer.classList.remove("input");
      this.inputContainer.classList.add("icon");
      this.inputContainer.classList.add("input");
      this.inputContainer.insertAdjacentElement("beforeend", $("<i class=\"" + this.icon + " link icon\"></i>")[0]);
      $(this.inputContainer).find('i.icon').on('click', this.iconClick.bind(this));
    }
  }, {
    key: "iconClick",
    value: function iconClick() {
      this.iconClicked();
    }
  }]);

  return _class115;
}());
QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "TimeTextBox",
  versions: /.*/,
  baseClass: "Semantic.Html.ComboBox",
  properties: {
    startHour: { type: "int", initialValue: "0" },
    startMin: { type: "int", initialValue: "0" },
    intervalMin: { type: "int", initialValue: "0" }
  },
  signals: {}
}, function () {
  function _class116(meta) {
    _classCallCheck(this, _class116);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this._Component$onCompleted);

    this.icon.remove();
    this.text = "00:00";
    this.search = true;
  }

  _createClass(_class116, [{
    key: "_Component$onCompleted",
    value: function _Component$onCompleted() {
      this.startMin = this.$validateMin(this.startMin);
      this.startHour = this.$validateHour(this.startHour);

      var m = moment({
        hour: this.startHour,
        minute: this.startMin,
        seconds: 0
      });

      this.intervalMin = this.$validateMin(this.intervalMin);
      this.intervalMin = this.intervalMin ? this.intervalMin : 60;

      var intervalRound = this.$calculateIntervalRound();
      this.$generateTimes(m, intervalRound);
    }
  }, {
    key: "$calculateIntervalRound",
    value: function $calculateIntervalRound() {
      var minInDay = 1440;
      return minInDay / this.intervalMin;
    }
  }, {
    key: "$generateTimes",
    value: function $generateTimes(m, intervalRound) {
      if (!m._isAMomentObject) return;

      var items = [];
      for (var i = 0; i < intervalRound; i++) {
        items.push({
          id: m.format("HHmm"),
          text: m.format("HH:mm")
        });
        m = m.add(this.intervalMin, "m");
      }

      this.addItems(items);
    }
  }, {
    key: "$validateHour",
    value: function $validateHour(hour) {
      if (hour > 24 || hour < 0) return 0;
      return hour;
    }
  }, {
    key: "$validateMin",
    value: function $validateMin(min) {
      if (min > 60 || min < 0) return 0;
      return min;
    }
  }, {
    key: "$validateTime",
    value: function $validateTime(str) {
      if (str.slice(0, 2) >= 24 || str.slice(0, 2) < 0) {
        return false;
      } else if (str.slice(2) >= 60 || str.slice(2) < 0) {
        return false;
      }

      if (!moment(str, "HH:mm").isValid()) {
        return false;
      }

      return true;
    }
  }, {
    key: "onChange",
    value: function onChange(value, text, $choice) {
      var _this92 = this;

      if (this.dom.classList.contains("multiple") || this.changeBySystem) return;

      this.dom.classList.remove("error");
      if ($choice[0].classList.contains("addition")) {
        $(this.dom).dropdown("remove visible");

        if (!this.$validateTime(value)) {
          this.setSelected("0000");
          this.changeBySystem = true;
          this.dom.classList.add("error");
        } else {
          setTimeout(function () {
            _this92.defaultText.innerHTML = moment(value, "HHmm").format("HH:mm");
          });
        }
      }
    }
  }]);

  return _class116;
}());

QmlWeb.registerQmlType({
  module: "Semantic.Html",
  name: "WebCam",
  versions: /.*/,
  baseClass: "Semantic.Html.Dom",
  properties: {
    width: { type: "int", initialValue: 640 },
    height: { type: "int", initialValue: 480 },
    destWidth: "int",
    destHeight: "int",
    enabled: { type: "bool", initialValue: true },
    fliped: { type: "bool", initialValue: false },
    closeable: { type: "bool", initialValue: true },
    base64Img: "var"
  },
  signals: {
    captured: []
  }
}, function () {
  function _class117(meta) {
    var _this93 = this;

    _classCallCheck(this, _class117);

    QmlWeb.callSuper(this, meta);
    this.Component.completed.connect(this, this.Component$onCompleted);
    this.widthChanged.connect(this, this.$onWidthChanged);
    this.heightChanged.connect(this, this.$onHeightChanged);
    this.enabledChanged.connect(this, this.$onEnabledChanged);
    this.flipedChanged.connect(this, this.$onFlipedChanged);
    this.closeableChanged.connect(this, this.$onCloseableChanged);
    this.destWidthChanged.connect(this, this.$onDestWidthChanged);
    this.destHeightChanged.connect(this, this.$onDestHeightChanged);

    this.setting = {
      fps: 45,
      width: this.width,
      height: this.height,
      flip_horiz: this.fliped,
      dest_width: this.destWidth,
      dest_height: this.destHeight
    };

    this.state = "off";

    Webcam.on('load', function () {
      this.state = "load";
    });

    Webcam.on('live', function () {
      _this93.state = "live";
      _this93.setNewSize();
    });

    this.cameraPane = $("\n            <div style=\"background-color: grey;\n                        overflow: hidden;\n                        width: " + this.width + "px;\n                        height: " + this.height + "px;\">\n            </div>");

    this.imgPane = $("\n            <img style=\"background-color: grey;\">\n            </img>");

    this.textNode = $("\n            <div style=\"display: table-cell; \n                    text-align: center; \n                    vertical-align: middle;\n                    font-weight: bold;\n                    font-size:xx-large\">\n                <div style=\"color: white;\">OFF</div>\n            </div>\n        ");

    this.controlPane = $("\n            <div class=\"ui centered padded grid\" \n                 style=\"width: " + this.width + "px; \n                        background-color: black;\n                        opacity: 0.85;\n                        filter: alpha(opacity=85);\n                 \">\n            </div>\n        ");

    this.captureNode = $("\n            <div class=\"ui centered row\">\n                <button class=\"ui circular icon button\" style=\"background: transparent\">\n                    <i class=\"large photo icon\" style=\"color:white\"></i>\n                </button>\n            </div>\n        ");

    this.afterCaptureNode = $("\n            <div class=\"centered row\">\n                <button class=\"ui icon blue button\" data-type='retake' style=\"background:transparent\">\n                    <i class=\"large repeat blue icon\"></i>\n                </button>\n                <div class=\"column\"></div>\n                <button class=\"ui icon button\" data-type='use' style=\"background:transparent\">\n                    <i class=\"large checkmark green icon\"></i>\n                </button>\n            </div>\n        ");

    this.captureButton = this.captureNode.find('button');
    this.retakeButton = this.afterCaptureNode.find('button[data-type=retake]');
    this.useButton = this.afterCaptureNode.find('button[data-type=use]');

    this.controlPane[0].appendChild(this.captureNode[0]);
    this.controlPane[0].appendChild(this.afterCaptureNode[0]);
    this.dom.appendChild(this.cameraPane[0]);
    this.dom.appendChild(this.controlPane[0]);

    this.captureButton.on('click', function () {
      return _this93.capture();
    });
    this.retakeButton.on('click', function () {
      _this93.showCapturePane();
    });
    this.useButton.on('click', function () {
      _this93.showCapturePane();
      //fire signal
      _this93.captured();
    });
    this.showCapturePane();
  }

  _createClass(_class117, [{
    key: "Component$onCompleted",
    value: function Component$onCompleted() {
      this.completed = true;
      this.refreshWebcam();
    }
  }, {
    key: "refreshWebcam",
    value: function refreshWebcam() {
      if (!this.completed) return;
      if (this.enabled) {
        this.turnoff();
        this.turnon();
      }
    }
  }, {
    key: "showTurnoffBackground",
    value: function showTurnoffBackground() {
      this.display = $(this.dom).css('display');
      this.cameraPane[0].style.display = "table";
      this.cameraPane[0].appendChild(this.textNode[0]);
    }
  }, {
    key: "turnoff",
    value: function turnoff() {
      Webcam.reset();
      this.showTurnoffBackground();
    }
  }, {
    key: "turnon",
    value: function turnon() {
      if (this.cameraPane[0].childNodes.length > 0) {
        this.cameraPane[0].style.display = this.display;
        this.cameraPane[0].removeChild(this.textNode[0]);
      }
      Webcam.set(this.setting);
      Webcam.attach(this.cameraPane[0]);
    }
  }, {
    key: "$onWidthChanged",
    value: function $onWidthChanged() {
      this.setNewSize();
      this.controlPane[0].style.width = this.width + "px";
      this.setting.width = this.width;
      this.refreshWebcam();
    }
  }, {
    key: "$onHeightChanged",
    value: function $onHeightChanged() {
      this.setNewSize();
      this.setting.height = this.height;
      this.refreshWebcam();
    }
  }, {
    key: "$onFlipedChanged",
    value: function $onFlipedChanged() {
      this.setting.flip_horiz = this.fliped;
      this.refreshWebcam();
    }
  }, {
    key: "$onEnabledChanged",
    value: function $onEnabledChanged() {
      if (!this.enabled) {
        this.turnoff();
      } else {
        this.turnon();
      }
    }
  }, {
    key: "$onDestWidthChanged",
    value: function $onDestWidthChanged() {
      this.setting.dest_width = this.destWidth;
      this.refreshWebcam();
    }
  }, {
    key: "$onDestHeightChanged",
    value: function $onDestHeightChanged() {
      this.setting.dest_height = this.destHeight;
      this.refreshWebcam();
    }
  }, {
    key: "capture",
    value: function capture() {
      var _this94 = this;

      Webcam.snap(function (base64) {
        _this94.cameraPane.find("video").transition({
          animation: 'fade',
          duration: 150
        }).transition({
          animation: 'fade',
          duration: 150,
          onComplete: _this94.showAfterCapturePane.bind(_this94)
        });
        _this94.base64Img = base64;
      });
    }
  }, {
    key: "setNewSize",
    value: function setNewSize() {
      this.cameraPane[0].style.width = this.width + "px";
      this.cameraPane[0].style.height = this.height + "px";
      this.imgPane.attr('width', this.width);
      this.imgPane.attr('height', this.height);
    }
  }, {
    key: "showCapturePane",
    value: function showCapturePane() {
      this.afterCaptureNode[0].style.display = "none";
      this.imgPane[0].style.display = "none";
      this.captureNode[0].style.display = "flex";
      if (this.cameraPane.find('video')[0]) this.cameraPane.find('video')[0].style.display = "block";
    }
  }, {
    key: "showAfterCapturePane",
    value: function showAfterCapturePane() {
      this.afterCaptureNode[0].style.display = "flex";
      this.imgPane.attr('src', this.base64Img);
      this.imgPane[0].style.display = "block";
      this.captureNode[0].style.display = "none";
      if (this.cameraPane.find('video')[0]) {
        this.cameraPane.find('video')[0].style.display = "none";
        this.cameraPane[0].insertBefore(this.imgPane[0], this.cameraPane.find('video')[0]);
      }
    }
  }]);

  return _class117;
}());
}(typeof global != "undefined" ? global : window));

//# sourceMappingURL=qt.js.map
