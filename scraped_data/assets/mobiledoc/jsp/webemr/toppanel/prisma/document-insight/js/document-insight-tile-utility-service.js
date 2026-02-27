(() => {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('DocumentInsightTileUtilityService', [function() {
            let self = this;
            self.jumpToDocumentInsightAnnotation = (annotation = {}, isJumpToEntityEnabled) => {
                const [leftX = 0, leftY = 0] = annotation?.bottom_left ?? [];
                const width = annotation?.width ?? 0;
                const height = annotation?.height ?? 0;
                const page = annotation?.page_number ?? '1';

                if(isJumpToEntityEnabled == 0){
                    self.goToPage(page);
                    return;
                }

                window.frames['iframeView'].contentDocument.defaultView.jumpToDocumentInsightAnnotation(page,
                    [leftX , leftY , width , height ]);
            };

            self.isValidCoordinate = (coordinate, isJumpToEntityEnabled) => {
                const pageNumber = Number(coordinate?.page_number);
                if(isJumpToEntityEnabled == 0){
                    return pageNumber > 0
                }
                return coordinate && coordinate?.top_left[0] > 0 && coordinate?.top_left[1] > 0 && coordinate?.width > 0 && coordinate?.height > 0 && pageNumber > 0;
            };

            self.goToPage = pageNumber => {
                let iframeView = document.querySelector('.docDetailViewer #iframeView');
                let myWebViewer1 = iframeView.contentWindow.myWebViewer1;
                if (myWebViewer1 && myWebViewer1.instance) {
                    myWebViewer1.instance.setCurrentPageNumber(pageNumber);
                }
            }

        }]);
})();
