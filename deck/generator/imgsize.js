// Minimal PNG size reader (avoids extra dependencies).
const fs = require("fs");
function imageSize(p) {
  const b = fs.readFileSync(p);
  if (b.readUInt32BE(0) !== 0x89504e47) throw new Error("PNG only: " + p);
  return [b.readUInt32BE(16), b.readUInt32BE(20)];
}
module.exports = { imageSize };
