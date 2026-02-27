angular.module("sunohAssistantSettingsModule", []).controller(
    'sunohAssistantSettingsController',
    function ($scope, $http, sharedServiceSunoh, $timeout) {

      $scope.checkBoxAllState = false;
      $scope.configuration = [];
      $scope.initialize = function () {
        $scope.fetchSunohAssistantCommand();
      }

      $scope.fetchSunohAssistantCommand = function () {
        $http({
          url: makeURL("/mobiledoc/modules/webemr/sunoh/assistant/commands"),
          method: 'GET'
        })
        .success(function (response) {
          let configurations = response;
          if (response.error_msg) {
            notification.show('info-msg', 'Sunoh Assistant ', response.error_msg, 4000);
            return;
          }

          const isConfiguredAlreadySaved = configurations.some(
              function (item, i) {
                if (item['configured']) {
                  return true;
                }
              });

          if (!isConfiguredAlreadySaved) {
            configurations.forEach(value => {
              value.configured = true;
            });
          }
          $scope.configurations = configurations;
          $scope.updateCheckboxAllState();
        }).error(function (error) {
          notification.show('error', '',
              'Something went wrong, please try again!', 4000);
        });

      }

      $scope.saveSunohAssistantCommand = function () {
        if ($scope.configurations.length === 0) {
          return;
        }
        let configurations = $scope.configurations.filter(config => config.configured === true);
        let params = JSON.stringify(configurations);
        $http({
          url: makeURL("/mobiledoc/modules/webemr/sunoh/assistant/command"),
          method: 'POST',
          data: params,
          headers: {
            'Content-Type': 'application/json'
          }
        })
        .success(function (response) {
          sharedServiceSunoh.sunohAssistantSettingsModal.close();
        }).error(function (error) {
          notification.show('error', '',
              'Something went wrong, please try again!', 4000);
        });
      }

      $scope.isConfigDirty = false;

      $scope.checkAssistantConfiguration = function (type) {
        if (type === 'all') {
          let checkBoxAllState = !$scope.checkBoxAllState;
          angular.forEach($scope.configurations,
              function (config) {
                config.configured = checkBoxAllState;
              });
        } else {
          $scope.updateCheckboxAllState();
        }
        $scope.isConfigDirty = true;
      }

      $scope.cancelAssistantConfiguration = function (type) {
        if(type === 'closewithoutsave'){
          sharedServiceSunoh.sunohAssistantSettingsModal.close();
          return;
        }
        if(type === 'closedropdown'){
          $('#endSunohAssistantSetting').hide();
          return;
        }
        if(type === 'close'){
          sharedServiceSunoh.sunohAssistantSettingsModal.close();
          return;
        }
        if($scope.isConfigDirty){
          $('#endSunohAssistantSetting').show();
        } else {
          sharedServiceSunoh.sunohAssistantSettingsModal.close();
        }
      }

      $scope.updateCheckboxAllState = function() {
        $timeout(function() {
          const totalChecked = $scope.configurations.filter(config => config.configured).length;
          const total = $scope.configurations.length;
          $scope.checkBoxAllState = (total === totalChecked);
        });
      }

    })