(function () {

    function immunizationToDoService(todolistSharedService) {
        return {
            checkCvx: checkCvx,
            showPrompt: showPrompt,
            isCvxExist: isCvxExist,
            isItemValid: isItemValid,
        }

        function isCvxExist(givenItem) {
            return !todolistSharedService.isUNE(givenItem.cvx);
        }

        function isItemValid(item) {
            let flag = true;
            if (!isCvxExist(item)) {
                todolistSharedService.showError(item.description + " does not have CVX associated with it so it can't imported.");
                flag = false;
            }
            return flag;
        }

        function checkCvx(context, item, targetElement, successCallBack,parentContainer) {
            if (!isItemValid(item)) {
                return;
            }
            return checkCvxCptExist(context, item, targetElement, successCallBack,parentContainer);
        }

        function checkCvxCptExist(context, item, targetElement, successCallBack,parentContainer) {
            todolistSharedService.httpCall(todolistSharedService.baseUrl() + 'immunizations/getItemsByCode/', 'POST', item)
                .then(function (response) {
                    if (response.data && response.data.codes && response.data.status === 1) {
                        resolveItem(context,response.data.codes, targetElement, item, successCallBack,parentContainer);
                    } else {
                        todolistSharedService.showError('Error occurred while checking duplicate cvx items.');
                    }
                }, function () {
                    todolistSharedService.showError('Error occurred while checking duplicate cvx items.');
                });
        }

        function resolveItem(context,codes, targetElement, item, successCallBack,parentContainer) {
            if (codes.length === 0) {
                todolistSharedService.showError(item.description+" immunization cannot be imported as no matching CVX code was found"+"(cvx : "+item.cvx+") " );
            } else if (codes.length === 1) {
                item.itemid = codes[0].itemId;
                successCallBack();
            } else if (codes.length > 1) {
                item.cvxItems = codes;
                let prop;
                if(context === 'ImmunizationHx'){
                    prop = {my: 'left-67 top+35', at: 'left top', collision: 'flipfit', opacity: 1};
                }else {
                    prop = {my:'left top+14',at:'left top',collision:'flipfit',opacity:1};
                }
                showPrompt('todo-immunization-multiple-cvx' + item.uiPromptId, targetElement, prop,parentContainer);
            }
        }

        function showPrompt(id, _that, properties,parentContainer) {
            todolistSharedService.showPrompt(id, _that, properties,parentContainer);
        }
    }

    angular.module('immunizationToDo.service', ['Todolist-Shared.service'])
        .service('immunizationToDoService', immunizationToDoService);
})();