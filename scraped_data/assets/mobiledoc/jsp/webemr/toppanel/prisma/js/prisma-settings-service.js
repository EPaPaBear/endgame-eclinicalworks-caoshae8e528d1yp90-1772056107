angular.module('prismaSettingsServiceModule', []).service("PrismaSettingsService",
    ["$http", "$q", "$filter","PRISMA_CONSTANT", function ($http, $q, $filter, PRISMA_CONSTANT) {

        let errMessage = "Something went wrong, please try again later.";
        return ({
            getPrismaUserBundles : getPrismaUserBundles,
            deletePrismaUserBundle : deletePrismaUserBundle,
            createPrismaUserBundle : createPrismaUserBundle,
            getEcwBundlesSpecialities: getEcwBundlesSpecialities,
            getSectionOrderConfig: getSectionOrderConfig,
            saveSectionOrderConfig:saveSectionOrderConfig,
            getHighlightsSectionSettings: getHighlightsSectionSettings,
            saveHighlightsSectionSettings: saveHighlightsSectionSettings,
            getSummarySectionSettings: getSummarySectionSettings,
            saveSummarySectionSettings: saveSummarySectionSettings
        })

        function getPrismaUserBundles(currentPage, recordPerPage, bundleNamePrefixString, isRequestForEcwBundle, bundleSpeciality) {
            let data = {
                currentPage: currentPage,
                recordsPerPage: recordPerPage,
                bundleNamePrefixString: bundleNamePrefixString,
                isRequestForEcwBundle: isRequestForEcwBundle,
                bundleSpeciality: bundleSpeciality
            };
            let request = httpPost('/mobiledoc/prisma/bundle/getPrismaUserBundles', data);
            return request.then(handleSuccessWithResponseData, handleCommonError);
        }

        function getEcwBundlesSpecialities() {
            let request = httpPost('/mobiledoc/prisma/bundle/getEcwBundlesSpecialities');
            return request.then(handleSuccessWithResponseData, handleCommonError);
        }
        function deletePrismaUserBundle(bundleId) {
            let data = {bundleId: bundleId};
            let request = httpPost('/mobiledoc/prisma/bundle/deletePrismaUserBundle', data);
            return request.then(handleSuccessWithResponseData, handleCommonError);
        }
        function createPrismaUserBundle( bundle, bundleId) {
            let data = {bundle: bundle};
            let request = httpPost('/mobiledoc/prisma/bundle/createPrismaUserBundle', data);
            return request.then(handleSuccessWithResponseData, handleCommonError);
        }
        function getSectionOrderConfig() {
            let request = httpPost('/mobiledoc/prisma/sectionOrderConfig/getSectionOrderConfig');
            return request.then(handleSuccessWithResponseData, handleCommonError);
        }
        function saveSectionOrderConfig(sendObject) {
            let request = httpPost('/mobiledoc/prisma/sectionOrderConfig/saveSectionOrderConfig',sendObject);
            return request.then(handleSuccessWithResponseData, handleCommonError);
        }
        function getHighlightsSectionSettings(sendObject) {
            let request = httpPost('/mobiledoc/prisma/summarization/getHighlightsSectionSettings',sendObject);
            return request.then(handleSuccessWithResponseData, handleCommonError);
        }

        function saveHighlightsSectionSettings(sendObject) {
            let request = httpPost('/mobiledoc/prisma/summarization/saveHighlightsSectionSettings',sendObject);
            return request.then(handleSuccessWithResponseData, handleCommonError);
        }

        function getSummarySectionSettings() {
            let request = httpPost('/mobiledoc/prisma/nonaihighlights/getPrismaCollapsableSectionSettings', {});
            return request.then(handleSuccessWithResponseData, handleCommonError);
        }
        function saveSummarySectionSettings(data) {
            let request = httpPost('/mobiledoc/prisma/nonaihighlights/saveSummarySectionSettings', data);
            return request.then(handleSuccessWithResponseData, handleCommonError);
        }

        function httpPost(url, data) {
            return $http({
                method: "post",
                headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: makeURL(url),
                data: $.param(data)
            });
        }

        function httpPostRequestBody(url, data) {
            return $http({
                method: "POST",
                url: makeURL(url),
                data: data
            });
        }

        function handleSuccessWithResponseData(response) {
            let res = response.data;
            if (res) {
                return $q.resolve(res);
            }
        }
        function handleCommonError(response) {
            if (!angular.isObject(response.data) || !response.data.message) {
                return $q.defer().reject(errMessage);
            }
            return $q.defer().reject(response.data.message);
        }
    }])