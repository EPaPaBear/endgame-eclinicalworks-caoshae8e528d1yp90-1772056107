angular.module('rpm.viewNotes.dir', ['ecw.datatruncUtilityModule', 'ecw.dir.patientidentifier'])
    .directive('rpmNotesModal', function($http, $modal, $ocLazyLoad) {
        return {
            restrict : 'AE',
            replace : 'true',
            scope : {
                patientId : '=',
                encounterId : '=',
                showImportBtn : '=',
                callbackFunction: '&'
            },
            link : function(scope, element, attrs, ngModelCtrl) {
                element.click(function(){
                    $ocLazyLoad.load({
                        name: 'openSmartNote',
                        files: [
                            '/mobiledoc/jsp/webemr/ccmr/rpm/js/service/rpmUserServices.js',
                            '/mobiledoc/jsp/webemr/templates/keywords-tpl.js',
                            '/mobiledoc/jsp/webemr/js/ecw.dir.patientidentifier.js',
                            '/mobiledoc/jsp/webemr/js/globalframeworkService.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/js/controller/rpmNotesModalController.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/js/directive/printDirective.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/css/rpm-smart-note.css'
                        ]
                    }).then(function() {
                        scope.viewNotesData = {
                            patientId : scope.patientId,
                            encounterId : scope.encounterId,
                            showImportBtn : scope.showImportBtn,
                            callbackFunction: scope.callbackFunction
                        };

                        $modal.open({
                            templateUrl: makeURL('/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/views/rpmNotesModal.html?'),
                            controller: 'rpmNotesController',
                            controllerAs:'rpmNotesCtrl',
                            backdrop: 'static',
                            windowClass: 'modal-style bluetheme w1280 rpm-user-wrapper',
                            animation: true,
                            resolve : {
                                viewNotesData: function() {
                                    return scope.viewNotesData;
                                }
                            }
                        });
                    }, function(e) {

                    });
                });
            }
        };
    });