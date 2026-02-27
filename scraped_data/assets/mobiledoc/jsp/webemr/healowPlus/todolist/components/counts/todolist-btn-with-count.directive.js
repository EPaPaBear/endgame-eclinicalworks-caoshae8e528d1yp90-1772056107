(function(){
    let directiveApp = angular.module('todoButtonWithCountsModule',['Todolist.service']);
    directiveApp.directive('todoButtonWithCounts',function(){
        return{
            restrict: 'AE',
            controller: 'todoButtonWithCountsController',
            controllerAs: 'vm',
            scope: {
                patientId: '=patientId',
                supportedItems:'=supportedItems',
                vmId:'=vmId',
                elementId:'=elementId',
                callback:'&'
            },
            bindToController:true,
            template: `
                <button ng-if="vm.isTodoEnabled" id="{{vm.elementId}}" type="button" ng-style= "vm.btnColor" class="btn btn-xs btn-lgrey mr3" ng-click="vm.callback()">
                    To Do
                    <span ng-if="vm.items.count > 0" class="badge badge-light" ng-bind="vm.items.count"></span>
                </button>
            `,
        }
    });
    directiveApp.controller( 'todoButtonWithCountsController', function ($scope,todoListService) {
        this.$onInit =  function () {
            let vm = this;
            vm.items = {count:0};
            vm.btnColor={};
            vm.isTodoEnabled =  isTodoEnabled();
            if(!vm.isTodoEnabled){
                return;
            }

            vm.getItemCounts= async function (){
                let keys = vm.supportedItems;
                let response = await todoListService.getItemCounts(vm.patientId,keys);
                if(response.data.status===1){
                    vm.items.count = response.data.count;
                    vm.btnColor= vm.items.count === 0 ? {} : {'background-color': '#90EE90;'};
                    $scope.$applyAsync();
                }
            }
            vm.getItemCounts();
            $scope.$on('todoItemsCount', function(e){
                vm.getItemCounts();
            });
            $scope.$on('decrementTodoCount', function(e,data){
                if(data && data.vmId === vm.vmId){
                    vm.items.count -= 1;
                }
                if(vm.items.count < 1){
                    vm.btnColor = {};
                }
            });

        }
    });
})();
