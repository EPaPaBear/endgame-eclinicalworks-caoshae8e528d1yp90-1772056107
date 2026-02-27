angular.module('milestoneWrapper', []).directive('milestoneWrapper',
    function ($ocLazyLoad) {
        return {
            restrict: 'AE',
            replace: false,
            scope: {
                module: '=',
                ptId: "=",
                ptDtl: '=',
                screen: '=',
                document:'='
            },
            link: function ($scope, element, attrs, modelCtrl) {
                $ocLazyLoad.load({
                    files: ['/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/css/milestone.css',
                        '/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/js/perfect-scrollbar.js',
                        '/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/js/angular-perfect-scrollbar.js',
                        '/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/css/perfect-scrollbar.css',
                        '/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/css/global-style.css'
                    ]
                }).then(function () {

                });
            },
            template: '<div ng-if="\'APCM\'===module" class="icon bhi-icon-flag" ng-class="{\'documented\':document}" module="" milestone-popup pt-id="ptId" ' +
                'pt-dtl="ptDtl" screen="screen"' +
                ' >' +
                '</div>'+
                '<div  ng-if="\'APCM\'!==module" class="hub-block text-center" style="width: 75px;\n  display: flex;\n  flex-direction: column;\n ' +
                ' align-items: center;\n  justify-content: center;\n  cursor: pointer;"  module="module" milestone-popup pt-id="ptId" ' +
                'pt-dtl="ptDtl" screen="\'enrolledqueue\'"' +
                ' ><span class="iconblock" style="height: 30px;\n  display: flex;\n  align-items: center;">' +
                '<i class="icon icon-patientenroll nomargin hub-list-icon" ' +
                'style="background: url(\'/mobiledoc/jsp/webemr/phm/actionHub/img/milestone_flag.png\') no-repeat;\n  width: 22px;\n  ' +
                'height: 22px;\n  display: inline-block;\n  margin-left: 0 !important;"></i>' +
                '</span><span class="iconname" style="font-size: 10px;\n  line-height: 12px;\n  margin-top: 5px;\n  height: 25px;">' +
                'Milestone</span></div>'

        };
    });