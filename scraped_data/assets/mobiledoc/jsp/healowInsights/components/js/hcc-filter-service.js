class HccFilterService {

    constructor($ocLazyLoad) {
        this.$ocLazyLoad = $ocLazyLoad;
    }

    isICDInsufficient = function(obj) {
        return obj.icd_status && obj.icd_status.toLowerCase() === 'insufficient';
    };
    IsPresentInProblemList = function(obj) {
        return obj.IsPresentInProblemList && obj.IsPresentInProblemList === true;
    };
    isCMSAccepted = function(obj) {
        let cmsAccepted = false;
        let withinCurrentYear = false;
        if (obj.infodata && obj.request_source_type === 'PAYOR_HOSTED') {
            let infoList = JSON.parse(obj.infodata);
            if (infoList.length > 0) {
                for (let item = 0, len = infoList.length; item < len; item++) {
                    if (!cmsAccepted && infoList[item].key && infoList[item].key.startsWith("CMS Accepted")) {
                        cmsAccepted = true;
                    }
                    if (!withinCurrentYear && infoList[item].key === 'Within Current Year' && infoList[item].value && infoList[item].value.toLowerCase() === 'yes') {
                        withinCurrentYear = true;
                    }
                }
            }
        }
        return cmsAccepted && withinCurrentYear;
    };
    isAccepted = function(obj) {
        let cmsAccepted = false;
        let withinCurrentYear = false;
        if (obj.infodata && obj.request_source_type === 'PAYOR_HOSTED') {
            let infoList = JSON.parse(obj.infodata);
            if (infoList.length > 0) {
                for (let item = 0, len = infoList.length; item < len; item++) {
                    if (!cmsAccepted && infoList[item].key && infoList[item].key.startsWith("CMS Accepted")) {
                        cmsAccepted = true;
                    }
                    if (!withinCurrentYear && infoList[item].key === 'Within Current Year' && infoList[item].value && infoList[item].value.toLowerCase() === 'yes') {
                        withinCurrentYear = true;
                    }
                }
            }
        }
        return !cmsAccepted && withinCurrentYear;
    };

}
HccFilterService.$inject = ['$ocLazyLoad'];
angular.module('ecw.component.hi.hcc.filter.service', ['oc.lazyLoad'])
    .service('HccFilterService',HccFilterService);