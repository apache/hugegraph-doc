const {buildSidebar} = require('./src/sidebars/buildSidebars');

module.exports = {
  docsSidebar: buildSidebar('content/en/docs'),
};
