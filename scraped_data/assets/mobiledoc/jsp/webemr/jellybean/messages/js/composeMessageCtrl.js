angular.module('messagesApp', [])
.controller('composeMessageController', ['$scope', '$modalInstance',
  function($scope, $modalInstance) {
    const composeCtrl = this;
    composeCtrl.source = 'compose-message';

    composeCtrl.close = function(isMessageSent) {
      if (isMessageSent) {
        $modalInstance.close(true);
      } else {
        $modalInstance.dismiss();
      }
    };
  }]);