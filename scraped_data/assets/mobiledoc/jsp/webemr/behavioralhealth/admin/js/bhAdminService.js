angular.module('bhAdminService',[]).factory("bhAdminService",['$http', function($http) {
        let bhScreeningCalledFrom = '';

        return {
            getAllCategory:function()
            {
                var url = '/mobiledoc/behavioralhealth/BhAdminCategories/getAllCategory';
                var obj={};
                return httpPostWithData(url,obj);
            },
            addOrUpdateCategory:function(requestParams) {
                var url = '/mobiledoc/behavioralhealth/BhAdminCategories/addOrUpdateCategory';
                return httpPostWithData(url, requestParams);
            },
            updateCategoryIndex:function (requestParams) {
                var url = '/mobiledoc/behavioralhealth/BhAdminCategories/updateCategoryIndex';
                return httpPostWithData(url, requestParams);
            },
            deleteSelectedCustomCategory: function (requestParams) {
                var url = '/mobiledoc/behavioralhealth/BhAdminCategories/deleteSelectedCustomCategory';
                return httpPostWithData(url, requestParams);
            },
            validateCategoryProgramMapping: function (requestParams) {
                var url = '/mobiledoc/behavioralhealth/BhAdminCategories/validateCategoryProgramMapping';
                return httpPostWithData(url, requestParams);
            },
            setBhScreeningCalledFrom: function setBhScreeningCalledFrom(calledFrom){
                bhScreeningCalledFrom=calledFrom;
            },
            getBhScreeningCalledFrom: function getBhScreeningCalledFrom(calledFrom){
                return bhScreeningCalledFrom;
            },
            getScreeningStructDataMigrationStatus:function(){
                var url = '/mobiledoc/behavioralhealth/BhAdminCategories/getScreeningStructDataMigrationStatus';
                return httpPostWithData(url, {});
            },
            migrateScreeningStructDataMigration:function(){
                var url = '/mobiledoc/behavioralhealth/BhAdminCategories/migrateScreeningStructDataMigration';
                return httpPostWithData(url, {});
            }
        }
        function httpPostWithData(url, data){
            return $http({
                headers: {
                    'Content-Type': 'application/json; charset=UTF-8'
                },
                method: 'POST',
                url: url,
                data: data
            });
        }
        function httpGET(url) {
            return $http({
                method: "GET",
                url: url,
                cache: false
            });
        }
}]);