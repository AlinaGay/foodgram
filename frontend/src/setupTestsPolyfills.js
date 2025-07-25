if (typeof clearImmediate === 'undefined') {
  global.clearImmediate = function (id) {
    clearTimeout(id);
  };
}
