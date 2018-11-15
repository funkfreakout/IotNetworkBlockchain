var Strings = artifacts.require("./strings.sol");

module.exports = function(deployer) {
  deployer.deploy(Strings);
};
