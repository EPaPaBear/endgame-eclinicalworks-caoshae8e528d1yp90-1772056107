angular.module('ecw.service.visionExamInlineEditService', []).service('VisionExamInlineEditService', function() {
    
    // Get Motility Section Data
    var fetchObservationFieldsSearchResults = function(propId) {
        var serverUrl = '/mobiledoc/jsp/webemr/progressnotes/usvision/visionexamination/inlineEditVisionExamService.jsp';
        var data = $.param({action: "getObservationFieldsSearchResults", "propId": propId});
        var searchData = urlPost(serverUrl, data);
        return JSON.parse(searchData);
    };
    return {        
    	fetchObservationFieldsSearchResults : fetchObservationFieldsSearchResults
    };
    
});
