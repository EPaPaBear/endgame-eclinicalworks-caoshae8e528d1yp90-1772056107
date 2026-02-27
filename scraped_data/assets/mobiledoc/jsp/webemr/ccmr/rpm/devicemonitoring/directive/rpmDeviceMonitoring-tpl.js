angular.module('ecw.rpm.deviceMonitoringApp', ['ecw.dir.patientidentifier']).directive('rpmDeviceMonitoring',
    function($http, $modal, $ocLazyLoad) {
        return {
            restrict : 'AE',
            replace : 'true',
            scope : {
                patientId : '=',
                ptaCoId : '=',
                timerStatus : '=',
                timerStartTime : '=',
                primaryContact : '=',
                deviceType : '=',
                trackerType : '=',
                deceasedOrInactive : '=',
                callbackFunction: '&',
                callFrom:'=',
                healowLogin:'='
            },
            link : function(scope, element, attrs, ngModelCtrl) {
                element.click(function(){
                    $ocLazyLoad.load({
                        name: 'rpmDeviceMonitoring',
                        files: ['/mobiledoc/jsp/webemr/ccmr/rpm/js/service/rpmUserServices.js',
                                '/mobiledoc/jsp/webemr/ccmr/rpm/devicemonitoring/css/rpm-device-monitoring.css',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/devicemonitoring/js/rpmDeviceMonitoringController.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/css/device-monitoring.css',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/css/rpm-modals.css'
                        ]
                    }).then(function() {
                        scope.rpmDeviceMonitoringData = {
                            patientId : scope.patientId,
                            ptaCoId : scope.ptaCoId,
                            timerStatus : scope.timerStatus,
                            timerStartTime : scope.timerStartTime,
                            primaryContact : scope.primaryContact,
                            deviceType : scope.deviceType,
                            trackerType : scope.trackerType,
                            deceasedOrInactive : scope.deceasedOrInactive,
                            callbackFunction: scope.callbackFunction,
                            callFrom: scope.callFrom,
                            encounterId:scope.encounterId,
                            healowLogin: scope.healowLogin
                        };

                        $modal.open({
                            templateUrl: makeURL('/mobiledoc/jsp/webemr/ccmr/rpm/devicemonitoring/rpmDeviceMonitoringModal.html?'),
                            controller: 'rpmDeviceMonitoringController',
                            controllerAs:'rpmDeviceMtrgCtrl',
                            keyboard:false,
                            backdrop:'static',
                            windowClass: 'bluetheme device-monitoring custom-modal w1285 rpm-user-wrapper',
                            animation: true,
                            resolve : {
                                rpmDeviceMonitoringData: function() {
                                    return scope.rpmDeviceMonitoringData;
                                }
                            }
                        });
                    }, function(e) {

                    });
                });
            }
        };
    });
