(function(){

    function assessmentController($sce){
        let vm=this;
        vm.trustNotesAsHtml = $sce.trustAsHtml;
        vm.openDeletePopup = function (item,itemType,event){
            vm.deleteCallback({arg1:item,arg2:itemType,arg3:event});
        }
        vm.showNotes = function (itemType,item){
            vm.showNotesCallBack({arg1:itemType,arg2:item});
        }
        vm.markSelectedItem = function (item){
            vm.markAsCompleted({arg1:'assessments',arg2:item});
        }
    }

    let directiveApp = angular.module('ToDoAssessmentModule',[])
        .controller('assessmentController',assessmentController)

    directiveApp.directive('todoAsssessment',function(){
        return{
            restrict: 'AE',
            controller: 'assessmentController',
            controllerAs: 'vm',
            scope: {
                items: '=items',
                healowPlusAccess:"=healowPlusAccess",
                deleteCallback:'&',
                markAsCompleted:'&',
                showNotesCallBack:'&',
                isHccItem :'=?'
            },
            bindToController:true,
            templateUrl: '/mobiledoc/jsp/webemr/healowPlus/todolist/components/todo-container/template/todolist-assessments.template.html',
            link: function(scope, element, attributes){
            }
        }
    });

})();