angular.module('insightActionServiceApp', [])
.service('insightActionDataService', function(){
    let sharedData = {
        patientId: 0,
        actionName: '',
        templateName: '',
        parentId: '',
        resultData:{},
        screenName: '',
        directiveScope:undefined

    }
    return {
        setPatientId: function(patientId) {
            sharedData.patientId = patientId;
        },
        setActionName: function(actionName) {
            sharedData.actionName = actionName;
        },
        getPatientId: function(){
            return sharedData.patientId;
        },
        getActionName: function(){
            return sharedData.actionName;
        },
        setTemplate: function(templateName) {
           sharedData.templateName = templateName;
        },
        getTemplate: function() {
           return sharedData.templateName;
        },
        setParentId: function(parentId) {
           sharedData.parentId = parentId;
        },
        getParentId: function(){
            return sharedData.parentId;
        },
        setResultData: function(resultData){
            sharedData.resultData = resultData;
        },
        getResultData: function(){
            return sharedData.resultData;
        },
        setScreeName: function(screenName) {
            sharedData.screenName = screenName;
        },
        getScreenName: function(){
            return sharedData.screenName;
        },
        setDirectiveScope: function(directiveScope) {
            sharedData.directiveScope = directiveScope;
        },
        getDirectiveScope: function(){
            return sharedData.directiveScope;
        }
     }
});