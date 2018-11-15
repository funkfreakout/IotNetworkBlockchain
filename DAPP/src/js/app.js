App = {
  web3Provider: null,
  contracts: {},
  account: '0x0',

  init: function() {
    return App.initWeb3();
  },

  initWeb3: function() {
    
    if (typeof web3 !== 'undefined'){
      App.web3Provider = web3.currentProvider;
      web3 = new  Web3(web3.currentProvider);
    } else{
      App.web3Provider = new Web3.providers.HttpProvider('httpL//localhost:7545');
      web3 = new Web3(App.web3Provider);
    }

    return App.initContract();
  },

  initContract: function() {
    $.getJSON("Root.json", function(rootCon) {
      App.contracts.Root = TruffleContract(rootCon);
      App.contracts.Root.setProvider(App.web3Provider);

      App.listenEvents();
      return App.render();
    });
    
  },

  listenEvents: function() {
    App.contracts.Root.deployed().then(function(instance) {
      instance.InternalGatewayAdded({}, {
        fromBlock: 0,
        toBlock: 'latest'
      }).watch(function(error, result) {
        if (!error){
          var gatewayResults = $('#gatewayResults');
          var gatewayTemplate = "<tr><th>" + result.args._gatewayId + "</th><td>" + result.args._publicKey + "</td><td>" + 
              result.args._data + "</td><td>" + result.args._owner + "</td></tr>";
          gatewayResults.append(gatewayTemplate);
        }else{
          console.log(error);
        }
      });
      
      instance.TierOneAccountAdded({}, {
        fromBlock: 0,
        toBlock: 'latest'
      }).watch(function(error, result) {
        if (!error){
          var tier1Results = $('#tier1Results');
          var accountTemplate = "<tr><th>" + result.args._id + "</th><td>" + result.args._publicKey + "</td><td>" + 
              result.args._deviceName + "</td><td>" + result.args._address + "</td></tr>";
          tier1Results.append(accountTemplate);
        }else{
          console.log(error);
        }
      });

      instance.NodeAddedToGateway({}, {
        fromBlock: 0,
        toBlock: 'latest'
      }).watch(function(error, result) {
        if (!error){
          var nodeResults = $('#nodeResults');
          var nodeTemplate = "<tr><th>" + result.args._nodeId + "</th><td>" + result.args._publicKey + "</td><td>" + result.args._data + 
                "</td><td>" + result.args._deviceName + "</td><td>" + result.args._mac + "</td><td>" + result.args._owner + "</td></tr>";
          nodeResults.append(nodeTemplate);
        }else{
          console.log(error);
        }
      });
      
    });
  },

  render: function() {
    var rootInstance;
    var loader = $('#loader');
    var gatewaycontent = $('#gatewaycontent');
    var nodecontent = $('#nodecontent');
    var teir1content = $('#teir1content');
    var GatewayForm = $('#GatewayForm');
    var AccountForm = $('#AccountForm');
    var NodeForm = $('#NodeForm');

    loader.show();
    nodecontent.hide();
    gatewaycontent.hide();
    teir1content.hide();
    GatewayForm.hide();
    NodeForm.hide();
    AccountForm.hide();

    web3.eth.getCoinbase(function(err, account) {
      if (err === null) {
        App.account = account;
        $('#accountAddress').html("Your Account: " + account);
      }
    });

    App.contracts.Root.deployed().then(function(instance) {
      rootInstance = instance
      return rootInstance.GatewaysCount(0);
    }).then(function(GatewaysCount) {
      var gatewayResults = $('#gatewayResults');
      gatewayResults.empty();
      var nodeResults = $('#nodeResults');
      nodeResults.empty();

      for (var i = 0; i < GatewaysCount; i++) {
        let Owner;

        let GID = i;
        rootInstance.GetGatewayDetails(GID, 0).then(function(gateway) {
          var Public_Key = gateway[0];
          var Data = gateway[1];
          Owner = gateway[2];

          var gatewayTemplate = "<tr><th>" + GID + "</th><td>" + Public_Key + "</td><td>" + Data + "</td><td>" + Owner + "</td></tr>";
          //gatewayResults.append(gatewayTemplate);

          return rootInstance.GatwayNodeCount(GID, 0);
        }).then(function(nodeCount) {
          for (var v = 0; v < nodeCount; v++) {
            let VID = v;
            rootInstance.GetGatewayNodeDetails(GID, VID, 0).then(function(node) {
              var Public_Key = node[3];
              var Data = node[4];
              var Name = node[1];
              var MAC = node[2];

              var nodeTemplate = "<tr><th>" + VID + "</th><td>" + Public_Key + "</td><td>" + Data + 
                "</td><td>" + Name + "</td><td>" + MAC + "</td><td>" + Owner + "</td></tr>";
              //nodeResults.append(nodeTemplate);
            })
          }
        })
      }

      loader.hide();
      nodecontent.show();
      gatewaycontent.show();
      GatewayForm.show();
      NodeForm.show();
    }).catch(function(error) {
      loader.hide();
      console.warn(error);
    });

    App.contracts.Root.deployed().then(function(instance) {
      rootInstance = instance
      return rootInstance.TierOneCount();
    }).then(function(accountCount) {
      var tier1Results = $('#tier1Results');
      tier1Results.empty();

      for (var i = 0; i < accountCount; i++) {
        let Owner;
        let ID = i;

        rootInstance.GetAccountDetails(ID, 0).then(function(taccount) {
          var Public_Key = taccount[1];
          var Data = taccount[2];
          Owner = taccount[3];

          var accountTemplate = "<tr><th>" + ID + "</th><td>" + Public_Key + "</td><td>" + Data + "</td><td>" + Owner + "</td></tr>";
          //tier1Results.append(accountTemplate);
        });
      }
      AccountForm.show();
    }).catch(function(error) {
      AccountForm.hide();
      console.warn(error);
    });
  },

  AddInternalGatewayDevice: function() {
    var pk = $('#publickey').val();
    var data = $('#data').val();
    var owner = $('#owner').val();
    App.contracts.Root.deployed().then(function(instance) {
      return instance.AddInternalGateway(0, pk, data, owner, {from: App.account});
    }).then(function(result) {
    }).catch(function(error) {
      console.warn(error);
    });
  },

  AddTier1Account: function() {
    var pk = $('#publickeyA').val();
    var device = $('#deviceNA').val();
    var owner = $('#ownerA').val();
    App.contracts.Root.deployed().then(function(instance) {
      return instance.AddTierOneAccount(pk, device, owner, {from: App.account});
    }).then(function(result) {
    }).catch(function(error) {
      console.warn(error);
    });
  },

  AddNodeToGateway: function() {
    var pk = $('#publickeyN').val();
    var device = $('#deviceNN').val();
    var gid = $('#GIDn').val();
    var mac = $('#macN').val();
    var data = $('#dataN').val();
    App.contracts.Root.deployed().then(function(instance) {
      return instance.AddNodeToGateway(0, gid, device, mac, pk, data, {from: App.account});
    }).then(function(result) {
    }).catch(function(error) {
      console.warn(error);
    });
  }
};

$(function() {
  $(window).load(function() {
    App.init();
  });
});
