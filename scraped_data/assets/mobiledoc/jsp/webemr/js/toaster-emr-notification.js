let notifications=[];let notificationsCnt=0;angular.module("toasterEmrNotification",[]).service("toasterEmrService",function($rootScope){this.showSuccessToasterWithUndo=function(windowName,subject,message,timeout,controllerName,testCalbackFn){let notifyObj={};if(angular.isUndefined(timeout)||timeout<=0){timeout=9e3}if(windowName===''||subject===''||message===''||controllerName===''||testCalbackFn===''||angular.isUndefined(windowName)||angular.isUndefined(subject)||angular.isUndefined(message)||angular.isUndefined(controllerName)||angular.isUndefined(testCalbackFn)){console.log("Add required params");return}notifyObj.duration=timeout;notifyObj.message=message;notifyObj.testCalbackFn=testCalbackFn;notifyObj.windowName=windowName;notifyObj.subject=subject;notifyObj.id=notificationsCnt;notifyObj.controllerName=controllerName;notifyObj.withUndoBtn=true;notifyObj.type='Success';$rootScope.$broadcast('toaster-addUndoToast',notifyObj)};this.showSuccessToaster=function(windowName,subject,message,timeout){if(angular.isUndefined(timeout)||timeout<=0){timeout=4e3}if(windowName===''||subject===''||message===''||angular.isUndefined(windowName)||angular.isUndefined(subject)||angular.isUndefined(message)){console.log("Add required params");return}let notifyObj={};notifyObj.duration=timeout;notifyObj.message=message;notifyObj.windowName=windowName;notifyObj.subject=subject;notifyObj.id=notificationsCnt;notifyObj.withUndoBtn=false;notifyObj.type='Success';$rootScope.$broadcast('toaster-addUndoToast',notifyObj)};this.showCommunicationToaster=function(windowName,subject,message,timeout){if(angular.isUndefined(timeout)||timeout<=0){timeout=4e3}if(windowName===''||subject===''||message===''||angular.isUndefined(windowName)||angular.isUndefined(subject)||angular.isUndefined(message)){console.log("Add required params");return}let notifyObj={};notifyObj.duration=timeout;notifyObj.message=message;notifyObj.windowName=windowName;notifyObj.subject=subject;notifyObj.id=notificationsCnt;notifyObj.type='Communication';$rootScope.$broadcast('toaster-addUndoToast',notifyObj)}}).directive("toasterEmrNotificationContainer",['$compile','$timeout','$http','$interval',function toasterEmrContainer($compile,$timeout,$http,$interval){return{restrict:'EA',scope:true,link:function(scope,elm,attrs){scope.$on('toaster-addUndoToast',function(event,notifyObj){if(!event.defaultPrevented){event.defaultPrevented=true;scope.addUndoToast(notifyObj)}});scope.addUndoToast=function(notifyObj){notificationsCnt++;scope.create(notifyObj)};scope.create=function(notifyNewObj){notifications.push(notifyNewObj);if(notifyNewObj.withUndoBtn&&notifyNewObj.type==='Success'){document.getElementById('notifications').innerHTML+=` <div class=" notification-container"  id="notification-${notifyNewObj.id}" >
                     <div class="toast-alert-box slideRight theme-success notification-content"  style="min-width: 400px; max-width: 550px" >
                    <div class="toast-wrap">
                        <div> <p class="fnt13 bold ml10 mr10 notification-text">${notifyNewObj.windowName} - ${notifyNewObj.subject}</p> </div>
                        <div>
                        <table>
                            <tr>
                                <td>
                                        <i class="icon icon-toast-confirmed mt10-main left ml5" style="top: 30px;"></i>        
                                </td>
                                <td>
                                    <p class="fnt13 ml10 mr10 notification-text"><span id="toasterMessageSpan"> ${notifyNewObj.message} </span>   </p>
                                </td>
                                <td>
                                    <button class="btn btn-aquagrey btn-xs mrr20 mar-r15 mt-20" ng-click="callBack(${notifyNewObj.id})" id="removing-in-${notifyNewObj.id}">Undo ${notifyNewObj.duration/1e3}sec</button>
                                </td>
                                <td>
                                    <i class="icon-toast-close" style="top: 42%;" ng-click="deleteNotification(${notifyNewObj.id})"></i>
                                </td>
                            </tr>
                        </table>                       
                        </div>
                    </div>
                </div>`}else if(!notifyNewObj.withUndoBtn&&notifyNewObj.type==='Success'){document.getElementById('notifications').innerHTML+=` <div class=" notification-container"  id="notification-${notifyNewObj.id}" >
                <div class="toast-alert-box slideRight theme-success notification-content"  style="min-width: 400px; max-width: 550px" >
                    <div class="toast-wrap">
                        <div> <p class="fnt13 bold ml10 mr10 notification-text">${notifyNewObj.windowName} - ${notifyNewObj.subject}</p> </div>
                        <div><i class="icon icon-toast-confirmed mt10-main left ml5"></i>
                        <p class="fnt13 ml10 mr10 notification-text"><span id="toasterMessageSpan"> ${notifyNewObj.message} </span></p>
                        <i class="icon-toast-close" ng-click="deleteNotification(${notifyNewObj.id})"></i>
                        </div>
                    </div>
                </div>`}else if(notifyNewObj.type==='Communication'){document.getElementById('notifications').innerHTML+=` <div class=" notification-container"  id="notification-${notifyNewObj.id}" >
                <div class="toast-alert-box slideRight theme-grey notification-content"  style="min-width: 400px; max-width: 550px" >
                    <div class="toast-wrap">
                        <div><i class="icon icon-info2 mt10-main ml5 infoIconPos" ></i>
                        <span class="fnt13 bold notification-text">${notifyNewObj.windowName} - </span><span id="toasterMessageSpan" class="fnt13  mr10 notification-text">${notifyNewObj.message} </span>
                        <i class="icon-toast-close" ng-click="deleteNotification(${notifyNewObj.id})"></i>
                        </div>
                    </div>
                </div>`}notifyNewObj.interval=$interval(addTime,1e3,0,true,notifyNewObj);notifyNewObj.timeout=$interval(deleteItem,notifyNewObj.duration,0,true,notifyNewObj);setTimeout(function(){$('.notification-content').addClass('active');$compile($("#notifications").contents())(scope)},10);scope.logNotification(notifyNewObj)};function addTime(thiss){if(document.getElementById(`removing-in-${thiss.id}`)!==null){thiss.duration-=1e3;document.getElementById(`removing-in-${thiss.id}`).innerHTML=`Undo ${thiss.duration/1e3}sec`}}function deleteItem(thiss){if(document.getElementById(`notification-${thiss.id}`)!==null){$interval.cancel(thiss.interval);clearTimeout(thiss.timeout);document.getElementById(`notification-${thiss.id}`).remove()}}scope.callBack=function(id){let parentscope=angular.element("[ng-controller='"+notifications[id].controllerName+"']");parentscope.methodName=notifications[id].testCalbackFn;if(typeof parentscope.methodName==="function"){parentscope.methodName();$('#notification-'+id).css("display","none")}};scope.deleteNotification=function(id){for(let notification of notifications){if(notification.id===id){$('#notification-'+id).css("display","none")}}};scope.logNotification=function(notifyNewObj){let params={"windowName":notifyNewObj.windowName,"typeOfNotification":notifyNewObj.type==='Communication'?'Communication':'Confirmation',"styleOfNotification":'Toaster Alert',"action":'Notify',"header":notifyNewObj.subject,"details":notifyNewObj.message,"isSuppressed":false};$http({method:'POST',url:makeURL('/mobiledoc/ascWeb/notification.go/saveNotification'),data:JSON.stringify(params)}).then(function errorCallback(response){console.log(response.data.errorMsg)})}},template:'<div class="notifications-container toast-wrapper toast-bottom-right emr-notification-main " id="notifications" ></div>'}}]);