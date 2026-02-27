(function(){

    function hmDetailsController(todolistSharedService){
        this.$onInit = function () {
            let vm = this;

            if(vm.hmItem.context !== 'smart-todo'){
                let ptDob = moment(vm.hmItem.ptDob,'YYYY-MM-DD');
                let currentDt = moment();
                let diffInDays = currentDt.diff(ptDob ,'days');
                vm.minDate = "-"+diffInDays+"D";
            }
            vm.showDatepicker=function (event){
                $(event.target).parent().parent().parent().find('input[type="text"]').datepicker("show");
            }
            vm.isImmInjItemType = function (){
                return todolistSharedService.isImmInjItemType(vm.hmItem);
            }

            vm.calculateLastDoneDate = function(count, units) {
                vm.hmItem.lastDoneDate = moment().add(count, units).format('MM/DD/YYYY');
            };

            vm.calculateDueDate = function(count, units) {
                vm.hmItem.dueDate = moment().add(count, units).format('MM/DD/YYYY');
            };

            vm.saveDueDate = function (){
                let date = moment(vm.hmItem.dueDate, 'MM-DD-YYYY');
                if(!date.isValid()){
                    ecwAlert("Please enter due date in 'MM-DD-YYYY' Format.");
                    return;
                }

                if(!isSameDate (vm.hmItem.dueDate) && date.isBefore(moment())){
                    ecwAlert("Due Date cannot be less than Today's date.");
                    return;
                }
                vm.saveCallback();
            }

            isSameDate = function (inputDate){
                return inputDate ===  moment().format("MM/DD/YYYY");
            }

            vm.placeOrder = function(){
                let date = moment(vm.hmItem.lastDoneDate, 'MM-DD-YYYY');
                if(!date.isValid()){
                    ecwAlert("Please enter given date in 'MM-DD-YYYY' Format.");
                    return;
                }
                let ptDob = moment(vm.hmItem.ptDob, 'YYYY-MM-DD');
                if(date.isBefore(ptDob)){
                    ecwAlert("Given Date cannot be less than Patient's Birth Date.");
                    return;
                }

                if(date.isAfter(moment())){
                    ecwAlert("Given Date cannot be greater than Today's date.");
                    return;
                }

                vm.hmItem.givenDate = vm.hmItem.lastDoneDate;
                vm.saveCallback();
            }
        }
    }

    let directiveApp = angular.module('HmDetailsModule',['Todolist-Shared.service'])
        .controller('hmDetailsController',hmDetailsController)

    directiveApp.directive('hmDetails',function(){
        return{
            restrict: 'AE',
            controller: 'hmDetailsController',
            controllerAs: 'vm',
            scope: {
                hmItem: '=hmItem',
                saveCallback:'&',
                closeCallback:'&'
            },
            bindToController:true,
            templateUrl: '/mobiledoc/jsp/webemr/healowPlus/todolist/components/todo-container/historical/hx-details-template.html',
            link: function(scope, element, attributes){
            }
        }
    });

})();