(function(){
     function addItemToChartTodolistController($modalInstance,requestParam) {
         let vm = this;
         vm.patientId = requestParam['patientId'];
         vm.encounterId = requestParam['encounterId'];
         vm.supportedItems = requestParam['supportedItems'];
         vm.remainingItems = requestParam['remainingItems'];
         vm.donotRefresh = requestParam['donotRefresh'];
         vm.allowImport = requestParam['allowImport'];
         vm.calledFrom = requestParam['calledFrom'];
         vm.context = requestParam['context'];
         vm.parentContainer='#addItemToChartToDoListModal';
         vm.close = function (){
             $modalInstance.close();
         }
         vm.loadTodoDirective = function(){
             vm.renderToDoItems = true;
         }
         vm.loadTodoDirective();
    };
    angular.module("AddItemToChartTodolistModule", ['AddtoChartTodolistModule'])
        .controller('addItemToChartTodolistController',addItemToChartTodolistController)

})();