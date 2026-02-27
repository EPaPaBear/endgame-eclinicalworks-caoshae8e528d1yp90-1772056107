var multiOptionListModule = angular.module('aiMultiOptionListModule', []);
var multiOptionListCtrl = ['$scope','$modal','resolveData','$modalInstance',
    function ($scope, $modal,resolveData, $modalInstance) {
        $scope.init=function(){
            $("#multiOptionList").modal();
        }
        $scope.listData = resolveData.listData;
        $scope.title = resolveData.title;
        $scope.subTitle = resolveData.subTitle;
        $scope.listHeaders = resolveData.listHeaders;
        $scope.listColumns = resolveData.listColumns;
        $scope.headerMsg = resolveData.headerMsg;
        $scope.closeListModel = function(){
            $("#multiOptionList").modal('hide');
            $modalInstance.close('cancel');
        };
        $scope.selectAiOption = function(optionData){
            $modalInstance.close(optionData);
            $("#multiOptionList").modal('hide');
        };
    }];
multiOptionListModule.controller('aiMultiOptionListCtrl', multiOptionListCtrl);