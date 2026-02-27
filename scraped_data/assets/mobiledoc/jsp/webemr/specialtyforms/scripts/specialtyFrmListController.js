angular.module('SpecFormListModule',['oc.lazyLoad'])
.controller('SpecFormListCtrl', function($scope,$http,$ocLazyLoad) {
	
	$scope.savedFormList = [];
	
	$scope.selectedForm = {};
	
	$scope.loadData = function (){
		try {
            var x2js = new X2JS();
            var jsonData = x2js.xml_str2json(specialtyForm_specialtyFormList_xmlData);
            var lst = jsonData.Envelope.Body['return'].SPLFORMS;
            
            for(var i = 0 ; i < lst.length ; i++){
            	var savedform = {};
            	savedform.formid = lst[i].formid;
            	savedform.encid = lst[i].encid;
            	savedform.comment = lst[i].comment;
            	savedform.formname = lst[i].formname;
            	savedform.formtypeid = lst[i].formtypeid;
            	savedform.formurl = lst[i].formurl;
            	savedform.modifieddate = lst[i].modifieddate;
            	
            	$scope.savedFormList.push(savedform);
            }
        } catch (err) {
			$scope.savedFormList = [];
        }
	};
	
	$scope.selectForm = function(sf) {
        $(".icon_chk:not(#icon_" + sf.formid + ")").css("display", "none");
        $("#icon_" + sf.formid).css("display", "block");
        $scope.selectedForm = sf;

    };

    $scope.updateForm = function() {
    	if($scope.selectedForm.formid == undefined){
    		ecwAlert("Please select the item you want to edit.");
    		return;
    	}

    	$ocLazyLoad.load({
			name: 'specFormModule_pnh',
			files: ['/mobiledoc/jsp/ascWeb/Views/progressnotes/pnpanel/socialhx/specialtyforms/scripts/specFrmCtrl_pnh.js'],
			cache: false
		}).then(function() {       	         
			var url = makeURL('/mobiledoc/jsp/webemr/specialtyforms/specFormContainer_pnh.jsp?encounterid=' + $scope.encounterId+ '&patientid=' + $scope.patientId+"&userid="+global.TrUserId+
								"&formid="+$scope.selectedForm.formid+"&formtypeid="+ $scope.selectedForm.formtypeid+"&formurl="+encodeURIComponent($scope.selectedForm.formurl));
			$scope.specFormUrl = url;
		}, function(e) {
			console.log('call funtiion :: '+e);
		});		 
		$(".modal-backdrop").css('position', 'relative');      
    };
    
    $scope.openFormList = function (){
    	
    };
	
	$scope.closeModal = function(id){
		$("#"+id).modal("hide");
	};
});