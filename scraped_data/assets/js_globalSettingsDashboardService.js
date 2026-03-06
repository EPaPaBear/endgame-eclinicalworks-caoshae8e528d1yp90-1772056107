angular.module('globalSettingsDashboardServiceModule',[]).factory('globalSettingsDashboardService', function($http) {
    this.phmGlobalSettingDirtyFlag =  false; //Flase = Allow to move, true = Not allow to move
    this.obj = undefined;
    this.loggedInUserid= undefined;
    return {
        setPhmGlobalSettingDirtyFlag : setPhmGlobalSettingDirtyFlag,
        getPhmGlobalSettingDirtyFlag : getPhmGlobalSettingDirtyFlag,
        setCurrentGlobalSettingObject : setCurrentGlobalSettingObject,
        getCurrentGlobalSettingObject : getCurrentGlobalSettingObject,
        setloggedInUserid : setloggedInUserid,
        getloggedInUserid : getloggedInUserid,
    };

    function setPhmGlobalSettingDirtyFlag(flag) {
        this.phmGlobalSettingDirtyFlag = flag;
    }

    function getPhmGlobalSettingDirtyFlag() {
        return this.phmGlobalSettingDirtyFlag;
    }

    function setCurrentGlobalSettingObject(object) {
        this.obj = object;
    }

    function getCurrentGlobalSettingObject() {
        return this.obj;
    }
    function setloggedInUserid(loggedInUserid) {
        this.loggedInUserid = loggedInUserid;
    }

    function getloggedInUserid() {
        return this.loggedInUserid;
    }

});