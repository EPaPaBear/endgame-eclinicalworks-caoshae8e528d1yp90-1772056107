// summary-tile.js

(() => {
    'use strict';

    angular.module('ecw.documentInsight')
        .directive('summaryTile', ['SummaryService', '$observableService', 'DocumentInsightTileWrapperService', 'DocumentInsightTileUtilityService', function(SummaryService, $observableService, DocumentInsightTileWrapperService, DocumentInsightTileUtilityService) {
            return {
                restrict: 'E',
                scope: {},
                templateUrl: '/mobiledoc/jsp/webemr/toppanel/prisma/document-insight/html/summary-tile-template.html',
                controller: ['$scope', function($scope) {
                    const vm = this;
                    vm.data = {};
                    vm.isContentLoaded = false;
                    vm.tileParams = DocumentInsightTileWrapperService.getDocumentInsights();

                    $observableService.subscribe('refreshTiles', event => {
                        if(event?.data?.tile === 'all' || event?.data?.tile === 'summary') {
                            vm.tileParams = event?.data?.data;
                            vm.summary = event?.data?.data?.summary;
                            vm.summaryHtml = vm.summary? readFieldsFromJson(vm.summary.find(item => item.key === 'Highlights')?.summary) : "<span style=\"color: #989898; font-style: italic;\" > Failed to generate Highlights</span>";
                            vm.isContentLoaded = true;
                        }
                    });

                    const PAGE_NUMBER_REGEX = "(?:Page|Pages|P|p|PAGE|PAGES)?\\s*[-.]?\\s*(\\d+)(?:\\s*-\\s*(?:Page|Pages|P|p|PAGE|PAGES)?\\s*[-.]?\\s*(\\d+))?";
                    const readFieldsFromJson = (summarizationContent, regexPattern = PAGE_NUMBER_REGEX) => {
                        try {
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(summarizationContent, "text/html");
                            const tocTable = doc.querySelector('table[id="toc"]');
                            let pageNumbers = new Set();
                            if (tocTable) {
                                const rows = tocTable.querySelectorAll('tr');
                                rows.forEach(row => {
                                    const cells = row.querySelectorAll('td');
                                    if (cells.length === 2) {
                                        const pageNumberText = cells[1].textContent.trim();
                                        const regex = new RegExp(regexPattern, 'ig');
                                        let match;
                                        while ((match = regex.exec(pageNumberText)) !== null) {
                                            pageNumbers.add({ start: match[1], end: match[2] });
                                        }
                                    }
                                });
                            }

                            let summaryContent = new XMLSerializer().serializeToString(doc);

                            pageNumbers.forEach(pageNumber => {
                                const displayText = pageNumber.end ? `${pageNumber.start}-${pageNumber.end}` : pageNumber.start;
                                const regex = new RegExp(`>(?:Page|Pages|P|p|PAGE|PAGES)?\\s*[-.]?\\s*\\b${displayText}\\b<`, 'g');
                                summaryContent = summaryContent.replace(regex, `><span class='page-link blue_txt' ng-click='summaryCtrl.goToPage(${pageNumber.start})'>[${displayText}]</span><`);
                            });
                            return summaryContent;
                        } catch (e) {
                            return summarizationContent;
                        }
                    }


                    vm.goToPage = DocumentInsightTileUtilityService.goToPage;

                    $scope.$on('$destroy', () => {
                        $observableService.unsubscribe('refreshTiles');
                    });
                }],
                controllerAs: 'summaryCtrl'
            };
        }]);
})();
