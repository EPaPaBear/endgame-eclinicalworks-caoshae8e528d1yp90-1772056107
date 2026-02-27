(function() {
    angular.module('prismaAppAccessLogService', [])
    .factory('prismaAccessLogService', PrismaAccessLogService);
    function PrismaAccessLogService( $http ) {
        return {
            getAccessLog				: getAccessLog,
        }
        function getAccessLog(patientId, currentPage, recordsPerPage){
            return $http({
                method: "POST",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: '/mobiledoc/prisma/accesslog/getPrismaAccessLog',
                data: $.param({patientId:patientId, currentPage:currentPage, recordsPerPage:recordsPerPage})
            });
        }
    }
})()