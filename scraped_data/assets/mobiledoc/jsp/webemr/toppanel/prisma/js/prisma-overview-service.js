(function() {
    angular.module('prismaAppOverviewService', [])
        .factory('prismaOverviewService', PrismaOverviewService);
    function PrismaOverviewService( $http ) {
        return {
            getActors				: getActors,
            getCumulativeSummary    : getCumulativeSummary
        }
        function getActors(request){
            return $http({
                method: "POST",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: '/mobiledoc/prisma/overview/getEhxRightPaneActors',
                data: $.param(request)
            });
        }
        function getCumulativeSummary(request){
            return $http({
                method: "POST",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: '/mobiledoc/jsp/dashboard/geteHXOverviewData.jsp',
                data: $.param(request)
            });
        }
    }
})()