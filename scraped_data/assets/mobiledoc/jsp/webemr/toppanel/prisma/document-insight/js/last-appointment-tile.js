(() => {
    'use strict';

    angular.module('ecw.documentInsight')
        .directive('lastAppointmentTile', ['LastAppointmentService', '$observableService', 'DocumentInsightTileWrapperService', 'PSACService', '$ocLazyLoad', function(LastAppointmentService, $observableService, DocumentInsightTileWrapperService, PSACService, $ocLazyLoad) {
            return {
                restrict: 'E',
                scope: {},
                templateUrl: '/mobiledoc/jsp/webemr/toppanel/prisma/document-insight/html/last-appointment-tile-template.html',
                controller: ['$scope', function($scope) {
                    const vm = this;
                    vm.lastAppt = {};
                    vm.isContentLoaded = false;
                    vm.$onInit = () => {
                        vm.tileParams = DocumentInsightTileWrapperService.getDocumentInsights();
                        getLastPatientAppointment(vm.tileParams?.patientId);
                    }

                    $observableService.subscribe('refreshTiles', event => {
                        if(event?.data?.tile === 'all' || event?.data?.tile === 'lastAppointment') {
                            vm.tileParams = event?.data?.data;
                            getLastPatientAppointment(vm.tileParams?.patientId);
                        }
                    });

                    $scope.$on('$destroy', () => {
                        $observableService.unsubscribe('refreshTiles');
                    });

                    const getLastPatientAppointment = patientId => {
                        if (!patientId) {
                            vm.isContentLoaded = true;
                            return {};
                        }
                        LastAppointmentService.getLastAppointment(patientId).then(response => {
                            vm.lastAppt = response?.data || {};
                            vm.isContentLoaded = true;
                        }, () => {
                            ecwAlert("Error occurred while fetching Patient Details.");
                            vm.isContentLoaded = true;
                            return {};
                        });
                    }

                    vm.loadEncounterModalUrl = () => {
                        if(!vm.hasAccess()) {
                            // TODO: implement logic
                        }
                        showMessageIfMultipleModalInstance("div.patient-encounter[ng-controller=encounterController]", "One instance of Encounters window is already open. You cannot open another instance");
                        PSACService.checkCommonStaffPermission(vm.tileParams?.patientId, function () {
                            $ocLazyLoad.load({
                                name: 'NewEncounter',
                                files: ['/mobiledoc/jsp/webemr/toppanel/encounter.js']
                            }).then(function () {
                                vm.enclinkurl = makeURL("/mobiledoc/jsp/webemr/toppanel/Encounter-lookup.jsp?patientId=" + vm.tileParams?.patientId);
                            }, function (e) {
                            });
                        }, function () {
                            return;
                        });
                    }

                    vm.hasAccess = () =>  {
                        // TODO: logic
                        return true;
                    }

                }],
                controllerAs: 'vm'
            };
        }]);
})();