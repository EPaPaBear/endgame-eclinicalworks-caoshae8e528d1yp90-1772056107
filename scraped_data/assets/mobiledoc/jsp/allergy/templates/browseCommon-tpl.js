
angular.module('ecw.dir.browsecommon', []).
        directive('browsecommon',
                function() {
                    return {
                        restrict: 'AE',
                        replace: 'true',
                        templateUrl: '/mobiledoc/jsp/allergy/templates/browseCommon-tpl.html',
                        scope: {
                            classname: '@',
                            custombrowseCommon: '&onBrowsecommon'
                        }
                    };
                });

