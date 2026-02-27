angular.module('rpmThirdPartyPortalDirective', ['ecw.dir.patientidentifier']
).directive('rpmThirdPartyPortal',
    function($http, $modal, $ocLazyLoad) {
        return {
            restrict : 'AE',
            replace : 'true',
            scope : {
                patientId        : '=',
                enrollmentId     : '=',
                ptaCoId          : '=',
                timerStatus      : '=',
                timerStartTime   : '=',
                primaryContact   : '=',
                hasPermission    : '=',
                patientDetails   : '=',
                trackerMappingId : '=',
                displayName      : '=',
                vendorId         : '=',
                trackerId        : '=',
                callBack         : '&',
                healowLogin      : '='
            },
            link : function(scope, element, attrs, ngModelCtrl) {
                element.click(function(){
                    $ocLazyLoad.load({
                        name: 'rpmThirdPartyPortal',
                        files: ['/mobiledoc/jsp/webemr/ccmr/rpm/js/service/rpmUserServices.js',
                                '/mobiledoc/jsp/webemr/ccmr/rpm/devicemonitoring/css/monitoring-status.css',
                                '/mobiledoc/jsp/webemr/ccmr/rpm/devicemonitoring/js/rpmThirdPartyPortalCtrl.js'
                            ]
                    }).then(function() {
                        scope.rpmThirdPartyPortalData = {
                            patientId       :    scope.patientId,
                            ptaCoId         :    scope.ptaCoId,
                            primaryContact  :    scope.primaryContact,
                            timerStatus     :    scope.timerStatus,
                            timerStartTime  :    scope.timerStartTime,
                            hasPermission   :    scope.hasPermission,
                            patientDetails  :    scope.patientDetails,
                            trackerMappingId:    scope.trackerMappingId,
                            displayName     :    scope.displayName,
                            vendorId        :    scope.vendorId,
                            trackerId       :    scope.trackerId,
                            callBack        :    scope.callBack,
                            healowLogin     :    scope.healowLogin
                        };

                        $modal.open({
                            templateUrl: makeURL('/mobiledoc/jsp/webemr/ccmr/rpm/devicemonitoring/view/rpmThirdPartyPortalModal.html?'),
                            controller: 'rpmThirdPartyPortalCtrl',
                            controllerAs:'thirdPtPortCtrl',
                            backdrop: 'static',
                            windowClass: 'custom-modal w720',
                            animation: true,
                            resolve : {
                                rpmThirdPartyPortalData: function() {
                                    return scope.rpmThirdPartyPortalData;
                                }
                            }
                        });
                    }, function(e) {

                    });
                });
            }
        };
    });