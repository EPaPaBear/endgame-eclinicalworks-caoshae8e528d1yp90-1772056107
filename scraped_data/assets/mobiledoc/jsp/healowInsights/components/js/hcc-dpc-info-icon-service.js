class HccDPCInfoIconService {

    constructor($ocLazyLoad, $http) {
        this.$ocLazyLoad = $ocLazyLoad;
        this.$http=$http;
        this.isWorklistEnable = getItemKeyValue("Pophealth_HCC_worklist", false).toUpperCase() === "YES";
    }

    openInfoPopup(elem, context, data) {
        let pdxHCCItemInfo = data;

        let _that = angular.element(elem.target);
        let clazz = '.' + context + '-smart-todo-hcc-dpc-info-popup';
        $(clazz).toggle().animate({}, 100, function () {
            $(this).position({
                of: _that,
                my: 'right top',
                at: 'right-20 top-65',
                collision: "flipfit"
            }).animate({
                "opacity": 1
            }, 100);
        });

        $(clazz + ' .hcc-dpc-info-popup-right-arrow').show().animate({}, 100, function () {
            $(this).position({
                of: _that,
                my: 'right top',
                at: 'right-21 top+10',
                collision: "flipfit"
            });
        });
        pdxHCCItemInfo.isWorklistEnable = this.isWorklistEnable;
        return pdxHCCItemInfo;
    }

    getEncounterDetails(ptId, hcc) {
        this.$http({
            method: "POST",
            url: makeURL('/mobiledoc/jsp/healowInsights/MemberInsightController.jsp'),
            data: $.param({
                action: 'getLastEncounterDetails',
                pid: ptId,
                diag: (hcc.primaryitemcode ? hcc.primaryitemcode : hcc.itemcode)
            }),
            cache: false
        }).then(function (response) {
            hcc.encDetails = response.data;
        });
    }

    hideInfoPopup(context) {
        let clazz = '.' + context + '-smart-todo-hcc-dpc-info-popup';
        $(clazz).hide();
    }

    getDPCSourceName(source) {
        if (source) {
            if (source === 'H') return 'Historical coding gap, diagnosis code was coded in the previous year, but has not been coded in the current';
            else if (source === 'S') return 'Secondary coding gap, secondary manifestation code missing for the patient’s primary condition';
            else if (source === 'M') return 'Manual Coding gap, entered by the user manually in the system';
            else if (source === 'Ex') return 'External Coding gap, coding gap received from Prisma or Medicare claims data';
            else return source;
        }
        return '';
    }

    openHCCDPCInfoPopup(elem, context, data) {
        return this.openInfoPopup(elem, context, data);
    }

}
HccDPCInfoIconService.$inject = ['$ocLazyLoad', '$http'];
angular.module('ecw.component.hi.hcc.dpc.info.icon.service', ['oc.lazyLoad'])
    .service('HccDPCInfoIconService',HccDPCInfoIconService);