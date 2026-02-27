(function(){

    function checkListController(todolistSharedService){
        let vm=this;
        vm.openDeletePopup = function (item,itemType,event){
            vm.deleteCallback({arg1:item,arg2:itemType,arg3:event});
        }
        vm.showCheckListItem = function (event,item){
            vm.showCheckListCallBack({arg1:event,arg2:item});
        }
        vm.markSelectedItem = function (item){
            vm.markAsCompleted({arg1:'checklist',arg2:item});
        }
        vm.isCheckListFromToDo = function (item){
            return todolistSharedService.isCheckListFromToDo(item);
        }
    }

    let directiveApp = angular.module('ToDoCheckListModule',['Todolist-Shared.service'])
        .controller('checkListController',checkListController)

    directiveApp.directive('todoChecklist',function(){
        return{
            restrict: 'AE',
            controller: 'checkListController',
            scope: {
                items: '=items',
                healowPlusAccess:"=healowPlusAccess",
                deleteCallback:'&',
                markAsCompleted:'&',
                showCheckListCallBack:'&'
            },
            controllerAs: 'vm',
            bindToController:true,
            templateUrl: '/mobiledoc/jsp/webemr/healowPlus/todolist/components/todo-container/template/todolist-checklist.template.html',
            link: function(scope, element, attributes){
            }
        }
    });

})();