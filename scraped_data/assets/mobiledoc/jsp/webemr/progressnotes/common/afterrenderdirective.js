(function(){

angular.module('ecw.directive.afterrender', [])
.directive('afterRenderComponent', afterRenderComponentDirective);

  afterRenderComponentDirective.$inject = ['$timeout'];
  function afterRenderComponentDirective($timeout){
    return {
      restrict: 'A',
      terminal: true,
      transclude: false,
      link: function (scope, element, attrs) {
        $timeout(scope.$eval(attrs.afterRenderComponent), 0);  //Calling a scoped method
        $timeout(function(){
          if(attrs.section === 'Chief-Complaints'){
            $(".iconlist .nav li").removeClass("active");
            $("#cc").addClass("active");
          } else if(attrs.section === 'Physical-Therapy-Assessment'){
            $(".iconlist .nav li").removeClass("active");
          }
          if(typeof scope.pnModalOnLoad === 'function') {
            scope.pnModalOnLoad();
          }
        }, 0);
      }
    }
  }

})();