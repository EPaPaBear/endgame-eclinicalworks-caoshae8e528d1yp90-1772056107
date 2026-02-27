(function () {
  angular.module('ecw.service.BirthVitalsService',['ecw.service.VitalsService', 'oc.lazyLoad'])
  .service('BirthVitalsService',function($http,$q,$ocLazyLoad,$modal,VitalsService){

    function getAuditLogs(patientId){
      return $http({
        method: 'POST',
        url: '/mobiledoc/clinicaldocumentation/vitals/getAuditLogs/'+patientId
      })
    }

    function getBirthVitals(patientId){
      return $http({
        method: 'POST',
        url: '/mobiledoc/clinicaldocumentation/vitals/getBirthVitals/'+patientId
      })
    }

    function saveBirthVitals(saveBirthVitals){
      return $http({
        method: 'POST',
        url: '/mobiledoc/clinicaldocumentation/vitals/setBirthVitals',
        data: saveBirthVitals
      })
    }

    function getPercentageWtChange(patientId, weight){
      return $http({
        method: 'POST',
        url: '/mobiledoc/clinicaldocumentation/vitals/getPercentageWtChange',
        data: {patientId:patientId, weight:weight},
      })
    }


    function saveDisplayPNState(saveDisplayPNState){
      return $http({
        method: 'POST',
        url: '/mobiledoc/clinicaldocumentation/vitals/update/displayOnPNState',
        data: saveDisplayPNState
      })
    }

    function loadBirthVitalsRangeData(patientSex) {
      const deferred = $q.defer();
      VitalsService.loadVitalsRangeForAll(0, 'M', patientSex).then(
          function (rangeArray) {
            if (rangeArray && rangeArray.status && rangeArray.status===200 && rangeArray.data) {
              deferred.resolve(VitalsService.processVitalRange(rangeArray.data));
            } else {
              deferred.reject();
            }
          }, function () {
            deferred.reject();
          });
      return deferred.promise;
    }

    function openBirthVitalsLogsPopUp(patientId,patientIdentifier,isEditableBirthVitals){
      return getAuditLogs(patientId)
      .then(function (response) {
        if (response && response.status === 200) {
          return showAuditLogsPopup(response.data,patientIdentifier,isEditableBirthVitals);
        } else {
          return $q.reject();
        }
      }, function () {
        return $q.reject();
      });
    }

    function showAuditLogsPopup(auditLogsData,patientIdentifier,isEditableBirthVitals) {
      return $ocLazyLoad.load({
        name: 'BirthVitalsAuditLogs',
        files: [
            '/mobiledoc/jsp/webemr/progressnotes/vitals/birthvitals/birthvitalsauditlog.css',
            '/mobiledoc/jsp/webemr/progressnotes/vitals/birthvitals/birthvitalsauditlogscontroller.js']
      }).then(function () {
        return $modal.open({
          templateUrl: '/mobiledoc/jsp/webemr/progressnotes/vitals/birthvitals/birthvitalsauditlogs.html',
          controller: 'BirthVitalsAuditLogsController as birthVitalsLogsCtrl',
          windowClass: 'modal fade custom-modal bluetheme',
          backdrop: "static",
          keyboard: false,
          resolve: {
            patientIdentifier: function () {
              return patientIdentifier;
            },
            auditLogsData: function () {
              return auditLogsData;
            },
            isEditableBirthVitals: function(){
              return isEditableBirthVitals;
            }
          }
        });
      }, function () {
        return $q.reject();
      });
    }

    return {
      getAuditLogs: getAuditLogs,
      saveBirthVitals: saveBirthVitals,
      getBirthVitals: getBirthVitals,
      loadBirthVitalsRangeData: loadBirthVitalsRangeData,
      saveDisplayPNState: saveDisplayPNState,
      openBirthVitalsLogsPopUp: openBirthVitalsLogsPopUp,
      getPercentageWtChange: getPercentageWtChange
    }
  });
})();