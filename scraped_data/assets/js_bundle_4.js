(function(){'use strict';let mainAppDependencies=["ui.bootstrap","ecw.dir.patientidentifier",'ecw.telemed','ComponentCleanUp'];if(isChatEnabledForLoggedInUser){mainAppDependencies.push("chatArea");mainAppDependencies.push("chatDataService")}angular.module('HealowConnect',mainAppDependencies)})();
(function(){'use strict';angular.module('HealowConnect').factory('SessionService',SessionService);function SessionService(){let service=this;service.activeSession=false;service.callInfo={};service.patientInitial="";service.isConnecting=false;service.showCallUI=false;service.showSipCallUI=false;service.callStatusMsg="";service.callTimer="";service.isMicMute=false;service.callRunning=false;service.callType=1;service.setPtNotOnCall=function(){};service.setIsPtEnrolled=function(){};service.disableHConnectBtn=false;service.endCall=function(){};service.showCallPaseView=function(){};service.hideCallapseView=function(){};service.muteUnMuteParticipant=function(){};service.hideDockViewOnEndCall=function(){};service.setVideoContainerLayout=function(){};service.disableConnectBtnFn=function(){};service.callStarted=false;service.changeHConnectBtnState=function(){};service.showHConnectModule=function(){};service.startH2HCall=function(callType,isManged,managedById,managedByName,managedByRelation){};service.emptyHealowPhoneNumberToCall=function(){};service.hideImgPanel=function(){};service.isPtOnCall=false;service.healowPhonePtName="";service.healowPhonePtContactDetails={};service.healowPhoneEmergencyContactDetails={};service.resetVarOnEndCall=function(){};service.inviteeJoined=function(){};service.resetTVVarOnEndCall=function(){};service.isMultiplePtBtn=false;return{isActiveSession:isActiveSession,setActiveSession:setActiveSession,getCallInfo:getCallInfo,setCallInfo:setCallInfo,getPtInitial:getPtInitial,setPtInitials:setPtInitials,getIsConnecting:getIsConnecting,setConnecting:setConnecting,getShowCallUI:getShowCallUI,setShowCallUI:setShowCallUI,getCallStatusMsg:getCallStatusMsg,setCallStatusMsg:setCallStatusMsg,getCallTimer:getCallTimer,setCallTimer:setCallTimer,getIsMicMute:getIsMicMute,setIsMicMute:setIsMicMute,endCallFun:endCallFun,setEndCallFunction:setEndCallFunction,getCallRunning:getCallRunning,setCallRunning:setCallRunning,showCallpseViewUI:showCallpseViewUI,showCallapsedView:showCallapsedView,hideCallapseView:hideCallapseView,hideCallapseViewUI:hideCallapseViewUI,setMuteParticipantFn:setMuteParticipantFn,muteUnMuteParticipant:muteUnMuteParticipant,setEndCallCleanFun:setEndCallCleanFun,hideCallDockView:hideCallDockView,setCallType:setCallType,getCallType:getCallType,setContainerLayout:setContainerLayout,callVideoLayout:callVideoLayout,setCallStarted:setCallStarted,setCallStartFunction:setCallStartFunction,setEmptyHealowPhoneNumberToCall:setEmptyHealowPhoneNumberToCall,emptyHealowPhoneNumberToCall:emptyHealowPhoneNumberToCall,setBtnState:setBtnState,getShowSipCallUI:getShowSipCallUI,setShowSipCallUI:setShowSipCallUI,showH2hOrSipCallUI:showH2hOrSipCallUI,changeBtnState:changeBtnState,startH2HCallBack:startH2HCallBack,setStartCallFn:setStartCallFn,setIsPtEnrolled:setIsPtEnrolled,getIsPtEnrolled:getIsPtEnrolled,setDisableHConnectBtn:setDisableHConnectBtn,isHConnectBtnDisable:isHConnectBtnDisable,disableConnectBtn:disableConnectBtn,setPtEnrolled:setPtEnrolled,showHConnectModule:showHConnectModule,showHConnectActivity:showHConnectActivity,setHideImgPanel:setHideImgPanel,hideImgPanel:hideImgPanel,setPtNotOnCall:setPtNotOnCall,setPtIsNotOnCall:setPtIsNotOnCall,setIsPtOnCall:setIsPtOnCall,isPtOnCall:isPtOnCall,setHealowPhonePtName:setHealowPhonePtName,getHealowPhonePtName:getHealowPhonePtName,setHealowPhonePtContactDetails:setHealowPhonePtContactDetails,getHealowPhonePtContactDetails:getHealowPhonePtContactDetails,setHealowPhoneEmergencyContactDetails:setHealowPhoneEmergencyContactDetails,getHealowPhoneEmergencyContactDetails:getHealowPhoneEmergencyContactDetails,setResetVarOnEndCallFn:setResetVarOnEndCallFn,resetVarOnEndCallFn:resetVarOnEndCallFn,setInviteeJoinTVFn:setInviteeJoinTVFn,callInviteeJoinedTV:callInviteeJoinedTV,resetTVVarOnEndCall:resetTVVarOnEndCall,resetTVVarOnEndCallFn:resetTVVarOnEndCallFn,isMultiplePtBtn:isMultiplePtBtn,setMultiplePtBtn:setMultiplePtBtn};function isMultiplePtBtn(){return service.isMultiplePtBtn}function setMultiplePtBtn(isMultiplePtBtn){service.isMultiplePtBtn=isMultiplePtBtn}function resetTVVarOnEndCallFn(resetTvVarFn){resetTVVarOnEndCall=resetTvVarFn}function resetTVVarOnEndCall(){resetTVVarOnEndCall()}function callInviteeJoinedTV(){service.inviteeJoined()}function setInviteeJoinTVFn(inviteeJoinFn){service.inviteeJoined=inviteeJoinFn}function setResetVarOnEndCallFn(resetVarOnEndCall){service.resetVarOnEndCall=resetVarOnEndCall}function resetVarOnEndCallFn(){service.resetVarOnEndCall()}function setHealowPhoneEmergencyContactDetails(healowPhoneEmergencyContactDetails){service.healowPhoneEmergencyContactDetails=healowPhoneEmergencyContactDetails}function getHealowPhoneEmergencyContactDetails(){return service.healowPhoneEmergencyContactDetails}function setHealowPhonePtContactDetails(healowPhonePtContactDetails){service.healowPhonePtContactDetails=healowPhonePtContactDetails}function getHealowPhonePtContactDetails(){return service.healowPhonePtContactDetails}function setHealowPhonePtName(ptName){service.healowPhonePtName=ptName}function getHealowPhonePtName(){return service.healowPhonePtName}function isPtOnCall(){return service.isPtOnCall}function setIsPtOnCall(isPtOnCall){service.isPtOnCall=isPtOnCall}function setPtIsNotOnCall(setPtNotOnCall){service.setPtNotOnCall=setPtNotOnCall}function setPtNotOnCall(){setIsPtOnCall(false);service.setPtNotOnCall()}function setHideImgPanel(setHideImgPanel){service.hideImgPanel=setHideImgPanel}function hideImgPanel(){service.hideImgPanel()}function showHConnectModule(showHConnectModule){service.showHConnectModule=showHConnectModule}function showHConnectActivity(){service.showHConnectModule()}function disableConnectBtn(disableConnectBtnFn){service.disableConnectBtnFn=disableConnectBtnFn}function isHConnectBtnDisable(){return service.disableHConnectBtn}function setDisableHConnectBtn(disable,btnId,isCallRunning){service.disableConnectBtnFn(disable,btnId,isCallRunning)}function setIsPtEnrolled(isPtEnrolledFn){service.setIsPtEnrolled=isPtEnrolledFn}function setPtEnrolled(){service.setIsPtEnrolled()}function getIsPtEnrolled(){return service.isPtEnrolled}function setStartCallFn(startCallFn){service.startH2HCall=startCallFn}function startH2HCallBack(callType,isManged,managedById,managedByName,managedByRelation){service.startH2HCall(callType,isManged,managedById,managedByName,managedByRelation)}function changeBtnState(){service.changeHConnectBtnState()}function showH2hOrSipCallUI(){return service.showCallUI||service.showSipCallUI}function getShowSipCallUI(){return service.showSipCallUI}function setShowSipCallUI(showSipCallUI){service.showSipCallUI=showSipCallUI}function setBtnState(changeBtnState){service.changeHConnectBtnState=changeBtnState}function setEmptyHealowPhoneNumberToCall(emptyHealowPhoneNumberToCall){service.emptyHealowPhoneNumberToCall=emptyHealowPhoneNumberToCall}function emptyHealowPhoneNumberToCall(){service.emptyHealowPhoneNumberToCall()}function setCallStarted(callStarted){service.callStarted=callStarted}function setCallStartFunction(){service.callStarted()}function setContainerLayout(setLayout){service.setVideoContainerLayout=setLayout}function callVideoLayout(){service.setVideoContainerLayout()}function setCallType(callType){service.callType=callType}function getCallType(){return service.callType}function setEndCallCleanFun(setEndCallCleanFun){service.hideDockViewOnEndCall=setEndCallCleanFun}function hideCallDockView(){return service.hideDockViewOnEndCall()}function muteUnMuteParticipant(){service.muteUnMuteParticipant()}function setMuteParticipantFn(muteUnMuteParticipant){service.muteUnMuteParticipant=muteUnMuteParticipant}function showCallpseViewUI(){service.showCallPaseView()}function showCallapsedView(callpaseView){service.showCallPaseView=callpaseView}function hideCallapseView(hideCallpseView){service.hideCallapseView=hideCallpseView}function hideCallapseViewUI(){service.hideCallapseView()}function isActiveSession(){return service.activeSession}function setActiveSession(){service.activeSession=true}function getCallInfo(){return service.callInfo}function setCallInfo(callInfo){service.callInfo=callInfo}function getPtInitial(){return service.patientInitial}function setPtInitials(ptInitial){service.patientInitial=ptInitial}function getIsConnecting(){return service.isConnecting}function setConnecting(isConnecting){service.isConnecting=isConnecting}function getShowCallUI(){return service.showCallUI}function setShowCallUI(showCallUI){service.showCallUI=showCallUI}function getCallStatusMsg(){return service.callStatusMsg}function setCallStatusMsg(callStatusMsg){service.callStatusMsg=callStatusMsg}function getCallTimer(){return service.callTimer}function setCallTimer(callTimer){service.callTimer=callTimer}function getIsMicMute(){return service.isMicMute}function setIsMicMute(isMicMute){service.isMicMute=isMicMute}function endCallFun(){service.endCall()}function setEndCallFunction(endCallFn){service.endCall=endCallFn}function getCallRunning(){return service.callRunning}function setCallRunning(callRunning){service.callRunning=callRunning}}})();
(function(){'use strict';var hConnectModule=angular.module("HealowConnect");hConnectModule.requires.push("telemedConstant");hConnectModule.factory("healowConnectModalService",healowConnectModalService);function healowConnectModalService($ocLazyLoad,SessionService,$modal,telemedConstantService){function openModel(patientArr,screen,encounterId,contextData,uniqueBtnId,onStartCallBack,message){SessionService.setDisableHConnectBtn(true,uniqueBtnId,SessionService.getCallRunning());if(angular.element('#healowConnectModal').scope()){if(screen==='resource_schedule'&&SessionService.getCallRunning()){return}let healowCtrlScope=angular.element('#healowConnectModal').scope().healowCtrl;if(healowCtrlScope.isDockedView||healowCtrlScope.chatData.chatDockView){if(healowCtrlScope.isTVDockView){healowCtrlScope.showTVFullView()}else{healowCtrlScope.changeToFullView()}return}}let patientInfoObj={};let isMultiplePatient=false;if(Object.prototype.toString.call(patientArr)==='[object Array]'){isMultiplePatient=true;patientInfoObj=patientArr}else{patientInfoObj['ID']=patientArr;patientInfoObj['isUnDock']=false;patientInfoObj['encounterId']=encounterId}function getConstants(callContext){var contextType=0;try{if(telemedConstantService.H2H.CALL_CONTEXT.hasOwnProperty(callContext)){contextType=telemedConstantService.H2H.CALL_CONTEXT[callContext]}}catch(error){core.h2hDebug(error)}return contextType}$ocLazyLoad.load({name:'healowConnect',files:['/mobiledoc/jsp/healowphone/assets/js/AculabCloudCaller.js','/mobiledoc/jsp/healowphone/app/js/sip.service.js','/mobiledoc/jsp/webemr/chatEMR/assets/css/auto-complete-chat-emr.css','/mobiledoc/jsp/webemr/chatEMR/landing-screen/auto-complete-chat-emr.js','/mobiledoc/jsp/webemr/telemed/scripts/telemed-module.js','/mobiledoc/jsp/webemr/healowconnect/app/healow-connect/healow-connect.controller.js','/mobiledoc/jsp/resources/jslib/@panzoom/panzoom/dist/panzoom.js','/mobiledoc/jsp/js/jquery.timeago.js','/mobiledoc/jsp/webemr/healowconnect/app/shared/services/secureText.service.js','/mobiledoc/jsp/webemr/healowconnect/app/shared/services/healow-connect-messenger.service.js','/mobiledoc/jsp/healowphone/app/directives/js/healow-phone-call-directive.js','/mobiledoc/jsp/webemr/healowconnect/app/shared/directives/healow-connect-attachment-type.directive.js','/mobiledoc/jsp/webemr/healowconnect/app/shared/directives/healow-connect-messenger-templates-directive.js','/mobiledoc/jsp/webemr/healowconnect/app/shared/directives/healow-connect-voice-message-directive.js','/mobiledoc/jsp/webemr/healowconnect/app/shared/directives/healow-connect-sms-message-directive.js','/mobiledoc/jsp/webemr/healowconnect/app/shared/directives/healow-connect-common-directive.js']}).then(function(){$modal.open({backdrop:false,windowClass:'healow-connect healow-connect-full-view custom-modal w1000p',resolve:{selectedPatient:function(){return patientInfoObj},isH2HActivated:function(){return urlPost('/mobiledoc/jsp/webemr/telemed/h2h/h2hResponse.jsp',{action:'getH2HActivationStatus'})},isMultiplePatient:function(){return isMultiplePatient},callContext:function(){return getConstants(screen)},contextData:function(){return contextData},uniqueBtnId:function(){return uniqueBtnId},onStartCallBack:function(){return typeof onStartCallBack==='function'?onStartCallBack():function(){return}},fromScreen:function(){return screen},message:function(){return message}},templateUrl:"/mobiledoc/jsp/webemr/healowconnect/assets/templates/healow-connect-modal.view.html",controller:'HealowConnectCtrl',controllerAs:'healowCtrl'})})}return{openModel:openModel}}})();
class EMRWebSocket {

    constructor(){
        this.ws = null;
        this.registedModules = [];
        this.init();

    }

    open(){
        console.log("Handshaking done");
    }
    error(event){
        console.log("WebSocket Error : ",event);
    }
    close(){
        console.log("Websocket closed");
    }
    postMessage(requestType,message){
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({requestType:requestType,message:message}))
        }
    }
    message(message,that){
        try{
            let data = JSON.parse(message.data);
            that.registedModules.forEach(v => {
                if(v.requestType === data.requestType && v.requestId===data.requestId){
                    v.callback(data.data);
                    if(v.isSingleResponse){
                        that.unregister(v.requestType,v.requestId);
                    }
                }
            })
        }catch (e){

        }
    }
    init(){
        let ws_protocol = 'wss://';
        if(location.protocol === 'http:') {
            ws_protocol = 'ws://';
        }
        this.ws = new WebSocket(ws_protocol + location.host + "/mobiledoc/socket/topic/emrNotification");
        this.ws.onopen = this.open;
        this.ws.onerror= this.error;
        this.ws.close = this.close;
        var that = this;
        this.ws.onmessage=function(message){
            that.message(message,that);
        }
        this.keepConnectionAlive();
    }
    register(requestType,requestId,isSingleResponse,callback){
        this.registedModules.push({requestType:requestType,requestId:requestId,isSingleResponse:isSingleResponse,callback:callback});
    }
    unregister(requestType,requestId){
        this.registedModules = this.registedModules.filter(v => requestType===v.requestType && requestId===v.requestId);
    }
    keepConnectionAlive(){
        const that = this;
        setInterval(() => {
            that.postMessage(EMRWebSocketRequestType.GENIE,"ping")
        }, 30000);
    }
}
var EMRWebSocketRequestType = {
    PLUGIN:1,
    FAX:2,
    GENIE:3
}
var emrws = new EMRWebSocket();
function faxCallback(message){
    notification.show('error', 'Failed Fax', message, 5000);
}
emrws.register(EMRWebSocketRequestType.FAX,null,false,faxCallback);

