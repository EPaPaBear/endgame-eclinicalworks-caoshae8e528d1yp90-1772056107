class PDInfoIconService {

    constructor($http) {
        this.$http=$http;
    }

    openPDInfoPopup(elem, context, infodata, source) {
        let pdInfo = JSON.parse(infodata);
        if (pdInfo) {
            let findHighestOrder = 0;
            angular.forEach(pdInfo, function(value, key) {
                if (value.order > findHighestOrder) {
                    findHighestOrder = value.order;
                }
            });

            let sourceObj = {};
            sourceObj.key = "Source";
            sourceObj.order = findHighestOrder + 1;
            sourceObj.value = source;
            pdInfo.push(sourceObj);

            let classs = '.' + context + '-pd-item-info';
            let _that = angular.element(elem.target);
            $(classs).toggle().animate({}, 100, function () {
                $(this).position({
                    of: _that,
                    my: 'right top',
                    at: 'right-20 top',
                    collision: "flipfit"
                }).animate({
                    "opacity": 1
                }, 100);
            });
            classs = classs + ' .pd-info-popup-arrow';
            $(classs).show().animate({}, 100, function () {
                $(this).position({
                    of: _that,
                    my: 'right top',
                    at: 'right-21 top+12',
                    collision: "flipfit"
                });
            });
        }
        return pdInfo;
    }

    hidePDInfoPopup(context) {
        let classs = '.' + context + '-pd-item-info';
        $(classs).hide();
    }

    async getSupportingEvidenceDetails(pid,itemcode,evidenceList){
        await this.$http({
            method: 'POST',
            url: makeURL('/mobiledoc/jsp/analytics/hccRequestHandler.jsp'),
            data: $.param({
                callingFor: "fetchEvidence",
                patientId: pid,
                suspectCode: itemcode,
            }),
            cache: false
        }).then(function (response) {
            evidenceList.data = response.data;
        });
    }

}
PDInfoIconService.$inject = ['$http'];
angular.module('ecw.component.hi.pd.info.icon.service', [])
    .service('PDInfoIconService', PDInfoIconService)