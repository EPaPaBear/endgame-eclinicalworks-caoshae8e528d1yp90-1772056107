class CIPCInfoIconActionService {

    openCIPCInfoPopup(elem, context, createddate, infodata, payerName) {
        let classs = '#' + context + '-cipc-item-info-popup';
        let pdxitemInfo = JSON.parse(infodata);
        if (pdxitemInfo.length > 0) {
            angular.forEach(pdxitemInfo, function (item) {
                if (item.key === 'Source') {
                    item.value = payerName;
                }
            });
        }
        let data = {};
        data.key = "Date Received";
        data.value = createddate;
        data.order = 2;
        pdxitemInfo.splice(1, 0, data);

        let _that = angular.element(elem.target);
        $(classs).toggle().animate({}, 100, function () {
            $(this).position({
                of: _that,
                my: 'right top',
                at: 'right-20 top-14',
                collision: "flipfit"
            }).animate({
                "opacity": 1
            }, 100);
        });
        classs = classs + ' .cipc-info-arrow';
         $(classs).show().animate({}, 100, function () {
             $(this).position({
                 of: _that,
                 my: 'right top',
                 at: 'right-21 top+12',
                 collision: "flipfit"
             });
         });
        return pdxitemInfo;
    }

    hideInfoPopup(context) {
        let classs = '#' + context + '-cipc-item-info-popup';
        $(classs).hide();
    }

}
CIPCInfoIconActionService.$inject = [];
angular.module('ecw.component.hi.cipc.info.icon.service', [])
    .service('CIPCInfoIconActionService', CIPCInfoIconActionService)