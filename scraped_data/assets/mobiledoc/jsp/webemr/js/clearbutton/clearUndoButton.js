(function (){
    let clearUndoButton = function(clearUndoType,clearUndoDefaultValue) {
        return {
            restrict: 'AE',
            templateUrl: makeURL('/mobiledoc/jsp/webemr/js/clearbutton/templates/clear-undo-button.html'),
            scope: {
                isClearButtonDisabled : '=',
                isClearButtonShow: '=',
                buttonContext : '@', 
                modalVariable : '=',
                clearCallback : '&',
                undoCallback : '&',
                isUndoCallback : '@',
                extraClass : '@',
                callBackParam : '=',
                clearButtonId : '@',

            },
            link: function(scope) {
                scope.isCurrentBtnClear = true;

                if(angular.isUndefined(scope.buttonContext)){
                    scope.buttonContext = clearUndoDefaultValue.BUTTONCONTEXT;
                }

                if(angular.isUndefined(scope.clearButtonId)){
                    scope.clearButtonId = clearUndoDefaultValue.CLEARBUTTONID;
                }
                if(angular.isUndefined(scope.isUndoCallback)){
                    scope.isUndoCallback = false;
                }

                if(!scope.buttonCurrentState)
                {
                    scope.buttonCurrentState = clearUndoType.CLEAR;
                    scope.isCurrentBtnClear = true;
                }
                let undoText = {};

                scope.clear = function (){
                    if(!scope.modalVariable){
                        return ;
                    }
                    undoText[scope.buttonContext] =  angular.copy(scope.modalVariable);
                    scope.modalVariable = '';
                    scope.buttonCurrentState = clearUndoType.UNDO;
                    scope.isCurrentBtnClear = false;
                    if (typeof(scope.clearCallback) === 'function'){
                        if(!scope.callBackParam){
                            scope.clearCallback()(scope.buttonContext);
                        }else{
                            scope.clearCallback()(scope.buttonContext,scope.callBackParam)
                        }
                    }
                };

                let clearButtonBroadcast = scope.$on(scope.buttonContext+clearUndoDefaultValue.BRODCASTUNIQUEKEY, function(e) {
                    scope.isCurrentBtnClear = true;
                });

                scope.$on('$destroy', function(){
                    clearButtonBroadcast();
                });

                scope.undo = function (){
                    scope.modalVariable = undoText[scope.buttonContext];
                    undoText[scope.buttonContext] = '';
                    scope.buttonCurrentState = clearUndoType.CLEAR;
                    scope.isCurrentBtnClear = true;
                    if (scope.isUndoCallback){
                        if(!scope.callBackParam){
                            scope.undoCallback()(scope.buttonContext);
                        }else{
                            scope.undoCallback()(scope.buttonContext,scope.callBackParam)
                        }
                    }
                };
            }
        };
    };
    angular.module('clearUndoButtonProvider', [])
        .directive('clearUndoButton', clearUndoButton)
        .constant('clearUndoType', {
            UNDO: "undo",
            CLEAR: "clr"
        })
        .constant('clearUndoDefaultValue', {
            BUTTONCONTEXT: "defaultClearUndoContext",
            CLEARBUTTONID : "btnClearCLR",
            BRODCASTUNIQUEKEY : "ClearUndoButton"
        });

})();