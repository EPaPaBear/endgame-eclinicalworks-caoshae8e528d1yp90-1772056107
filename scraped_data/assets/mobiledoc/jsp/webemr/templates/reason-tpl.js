/* 
 * For Notes template you have to pass following parameters
 * notesKeywords = {notesAction:'',notesText:'',browseModuleName:'',showBrowseBtn:'',showTimestampBtn:''}
 * customOk and customCancle method names
 * This will be the child screen so first to include this screen you have to include keyword in parent screen.
 */
angular.module('ecw.dir.reasonSerivce',[]).service('reasonService',function(){
    return{
        getReasonOption: function(param) {
            var strReturn = "";
            $.ajax({
                url: makeURL("/mobiledoc/jsp/webemr/labs/LabsRequestHandler.jsp"),
                type: "POST",
                cache: false,
                dataType: "json",
                data: $.param(param),
                async: false,
                success: function(text) {
                    strReturn = text;
                }
            });
            return strReturn;
        }
    };
});
angular.module('ecw.dir.reason',['ecw.dir.reasonSerivce']).directive('reason',
        function(reasonService){
            return{
                restrict: 'AE',
                replace: 'true',
                templateUrl: '/mobiledoc/jsp/webemr/templates/reason-tpl.html',
                scope:{
                    content: '=content',
                    customOk: '&onCustomok',
                    customCancel: '&onCustomcancel'
                },
                link: function(scope){
                    if(!scope.content.title){
                        scope.content.title = "eClinicalworks";
                    }
                    var param = {sRequestFrom:"labsResultScreenReason",action :scope.content.action};
                    scope.reasonOptions = reasonService.getReasonOption(param);
                    scope.reasonOptions =  scope.reasonOptions.Values;
                    
                    if(scope.content.showReason && scope.reasonOptions && scope.reasonOptions[0]){
                    	scope.content.reason = scope.reasonOptions[0].Description;
                    }else{
                    	scope.content.reason = "";
                    }
                    scope.getBodyStyle = function(){
                			if(scope.content.showReason){
                				return {height : "155px"};
                			}else {
                				return {height: "75px"};
                			}
                	};
                	  scope.getContentStyle = function(){
                  			if(scope.content.showReason){
                  				return	{height : "225px !important"};
                  			}else {
                  				return	{height: "200px !important"};
                  			}
                  	};
                }
            };
        });