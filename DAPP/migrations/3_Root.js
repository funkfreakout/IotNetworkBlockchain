var Root = artifacts.require("./Root.sol");

module.exports = function(deployer) {
  deployer.deploy(Root, "lol", { gas: 47123888 });
};
