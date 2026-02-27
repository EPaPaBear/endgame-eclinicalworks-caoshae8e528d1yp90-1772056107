'use strict';
(function(f) {
  var allergyPromptDirectiveApp = f.module('allergyPromptDirectiveApp', []);
  allergyPromptDirectiveApp.directive('prompt', ['$sce', function ($sce) {
    return {
      restrict: 'E',
      templateUrl: '/mobiledoc/jsp/allergy/assets/directives/prompt/index.html',
      transclude: true,
      scope: {
        promptType: '@', // Probable options - error (red theme), warning (yellow theme), communication (blue theme), confirmation (orange theme) 
        primaryBtnTxt: '@',
        secondaryBtnTxt: '@',
        primaryBtnPress: '&',
        secondaryBtnPress: '&',
      },
      controller: 'promptController',
      controllerAs: 'vm',
      link: function (scope) {
        scope.trustHtml = function (html) {
          return $sce.trustAsHtml(html);
        };
      }
    };
  }]).controller('promptController', () => {

  })
})(angular);