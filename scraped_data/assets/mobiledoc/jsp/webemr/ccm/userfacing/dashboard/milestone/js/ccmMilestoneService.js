angular.module('ccm.ccmMilestoneService', []).service('ccmMilestoneService', ['$http', '$log', '$q', ccmMilestoneService])
function ccmMilestoneService($http) {
    var getMileStoneList = function (ptMilestoneId,userId,columnName) {
        return $http({
            method: 'POST',
            url: '/mobiledoc/phm/ccmMilestone/getMileStoneNewList?ptMilestoneId='+ptMilestoneId+'&userId='+userId+'&columnName='+columnName

        });
    };

    var saveAll = function (param,ptMilestoneId,queArray) {
        return $http({
            method: 'POST',
            url: '/mobiledoc/phm/ccmMilestone/saveAll?patientid='+ptMilestoneId+'&tblName='+param+'&info='+encodeURIComponent(JSON.stringify(queArray))


        });
    };
    return {
        getMileStoneList: getMileStoneList,
        saveAll:saveAll
    }
}