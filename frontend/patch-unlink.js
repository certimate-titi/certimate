// Patch fs.unlink to be a no-op to work around fuse mount EPERM issues
const fs = require('fs');
const orig = fs.unlink;
const origSync = fs.unlinkSync;

const BLOCK_KEYWORDS = ['.features-gen', 'test-results/.last-run', 'playwright-report'];

function shouldBlock(path) {
  if (!path) return false;
  return BLOCK_KEYWORDS.some(k => path.includes(k));
}

fs.unlink = function(path, callback) {
  if (shouldBlock(path)) {
    if (typeof callback === 'function') callback(null);
    return;
  }
  return orig.apply(this, arguments);
};

fs.unlinkSync = function(path) {
  if (shouldBlock(path)) return;
  return origSync.apply(this, arguments);
};

const promises = fs.promises;
const origPromise = promises.unlink;
promises.unlink = async function(path) {
  if (shouldBlock(path)) return;
  return origPromise.apply(this, arguments);
};
