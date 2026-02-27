(function(){

	function toDoListLogsController($modalInstance,requestParam,todoListService,todolistSharedService){
		let vm  = this;
		const DATE_RANGE_IN_MONTHS = 9;
		vm.toDoListLogObj = {
			"sortBy": 0,
			"sortOrder": "DESC",
			patientId: requestParam['patientId'],
			todoStandaloneContext:requestParam['isTodoStandaloneContext'],
			pageNo: 1,
			rowPerPage: 17,
			actionTakenTabId: -1,
			performedOn: moment().format('MM/DD/YYYY'),
			fromDate: moment().subtract(DATE_RANGE_IN_MONTHS, 'months').format('MM/DD/YYYY')
		};
		vm.logDetails = {};
		vm.toDoListLogObjCopy = angular.copy(vm.toDoListLogObj);

		vm.showDatePicker = function (event){
			$(event.currentTarget).parent().parent().find('input[type="text"]').datepicker("show");
		}
		vm.close = function(){
			$modalInstance.close();
		}
		vm.sortUserLog = function(sortBy){
			vm.toDoListLogObj.sortBy = sortBy;
			vm.toDoListLogObj.sortOrder = vm.toDoListLogObj.sortOrder === 'DESC' ? "ASC" : "DESC";
			vm.getLogs();
		};

		vm.filterByPerformedOn = function () {
			let performedOn = moment(vm.toDoListLogObj.performedOn, 'MM/DD/YYYY');
			vm.toDoListLogObj.fromDate = performedOn.subtract(DATE_RANGE_IN_MONTHS, 'months').format('MM/DD/YYYY');
			let isFutureDate = performedOn.isAfter(moment())
			if (todolistSharedService.isUNE(vm.toDoListLogObj.performedOn)
				|| (vm.toDoListLogObj.performedOn.length === 10 && performedOn.isValid() && !isFutureDate)) {
				vm.toDoListLogObj.pageNo = 1;
				vm.getLogs();
			}
		};

		vm.filterLogs = function (event) {
			if (event && event.keyCode === 13 && !_.isEqual(vm.toDoListLogObjCopy,vm.toDoListLogObj)) {
				vm.toDoListLogObj.pageNo = 1;
				vm.getLogs();
			}
		};

		vm.getLogs = function (){
			todoListService.getLogs(vm.toDoListLogObj,function (response) {
				vm.logDtls = response.logDtls;
				vm.toDoListLogObjCopy = angular.copy(vm.toDoListLogObj);
			});
		}
		vm.getLogs();
	}
	angular.module('toDoListLogs', ['ui.bootstrap','ecw.pagination','ecw.dir.maskdateinput'])
		.controller('toDoListLogsController',toDoListLogsController)

})();