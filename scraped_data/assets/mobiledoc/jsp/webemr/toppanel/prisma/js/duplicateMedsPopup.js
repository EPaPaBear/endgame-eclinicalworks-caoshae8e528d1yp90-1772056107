angular.module('prisma.clinicalInsights.medsDeduplicationToolTip',[]).directive('medDeduplicationToolTip', ($compile) => {
    return {
        restrict: 'AE',
        replace: true,
        template: 	`<i class="icon mr5 " ng-class="icon" title="Duplicates found" ng-click="onClickFn()"></i>`,
        scope      : {
            data: '=',
            icon: '@',
            parentElement: '@',
            header: '@',
            headerLabel: '@'
        },
        link: function(vm, elem){
            const classSelector = '.prisma-ci-dir-list-tooltip';
            if (angular.element(classSelector).length === 0) {
                const divElement  = document.createElement("div");
                divElement.className = "prisma-ci-dir-list-tooltip"
                angular.element(vm.parentElement).append(divElement);
            }
            vm.capitalize = string => {
                string = string == null ? '' : String(string);
                return string ? (string.charAt(0).toUpperCase() + string.slice(1).toLowerCase()) : string;
            };
            vm.data?.forEach(med => {
                med.medicationName = vm.capitalize(med.medicationName);
            });
            vm.onClickFn = () => {
                const popupHtml = _createPopUpHtml();
                angular.element(classSelector).empty();
                // provide top div id
                angular.element(classSelector).append($compile(popupHtml)(vm));
                const _that = elem;
                angular.element(classSelector).toggle().animate({}, 100, function () {
                    angular.element(this).position({
                        of: _that,
                        my: 'left top',
                        at: 'left top+22',
                        collision: "flipfit",
                        within: ".prismaview"
                    }).animate({
                        "opacity": 1
                    }, 100)
                });
            };

            function _createPopUpHtml(){
                return `<div ng-mouseenter="toggleClinicalInsightPopupMed($event,true);" ng-mouseleave="toggleClinicalInsightPopupMed($event,false)" > 
                    <div class="mb5 fntblde" >${vm.headerLabel?vm.headerLabel + ':':''}  <span class="fw900">${vm.header?vm.header:''}</span>
                    <span class="pull-right" ><i class="icon icon-close" ng-click='closePopupInClinicalInsightMed($event)'></i></span>
                    </div>
                        <table class="table table-bordered nomargin">
                            <div class="tablehead">
                                    <thead>
                                        <tr class="nobrdrbtm">
                                            <th class="w75p">Source</th>
                                            <th class="w75p">Medication Name</th>
                                            <th class="w75p">Code</th>
                                            
                                        </tr>
                                    </thead>
                            </div>
                            <div class="tablebody">
                                <tbody>                           
                                    ${vm.data?.map(med => `<tr>   
                                    <td class="w8p" style="min-width: 38px;">
                                        ${med?.source === 'e' ? `<i class="icon squarearrow"/>` : ``}
                                        ${med?.source === 'i' ? `<i class="icon internalarrow"/>` : ``}
                                    </td>   
                                    <td class="w75p">${med?.medicationName}</td>         
                                        <td class="w75p">${med?.ndcCode}</td>
                                                                      
                                    </tr>`).join("")}
                                </tbody>                       
                            </div>
                        </table>
                    
                </div>`;
            }
        },
        controller: function ($scope) {
            $scope.closePopupInClinicalInsightMed = function () {
                angular.element('.prisma-ci-dir-list-tooltip').hide();
            }
            $scope.toggleClinicalInsightPopupMed = function (event, toggleDisplay) {
                if (toggleDisplay) {
                    angular.element('.prisma-ci-dir-list-tooltip').show();
                } else {
                    angular.element('.prisma-ci-dir-list-tooltip').hide();
                }
                event.stopPropagation();
            }
        }
    }
})