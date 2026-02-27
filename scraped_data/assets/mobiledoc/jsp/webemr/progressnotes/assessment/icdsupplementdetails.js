angular.module('icdsupplementdata',[])
    .controller('icdsupplementdatacontroller', function($scope) {
        var popupObj = $("#assessment-instancepopup");

        $scope.init = function () {
            var data = $("#mICDSupplementPopUpJSONData").val();
            if (data) {
                data = JSON.parse(data);
                $scope.supplementaldata = data["supplementalData"];
                $scope.supplementalDataForProblemList = data["supplementalDataForProblemList"] ? data["supplementalDataForProblemList"] : [];
                try{
                    $scope.icdcaption  = decodeURIComponent(data["name"]);
                }catch (e) {
                    $scope.icdcaption = data["name"];
                }
                $scope.requestFromVB = (1 === data["requestFromVB"]);
                if(data["context"]){
                    $scope.context = data["context"];
                }
                if ($scope.supplementaldata.length < 1 && $scope.supplementalDataForProblemList.length < 1) {
                    setTimeout(function(){$scope.addicd(undefined, 'blank');});
                } else {
                    popupObj.modal();
                    popupObj.find(".modal-dialog").draggable({disabled: true});
                    popupObj.find(".modal-dialog").removeClass("ui-state-disabled");
                }
            }
        };

        $scope.addicd = function (data, flag, callerType) {
            if($scope.requestFromVB) {
                if (flag === 'blank') {
                    if($scope.context === "scribe"){
                        window.parent.setSpecifyNotesData('', '', '', '', callerType);
                    }else{
                        window.external.setSpecifyNotesData('', '', '', '');
                    }
                } else {
                    if($scope.context === "scribe"){
                        window.parent.setSpecifyNotesData(data.specify, data.notes, data.onsetdate, data.risk);
                    }else{
                        window.external.setSpecifyNotesData(data.specify, data.notes, data.onsetdate, data.risk);
                    }
                }
            } else {
                $scope.parentItem = {};
                if (flag === 'blank') {
                    $scope.parentItem.specify = '';
                    $scope.parentItem.notes = '';
                    $scope.parentItem.OnsetDate = '';
                    $scope.parentItem.risk = '';
                    if(callerType){
                        $scope.parentItem.callerType = callerType;
                    }
                } else {
                    $scope.parentItem.specify = data.specify;
                    $scope.parentItem.notes = data.notes;
                    $scope.parentItem.OnsetDate = data.onsetdate;
                    $scope.parentItem.risk = data.risk;
                }
                popupObj.modal('hide');
                $('body').find('.modal-backdrop').last().remove();
                $scope.$parent.processAfterICDSupplementData($scope.parentItem);
                var controllerScope = angular.element(popupObj).scope();
                controllerScope.$destroy();
            }
        };
    });