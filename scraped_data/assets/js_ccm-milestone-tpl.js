angular.module('ecw.phm.milestonePopup', [ 'ui.bootstrap', 'oc.lazyLoad']).directive('milestonePopup',
    function ($http, $modal, $ocLazyLoad) {
        return {
            restrict: 'AE',
            replace: 'false',
            scope: {
                module: '=',
                ptId: "=",
                ptDtl:'=',
                screen:'='
            },
            link: function (scope, element) {
                element.click(function () {
                    $('.action-hub-modal').remove();
                    $ocLazyLoad.load({
                        name: 'ccmPcmMilestone',
                        files: ['/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/milestone/js/ccmMilestoneController.js', '/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/enrollmentqueue/enrollmentqueuefilter/js/common-directive.js',
                            '/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/milestone/js/ccmMilestoneService.js', '/mobiledoc/jsp/webemr/spellcheck/lookup/js/spell.check.js',
                            '/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/js/ccmEnrollmentBridgeService.js'
                        ]
                    }).then(function () {
                        scope.mileStoneData = {
                            module: scope.module,
                            ptId: scope.ptId,
                            ptDtl:scope.ptDtl,
                            screen:scope.screen
                        };

                        var permission = getPermission("AccesstopatientsMilestones", global.TrUserId);
                        if(!permission){
                            alert ("You do not have permission to access Patient Milestone . Please contact your administrator to give the permission for security item '<b>Access to Patient's Milestones</b>'.");
                            return false;
                        }

                        $modal.open({
                            templateUrl: makeURL('/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/milestone/ccmMilestoneModal.html'),
                            backdrop: "static",
                            keyboard:false,
                            controller:'ccmMilestoneController',
                            controllerAs:'milestoneCtrl',
                            animation: true,
                            windowClass: "custom-modal w1000",
                            resolve: {
                                mileStoneData: function () {
                                    return scope.mileStoneData;
                                }
                            }
                        });
                    });
                });
            }
        };
    });