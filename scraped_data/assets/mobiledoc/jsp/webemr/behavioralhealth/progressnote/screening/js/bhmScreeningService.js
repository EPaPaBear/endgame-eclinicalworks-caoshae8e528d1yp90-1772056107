(function () {
    angular.module('ecw.service.bhmScreeningService', []).service('bhmScreeningService', ['$http', "$log", '$q', bhmScreeningService])
    function bhmScreeningService($http,$log,$q) {
        var adminUrlPrefix="/mobiledoc/behavioralhealth/screeningTemplate/";
        var pnScreeningPrefix="/mobiledoc/behavioralhealth/PnScreening/";
        return {
            getItemKeyId: getItemKeyId,
            getTemplateListForCategory: getTemplateListForCategory,
            getSmartFormsList: getSmartFormsList,
            getMappedCustomFormsList: getMappedCustomFormsList,
            checkPNSectionsWithScreeningPermission: checkPNSectionsWithScreeningPermission
        };



        function httpPost(url,data){
            var param = $.param(data);
            return $http({
                headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                method: 'POST',
                url: url,
                data: param
            });
        }

        function getItemKeyId (keyName) {
            var id = 0;
            if(keyName) {
                var itemKey = {};
                getItemKeyValuePair(keyName, itemKey);
                id = (itemKey && itemKey.itemId) ? itemKey.itemId : 0;
            }
            return id;
        }

        function getTemplateListForCategory(encounterId,categoryId, entryId){
            if(categoryId!=0){
                if(!entryId) {
                    entryId = 0;
                }
                var url=adminUrlPrefix+"getTemplateListForCategoryGivenEncounterId";
                var data = {encounterId:encounterId,categoryId:categoryId, entryId: entryId, considerCompleted: "no"};
                return httpPost(url,data)
            }else{
                ecwAlert('No Category selected');
            }
        }

        function getSmartFormsList(encounterId, patientId) {
            var url=pnScreeningPrefix+"getSmartFormsForGivenEncounterId";
            var data = {encounterId:encounterId,patientId: patientId, isFromSFDropdown: "true"};
            return httpPost(url,data)
        }

        function getMappedCustomFormsList(encounterId, patientId) {
            let url=pnScreeningPrefix+"getMappedCustomFormsForEncounter";
            let data = {encounterId: encounterId,patientId: patientId, isFromDischarge:false, programId: 0};
            if ($('#isFromDischarge').val() === 'true'){
                data.isFromDischarge = true;
                data.programId = angular.element("#bh-discharge").scope().programId;
            }
            return httpPost(url,data)
        }

        function checkPNSectionsWithScreeningPermission(encounterId) {
            if(encounterId>0){
                let url = pnScreeningPrefix+ 'checkPNSectionsWithScreeningPermission/'+ encounterId;
                return $http({
                    headers: {'Content-Type': 'application/json'},
                    method: 'POST',
                    url: url
                });
            }else{
                ecwAlert('No valid encounterId');
            }
        }
    }
})();