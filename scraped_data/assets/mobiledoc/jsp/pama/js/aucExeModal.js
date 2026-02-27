var app = angular.module('aucExeModalApp',['pama']);
app.controller('aucExeModalController', function ($scope,aucService,$modal) {
    let vm = this;
    vm.reportId , vm.patientId , vm.encounterId, vm.context;
    $scope.init = function (reportId ,patientId,encounterId,context)  {
        vm.reportId = reportId;
        vm.patientId = patientId;
        vm.encounterId = encounterId;
        vm.context = context;
        let requestParams = {
            reportId: vm.reportId,
            patientId : vm.patientId
        };
        if(vm.context === "GET_AUC_LOGS"){
            aucService.getAUCDetailsLogs(requestParams, openAucLogModal);
        }
    };

    function openAucLogModal(data) {
        if(!data.response.recommendationsJson) {
            showMessage("There is no AUC details to display for this item", "");
            return;
        }

        openRecommendationsModal(data.response);
    }

    function openRecommendationsModal(response){
        let context = 'AUC_LOG';

        let encounterData = {
            encounterId: vm.encounterId
        };

        let patientIdentifier = {};
        patientIdentifier.patientId = vm.patientId;

        let icdDetails = {};

        let ordersWithPerformingICD = [];

        let recommendationsJson = angular.extend(JSON.parse(response.recommendationsJson), {rejectReasonId: response.rejectReasonId});

        let aucDetailsAdditionalInfo = {
            rejectionReasonList	: response.rejectionReasonList,
            acceptedRejectedBy	: response.acceptedRejectedBy,
            acceptedRejectedTime: response.acceptedRejectedTime,
            aucOrderStatus		: response.aucOrderStatus,
            aucAppropriateness 	: response.aucAppropriateness,
            gCode 				: response.gCode,
            transactionId 		: response.transactionId,
            hcpcsModifier 		: response.hcpcsModifier
        };
        aucService.openRecommendationsModal($modal, closeVBModal, context, encounterData, patientIdentifier, icdDetails, ordersWithPerformingICD, recommendationsJson, aucDetailsAdditionalInfo);
    }

});

