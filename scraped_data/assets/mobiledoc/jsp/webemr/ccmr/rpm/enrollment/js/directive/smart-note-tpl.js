angular.module('openSmartNoteModalDirective', ['ecw.datatruncUtilityModule', 'ecw.dir.patientidentifier']).directive('smartNoteModal',
    function($http, $modal, $ocLazyLoad) {
        return {
            restrict : 'AE',
            replace : 'true',
            scope : {
                patientId : '=',
                isViewOnly :'=',
                notes :'=',
                subject: '=',
                tags :'=',
                tagColors :'=',
                devices :'=',
                editMode : '=',
                noteId: '=',
                callbackFunction: '&'
            },
            link : function(scope, element, attrs, ngModelCtrl) {
                element.click(function(){
                    $('.action-hub-modal').remove();
                    $ocLazyLoad.load({
                        name: 'openSmartNote',
                        files: [
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/js/controller/smart-note-ctrl.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/js/service/rpmUserServices.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/timer/directive/rpmViewFullNotes-tpl.js',
                            '/mobiledoc/jsp/webemr/templates/keywords-tpl.js',
                            '/mobiledoc/jsp/webemr/js/ecw.dir.patientidentifier.js',
                            '/mobiledoc/jsp/webemr/js/globalframeworkService.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/js/directive/printDirective.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/css/rpm-smart-note.css'
                        ]
                    }).then(function() {
                        scope.smartNoteData = {
                            patientId : scope.patientId,
                            devices :scope.devices,
                            tags: scope.tags,
                            tagColors: scope.tagColors,
                            notes :scope.notes,
                            subject:scope.subject,
                            isViewOnly: scope.isViewOnly,
                            editMode: scope.editMode,
                            noteId: scope.noteId,
                            callbackFunction: scope.callbackFunction,
                        };

                        $modal.open({
                            templateUrl: makeURL('/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/views/smart-note-modal.html?'),
                            controller: 'smartNoteModalController',
                            controllerAs:'smartNoteModalCtrl',
                            backdrop: 'static',
                            windowClass: 'disenroll custom-modal w720',
                            animation: true,
                            resolve : {
                                smartNoteData: function() {
                                    return scope.smartNoteData;
                                }
                            }
                        });
                    }, function(e) {

                    });
                });
            }
        };
    });