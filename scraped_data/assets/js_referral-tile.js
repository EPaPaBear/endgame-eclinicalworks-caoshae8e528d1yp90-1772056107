(() => {
    'use strict';

    angular.module('ecw.documentInsight')
        .directive('referralTile', ['ReferralService', '$observableService', 'DocumentInsightTileWrapperService', '$ocLazyLoad', function(ReferralService, $observableService, DocumentInsightTileWrapperService, $ocLazyLoad) {
            return {
                restrict: 'E',
                scope: {},
                templateUrl: '/mobiledoc/jsp/webemr/toppanel/prisma/document-insight/html/referral-tile-template.html',
                controller: ['$scope', function($scope) {
                    const vm = this;
                    vm.referral = [];
                    vm.tileParams = DocumentInsightTileWrapperService.getDocumentInsights();
                    vm.isExpanded = true;
                    vm.isContentLoaded = false;
                    vm.token = $("meta[name='_csrf']").attr("content");

                    $observableService.subscribe('refreshTiles', event => {
                        if(event?.data?.tile === 'all' || event?.data?.tile === 'referral') {
                            vm.tileParams = event?.data?.data;
                            getLastPatientReferral(vm.tileParams?.patientId);
                        }
                    });

                    const getLastPatientReferral = patientId => {
                        if (!patientId || !vm.tileParams.recordId) {
                            vm.isContentLoaded = true;
                            return {};
                        }
                        ReferralService.getIncomingReferral(patientId, vm.tileParams.recordId).then(response => {
                            vm.referral = response?.data || {};
                            vm.isContentLoaded = true;
                        }, () => {
                            ecwAlert("Error occurred while fetching Referral Details.");
                            vm.isContentLoaded = true;
                            return {};
                        });
                    }

                    vm.expandAll = () => {
                        vm.isExpanded = !vm.isExpanded;
                    }

                    vm.openAttachment = (nhxReqId) => {
                        $("#doc-insights-referralpopup_refattform").attr("action", makeURL("/mobiledoc/jsp/webemr/jellybean/patientrecord/referralattachmentshtml.jsp"));
                        $("#doc-insights-referralpopup_refattform #nhxReqId").val(nhxReqId);
                        $("#doc-insights-referralpopup_refattform").submit();
                        $("#doc-insights-ptRecordInboxAtt").modal('show')
                    }

                    vm.initReferral = function(refId, patientId) {
                        vm.referralPopUpURL2 = "";
                        var params = {
                            refId: refId,
                            patientId: patientId,
                            ptName: "",
                            refEncId: 0,
                            nNhxReqId: 0,
                            recType: "REF",
                            referralType: 'Incoming',
                            callingFrom: 'documentInsights',
                            refSubType:''
                        };

                        params = $.param(params);
                        $ocLazyLoad.load({
                            name: 'referralPopUpApp',
                            files: [
                                '/mobiledoc/jsp/webemr/jellybean/patientrecord/commanP2PService.js',
                                '/mobiledoc/jsp/webemr/jellybean/referral/referralPopupController.js',
                                '/mobiledoc/jsp/webemr/templates/icd-tpl.js',
                                '/mobiledoc/jsp/webemr/progressnotes/physiciansdashboard/EncDetailsService.js',
                                '/mobiledoc/jsp/webemr/templates/cpt-tpl.js',
                                '/mobiledoc/jsp/webemr/templates/savePrompt-tpl.js',
                                '/mobiledoc/jsp/webemr/progressnotes/ecwrx/RxHelper/ICD_Treatment.js'
                            ]
                        }).then(function() {
                            var url = makeURL('/mobiledoc/jsp/webemr/jellybean/referral/referralPopup.jsp?' + params);
                            vm.referralPopUpURL2 = url ;
                        }, function(e) {
                            ecwAlert("An error occurred while loading Referral.")
                        });

                    };

                    $scope.$on('$destroy', () => {
                        $observableService.unsubscribe('refreshTiles');
                    });
                }],
                controllerAs: 'vm'
            };
        }]);
})();