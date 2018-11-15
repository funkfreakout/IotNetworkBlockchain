var HashedData = artifacts.require("./HashedData.sol");

module.exports = function(deployer) {
  deployer.deploy(HashedData);
};