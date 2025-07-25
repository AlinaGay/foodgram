if (typeof setImmediate === 'undefined') {
  global.setImmediate = function (callback) {
    return setTimeout(callback, 0);
  };
}

if (typeof clearImmediate === 'undefined') {
  global.clearImmediate = function (id) {
    clearTimeout(id);
  };
}
