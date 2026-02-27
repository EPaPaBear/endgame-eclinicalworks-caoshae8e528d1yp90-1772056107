angular.module('tocModuleCommonDirective',["ui.bootstrap"]).directive('contenteditable',['$sce',function($sce){return{restrict:'A',require:'?ngModel',link:function(scope,element,attrs,ngModel){if(!ngModel)return;ngModel.$render=function(){element.html($sce.getTrustedHtml(ngModel.$viewValue||''));read()};read();element.on('blur keyup change',function(){scope.$evalAsync(read)});read();function read(){let html=element.html();if(attrs.stripBr&&html==='<br>'){html=''}ngModel.$setViewValue(html)}}}}]).directive('tocSelectBox',function($document){return{restrict:'EA',require:'ngModel',scope:{ngModel:'=',options:'=',updateVal:'&'},template:'<div class="select-box">'+'<b class="caret selection-click" data-ng-click="openDropdown($event)"></b>'+'<span class="selection-field selection-click" data-ng-click="openDropdown($event)" ng-bind-html="ngModel.name"></span>'+'<ul class="sel-optn selection-options p-0" data-ng-class="{open: open}">'+'<perfect-scrollbar class="scroller dropdown-scroll" wheel-propagation="true" swipe-propagation="true" refresh-on-change="someArray" on-scroll="onScroll(scrollTop, scrollHeight)" always-visible="true">'+'<li ng-repeat="option in options" data-ng-click="selectItem(option, $event)" ng-bind-html="option.name">'+'</li>'+'</perfect-scrollbar>'+'</ul>'+'</div>',controller:function($scope){$scope.openDropdown=function(e){$scope.open=!$scope.open;let _that=e.target;let selectBoxWidth=angular.element(_that).parents('.select-box').outerWidth();let droplist=angular.element(_that).parents('.select-box').find('.sel-optn');angular.element(droplist).width(selectBoxWidth);droplist.show().animate({},100,function(){angular.element(this).position({of:angular.element(_that).parents('.select-box'),my:'left top',at:'left bottom',collision:"flipfit"}).animate({"opacity":1},100)})}},link:function(scope,element,attrs,ctrl){function onMouseup(e){let container=angular.element('.selection-options');if(!container.is(e.target)&&container.has(e.target).length===0){container.removeClass('open');container.hide()}}$document.on('mouseup',onMouseup);scope.$on('$destroy',function(){$document.off('mouseup',onMouseup)});scope.selectItem=function(option,e){scope.ngModel=option;scope.open=false;angular.element(e.target).parents('.sel-optn').hide();ctrl.$setViewValue(option)}}}}).directive('onOutsideElementClick',function($document){return{restrict:'A',link:function(scope,element,attrs){element.on('click',function(e){e.stopPropagation()});function onClick(){scope.$apply(function(){scope.$eval(attrs.onOutsideElementClick)})}$document.on('click',onClick);scope.$on('$destroy',function(){$document.off('click',onClick)})}}}).directive('tcnDatepicker',function(){return{restrict:'AE',require:'ngModel',scope:{showon:'@',showbuttonpanel:'@',ngModel:"="},link:function(scope,element,attrs,ngModelCtrl){function changeYearButtons(input){setTimeout(function(){let buttonPane=$(input).datepicker("widget").find(".ui-datepicker-buttonpane");let btn=$('<button type="button" class="ui-datepicker-clear ui-state-default ui-priority-primary ui-corner-all" data-label="clear">Clear</button>');btn.unbind("click").bind("click",'button',function(e){let currentDate=new Date;let shortcut=e.target.dataset.label;if(shortcut==="clear"){$.datepicker._clearDate(input)}else{let dateRange=shortcut.slice(1,2);let rangeCount=shortcut.slice(0,1);let selectedDate=new Date;switch(dateRange){case"D":selectedDate.setDate(currentDate.getDate()+Number(rangeCount));break;case"W":selectedDate.setDate(currentDate.getDate()+7*rangeCount);break;case"M":selectedDate.setMonth(currentDate.getMonth()+Number(rangeCount));break;case"Y":selectedDate.setFullYear(currentDate.getFullYear()+Number(rangeCount));break;default:selectedDate=new Date;break}let inputVal=moment(selectedDate).format("MM/DD/YYYY");$(input).val(inputVal)}$(input).datepicker("hide")});btn.appendTo(buttonPane)},0)}element.datepicker({showOn:scope.showon,buttonImage:"/mobiledoc/jsp/TCM/modules/TCN/assets/img/calender-icon.png",buttonImageOnly:true,buttonText:"Select date",maxDate:new Date,changeMonth:true,changeYear:true,dateFormat:'mm/dd/yy',closeText:"Clear",showButtonPanel:scope.showbuttonpanel,onSelect:function(date,input){if($(input).datepicker("widget").find(".ui-datepicker-buttonpane").children('button').length===2){changeYearButtons(input)}scope.ngModel=date;ngModelCtrl.$setViewValue(date)},beforeShow:function(input){changeYearButtons(input)},onChangeMonthYear:function(year,month,input){changeYearButtons(input.input)}});scope.$watch('ngModel',function(newVal,oldValue){if(new Date(newVal)!='Invalid Date'&&newVal>=1900){element.datepicker('setDate',new Date(newVal))}})}}}).directive('slider',function(){return{link:function(scope,element,attrs){console.log(scope);scope.prevVal=()=>{alert()}}}}).directive('multiSelect',function(){return{restrict:'A',link:function(scope,element,attrs){element.on('click',function(e){e.stopPropagation()});function onClick(){scope.$apply(function(){scope.$eval(attrs.onOutsideElementClick)})}$document.on('click',onClick);scope.$on('$destroy',function(){$document.off('click',onClick)})}}}).directive('sortable',function(){return{restrict:'A',require:'?ngModel',link:function(scope,element,attrs,ngModel){if(ngModel){ngModel.$render=function(){element.sortable('refresh')}}element.sortable({connectWith:attrs.sortableSelector,handle:attrs.sortableHandle,cancel:'a',revert:true,remove:function(e,ui){if(ngModel.$modelValue.length===1){ui.item.sortable.moved=ngModel.$modelValue.splice(0,1)[0]}else{ui.item.sortable.moved=ngModel.$modelValue.splice(ui.item.sortable.index,1)[0]}},receive:function(e,ui){ui.item.sortable.relocate=true;ngModel.$modelValue.splice(ui.item.index(),0,ui.item.sortable.moved)},update:function(e,ui){ui.item.sortable.resort=ngModel},start:function(e,ui){ui.item.sortable={index:ui.item.index(),resort:ngModel}},stop:function(e,ui){if(ui.item.sortable.resort&&!ui.item.sortable.relocate){let start=ui.item.sortable.index;let end=ui.item.index();ui.item.sortable.resort.$modelValue.splice(end,0,ui.item.sortable.resort.$modelValue.splice(start,1)[0])}if(ui.item.sortable.resort||ui.item.sortable.relocate){scope.$apply()}}})}}}).directive("tcmMultiSelect",function($document){return{restrict:"E",scope:{options:"=",placeholder:"@",badge:"=",noOfBadges:"=",isDisabled:'=?',onChange:"&",confirmAlertPosition:"=",showConfirm:"=?"},template:`
      <div class="custom-multiselect-input">
    <div class="multi-select-input-group" data-ng-class="{active: isDropDownOpen, disabled:isDisabled}">
        <div class="badge-wrapper" ng-if="selectedList.length>0">
            <div class="badges" ng-repeat="item in selectedList | limitTo: noOfBadges?noOfBadges:2"> 
                <span class="badges-text" tooltip-enable="{{item.name.length>10?true:false}}"  tooltip-placement="top"
                uib-tooltip="{{item.name}}"  tooltip-append-to-body="true"
                tooltip-class="custom-white-bg arrow-right-bottom" ng-bind="item.name"></span>
                <i class="icon pcc-icon-close-bold" ng-click="discardBadge(item, index)"></i>
            </div>
        </div>
        <input type="text" ng-keyup="applySearch()" ng-model="searchText" > 
        <div class="selected-list"  ng-if="selectedList.length>1" ng-click="showSelectedPopover()">
            <span class="count">+{{selectedList.length-1}}</span>
        </div>
        <div class="multi-select-input-group-addon" ng-click="isDropDownOpen = !isDropDownOpen">
            <span class="icon icon-arrow"></span>      
        </div>
        <div class="multi-select-input-group-addon" ng-click="discardSelected()" ng-if="selectedList.length>0">
            <span class="icon icon-close"></span>  
        </div>
    </div>
    <perfect-scrollbar class="multiselect-dropdown-list" wheel-propagation="true" ng-if="isDropDownOpen"
        swipe-propagation="true" refresh-on-change="someArray" on-scroll="onScroll(scrollTop, scrollHeight)" always-visible="true" ng-style="{'max-height': scrollerHeight}">
        <ul class="nopadding nomargin mb-0">
            <li ng-repeat="item in options | filter : searchText track by $index" ng-click="selectListValue(item)">
                <div class="form-check-inline">
                    <input type="checkbox" ng-change="selectListValue(item)" ng-disabled="isDisabled" ng-model="item.selected">
                </div> <div class="text-ellipse" ellipses-tooltip placement="'bottom'" class-name="'multiselect-tooltip'" content="item.name" >
                <span ng-bind="item.name"></span>
                </div> 
            </li>
        </ul>
        </perfect-scrollbar>
    <div class="selected-list-wrapper" ng-if="showSelectedList && selectedList.length>1">
      <perfect-scrollbar class="scroller">
      <ul class="nopadding nomargin">
          <li class="flex justify-content-between" ng-repeat="item in selectedList" ng-if="!$first">
              <span ng-bind="item.name" class="text-ellipse mr5"></span>
              <span class="icon-close pcc-icon-cleartext" ng-click="discardBadge(item, index);showSelectedList=false"></span>  
          </li>
      </ul>
      </perfect-scrollbar>
    </div>

    <div class="confirmation-propmt"  ng-class="{'right': confirmAlertPosition}" ng-show="showConfirmationDelete">
      <div class="popup-arrow yellow-toast">
        <div class="left-section">
            <i class="icon pcc-icon-warning color-black"></i>
        </div>
        <div class="rightsection d-flex">
            <div class="fnt12bold">Are you sure you want to clear these selections? </div>
            <div class="d-flex ml10 gap-5">
                <button type="button" class="btn btn-xs" name="button" ng-click="showConfirmationDelete=false">No</button>
                <button type="button" class="btn btn-xs" name="button" ng-click="resetOptions();isDropDownOpen=false;searchText='';showConfirmationDelete=false">Yes</button>
            </div>
        </div>
      </div>
    </div>                                                            
    
</div>

      `,controller:function($scope){$scope.isDropDownOpen=false;$scope.selectedList=[];$scope.showSelectedList=false;$scope.searchText="";$scope.showConfirmationDelete=false;$scope.isDisabled=angular.isDefined($scope.isDisabled)?$scope.isDisabled:false;$scope.showConfirm=angular.isDefined($scope.showConfirm)?$scope.showConfirm:false;$scope.$watch('options',function(newValue,oldValue){if(newValue){$scope.selectedList=$scope.options.filter(el=>el.selected)}},true);$scope.selectListValue=item=>{if(item.name==='All'){$scope.options.forEach(function(el){el.selected=false})}else{$scope.checkAllOption(false)}item.selected=!item.selected;$scope.selectedList=$scope.options.filter(el=>el.selected);$scope.onChange({data:$scope.selectedList});$scope.searchText=""};$scope.discardSelected=()=>{if($scope.showConfirm){$scope.showConfirmationDelete=true}else{$scope.resetOptions();$scope.isDropDownOpen=false;$scope.searchText="";if($scope.selectedList.length===0){$scope.onChange({data:[{id:0,name:"All",selected:true}]})}}};$scope.discardBadge=(item,index)=>{$scope.options[$scope.options.indexOf(item)].selected=false;item.selected=false;$scope.selectedList.splice(index,1);$scope.showConfirmationDelete=false;if($scope.selectedList.length===0){$scope.onChange({data:""})}};$scope.applySearch=()=>{$scope.isDropDownOpen=true};$scope.showSelectedPopover=()=>{$scope.showSelectedList=!$scope.showSelectedList};$scope.checkAllOption=value=>{let allEle=$scope.options.find(el=>el.name==='All');if(allEle){allEle.selected=value}};$scope.resetOptions=()=>{$scope.selectedList=[];$scope.options.forEach(el=>el.selected=false);$scope.checkAllOption(true);$scope.onChange({data:[{id:0,name:"All",selected:true}]})}},link:function(scope,element,attrs){var onMouseup=function(e){var container=angular.element(element);if(!container.is(e.target)&&container.has(e.target).length===0){scope.isDropDownOpen=false;scope.showSelectedList=false}};$document.on("mouseup",onMouseup);scope.$on("$destroy",function(){$document.off("mouseup",onMouseup)})}}}).directive("tcmCountyMultiSelect",function($document){return{restrict:"E",scope:{placeholder:"@",multiselect:"=?",badge:"=",noOfBadges:"=",isDisabled:'=?',model:'=',onChange:"&",confirmAlertPosition:"=",showConfirm:"=?",filterName:"@",showalloption:"=?"},template:`
      <div class="custom-multiselect-input infiniteCountyScrollDiv">
    <div class="multi-select-input-group" data-ng-class="{active: isDropDownOpen, disabled:isDisabled}">
        <div class="badge-wrapper" ng-if="selectedList.length>0 || showalloption" style="display: block">
            <div class="badges" ng-if="selectedList.length <= 0 && alloptions.selected"> 
                <span class="badges-text" tooltip-class="custom-white-bg arrow-right-bottom" ng-bind="alloptions.name"></span>
                <i class="icon icon-close" ng-click="alloptions.selected=false"></i>
            </div>
            <div class="badges" ng-repeat="item in selectedList | limitTo: noOfBadges?noOfBadges:2" ng-if="item.name && item.id > 0"> 
                <span class="badges-text" tooltip-enable="{{item.name.length>10?true:false}}"  tooltip-placement="top"
                uib-tooltip="{{item.name}}"  tooltip-append-to-body="true"
                tooltip-class="custom-white-bg arrow-right-bottom" ng-bind="item.name"></span>
                <i class="icon icon-close" ng-click="discardBadge(item, index)"></i>
            </div>
        </div>
        <input ng-readonly="selectedList.length > 0" type="text" placeholder="{{(selectedList.length <= 0) ? placeholder : ''}}" ng-keyup="searchCounty($event)" ng-model="searchText" > 
        <div class="selected-list"  ng-if="selectedList.length>1 && multiselect" ng-click="showSelectedPopover()">
            <span class="count">+{{selectedList.length-1}}</span>
        </div>
        <div class="multi-select-input-group-addon" ng-click="getAllFacilities()">
            <span class="icon icon-arrow"></span>      
        </div>
        <div class="multi-select-input-group-addon" ng-click="discardSelected()" ng-if="selectedList.length>0 && multiselect">
            <span class="icon icon-close"></span>  
        </div>
    </div>
    <perfect-scrollbar class="multiselect-dropdown-list" id= "CountyScrollbar" wheel-propagation="true" ng-if="isDropDownOpen"
        swipe-propagation="true" refresh-on-change="someArray" on-scroll="scrollHandler(scrollTop, scrollHeight)" always-visible="true" ng-style="{'max-height': scrollerHeight}">
        <ul class="nopadding nomargin mb-0">
            <li ng-if="showalloption"  ng-click="selectListValue(alloptions)">
                <span ng-bind="alloptions.name"></span>
            </li>
            <li ng-repeat="item in options" ng-click="selectListValue(item)">
                <div class="text-ellipse" ellipses-tooltip placement="'bottom'" class-name="'multiselect-tooltip'" content="item.name" >
                  <span ng-bind="item.name"></span>
                </div> 
            </li>
            <li class="tcnEndOfListLi" ng-if="!noRecordFound && isEndOfList">Please continue your search by typing</li>
            <li ng-if="noRecordFound">
                <span>No record found</span>
            </li>
        </ul>
        </perfect-scrollbar>
    <div class="selected-list-wrapper" ng-if="showSelectedList && selectedList.length>1">
      <perfect-scrollbar class="scroller">
      <ul class="nopadding nomargin">
          <li class="flex justify-content-between" ng-repeat="item in selectedList" ng-if="!$first">
              <span ng-bind="item.name" title="{{item.name}}" class="text-ellipse mr5"></span>
              <span class="icon-close icon-close" ng-click="discardBadge(item, index);showSelectedList=false"></span>  
          </li>
      </ul>
      </perfect-scrollbar>
    </div>

    <div class="confirmation-propmt"  ng-class="{'right': confirmAlertPosition}" ng-show="showConfirmationDelete">
      <div class="popup-arrow yellow-toast">
        <div class="left-section">
            <i class="icon pcc-icon-warning color-black"></i>
        </div>
        <div class="rightsection d-flex">
            <div class="fnt12bold">Are you sure you want to clear these selections? </div>
            <div class="d-flex ml10 gap-5">
                <button type="button" class="btn btn-xs" name="button" ng-click="showConfirmationDelete=false">No</button>
                <button type="button" class="btn btn-xs" name="button" ng-click="resetOptions();">Yes</button>
            </div>
        </div>
      </div>
    </div>                                                            
</div>`,controller:function($scope,$timeout,commonServiceFactory){$scope.isDropDownOpen=false;$scope.selectedList=[];$scope.showSelectedList=false;$scope.searchText="";$scope.showConfirmationDelete=false;$scope.isDisabled=angular.isDefined($scope.isDisabled)?$scope.isDisabled:false;$scope.showConfirm=angular.isDefined($scope.showConfirm)?$scope.showConfirm:false;$scope.multiselect=angular.isDefined($scope.multiselect)?$scope.multiselect:true;$scope.showalloption=angular.isDefined($scope.showalloption)?$scope.showalloption:false;$scope.filterName=angular.isDefined($scope.filterName)?$scope.filterName:'facility';$scope.isEndOfList=false;$scope.dropdownType=$scope.multiselect?'multiselect':'singleselect';$scope.pageNumber=0;$scope.rowPerPage=20;$scope.maxSize=100;$scope.options=[];$scope.isNoMoreRecords=false;$scope.alloptions={name:'All',id:0,selected:true};$scope.isFirstCall=true;$scope.minCharLookupVal=3;let timer="";$scope.$watch('model',function(newValue,oldValue){if(newValue){$scope.selectedList=newValue;if($scope.selectedList.length===0){$scope.alloptions.selected=true}}},true);setTimeout(function(){$('.custom-multiselect-input').find('.infiniteCountyScrollDiv').on('scroll',$scope.scrollHandler())},500);$scope.scrollHandler=(scrollTop,scrollHeight)=>{if(scrollTop+scrollHeight>480){let position=Object.keys($scope.options).length;if(position>=$scope.maxSize){$timeout(function(){$scope.isEndOfList=true})}else{if($scope.isNoMoreRecords||$scope.isEndOfList){return}$timeout(function(){$scope.pageNumber+=1;$scope.loadCountyList()},250)}}};$scope.selectListValue=item=>{if(item.name==='All'){$scope.selectedList=[];$scope.alloptions.selected=true}else{$scope.alloptions.selected=false;$scope.searchText='';if($scope.multiselect){if($scope.selectedList.findIndex(el=>el.id===item.id)===-1){$scope.selectedList.push(item);item.selected=!item.selected}}else{$scope.isDropDownOpen=false;$scope.selectedList[0]=item}}$scope.callOnChange()};$scope.callOnChange=function(){$scope.onChange({data:{filterName:$scope.filterName,modelVal:$scope.selectedList,type:$scope.dropdownType}})};$scope.discardSelected=()=>{if($scope.showConfirm){$scope.showConfirmationDelete=true}else{$scope.selectedList.forEach(el=>el.selected=false);$scope.resetOptions()}};$scope.discardBadge=item=>{let index=$scope.selectedList.findIndex(el=>el.id===item.id);$scope.selectedList.splice(index,1);item.selected=!item.selected;$scope.showConfirmationDelete=false;$scope.callOnChange()};$scope.showSelectedPopover=()=>{$scope.showSelectedList=!$scope.showSelectedList};$scope.getAllFacilities=function(){$scope.pageNumber=1;$scope.options=[];$scope.searchText='';$scope.loadCountyList()};$scope.searchCounty=function(e){if(e&&e.type=="keyup"){switch(e.keyCode){case 9:e.stopPropagation();break}}if($scope.searchText&&$scope.searchText.length>=$scope.minCharLookupVal){if(timer&&timer!=''){$timeout.cancel(timer)}timer=$timeout(function(){$scope.pageNumber=1;$scope.options=[];$scope.loadCountyList()},500)}};$scope.loadCountyList=async()=>{$scope.isDropDownOpen=true;$scope.noRecordFound=false;let param={pageNumber:$scope.pageNumber,rowPerPage:$scope.rowPerPage,searchText:$scope.searchText};let promiseObj=commonServiceFactory.getPromiseService({url:"/mobiledoc/emr/ecw.tcm/getUniqueUserCountyList",data:param});const[error,response]=await commonServiceFactory.getCallbackData(promiseObj);if(response){if(response.data.responseData.length>0){$scope.setResponseData(response.data.responseData)}else{$timeout(function(){if($scope.searchText)$scope.noRecordFound=true},100)}}else if(error){notification.show("error","TCN County Filters","Something went wrong",4e3)}$scope.isFirstCall=false};$scope.setResponseData=function(resList){if(resList.length<$scope.rowPerPage){$scope.isNoMoreRecords=true}resList=resList.filter(el=>el.county!=='');$timeout(function(){if($scope.options.length>0){$scope.options.push(...resList)}else{$scope.options=resList}},100)};$scope.resetOptions=()=>{$scope.selectedList=[];$scope.isDropDownOpen=false;$scope.searchText="";$scope.callOnChange()}},link:function(scope,element,attrs){var onMouseup=function(e){var container=angular.element(element);if(!container.is(e.target)&&container.has(e.target).length===0){scope.isDropDownOpen=false;scope.showSelectedList=false}};$document.on("mouseup",onMouseup);scope.$on("$destroy",function(){$document.off("mouseup",onMouseup)})}}}).directive("tocMultiSelectControl",function($document){return{restrict:"E",scope:{model:"=",key:"@",limit:"=",options:"=",updateVal:"=",placeholder:"@",badge:"=",ddarrow:"@",badgeContainer:"@",badgeContainerWidth:"@",onChange:'&',templateType:"@"},template:`
      <div class="main-multiSelect-wrapper">

          <div class="input-group input-group-sm nopadding multiSelect-input-group white-bg">

              <div class="badge-container" ng-if="badge===true && showPlaceholder===true && !tempObj.selectAllList">

                  <span class="badges"
                      ng-repeat="data in options | filter: {selected:true}  track by $index" ng-if="$index <= taglimit">
                      <span class="pull-left badges-text" data-toggle="tootltip">{{data.name}}</span>
                      <span class="pull-right">
                          <i class="icon icon-cancel del-badge" data-ng-click="cancelBadge(data)"> </i>
                      </span>
                      <div class="tooltip-box custom-tooltip">
                          <div class="tooltiparrow whitebg pad8">
                              <p class="fnt12">{{data.name}}</p>
                          </div>
                      </div>
                  </span>
              </div>

              <i class="icon icon-greysearch ml5 mr5" ng-show="result.length === 0"></i>
              <input type="text" placeholder="{{result.length===0?'Search':''}}"  class="multiselectInput form-control clearable nobrdr input-multiselect multiselctID" ng-model="filterSearch"
                  data-ng-keyup="triggerDropdown($event)" tooltip-class="whitetooltip" tooltip-enable="inputTooltip" uib-tooltip="{{showTooltipData(options)}}" tooltip-trigger="mouseenter"' +
                  'tooltip-placement="bottom-right" tooltip-append-to-body="true">

              <div class="input-group-btn d-flex w-auto ml-auto">
                  <div class="selectedlist" ng-show="$first && result.length > limit"
                      ng-repeat="data in options | filter: {selected:true} as result track by $index">
                      <span class="number" style="display:block" data-ng-click="viewFilters(data, $event)">
                          <div>+{{result.length - limit}}</div>
                      </span>
                  </div>
                  <button data-ng-click="clearValues($event)" ng-repeat="data in options | filter: {selected:true}  as result track by $index" ng-if="$first &&  result.length > 1" type="button" class="btn btn-default"><i
                          class="icon icon-cancel clear-selected"></i></button>

                  <button type="button" class="btn btn-default btnDD align-center" ng-if="ddarrow===\'caret\'"
                      data-ng-click="openDropdown($event)"><i class="icon-arrow"></i></button>
              </div>
          </div>
          
          <ul class="list-multiSelect-search" data-ng-class="{open: open}">
              <li>
              <perfect-scrollbar style="max-height:150px; position:relative" class="scroller dropdown-scroll" wheel-propagation="true" swipe-propagation="true" refresh-on-change="someArray" on-scroll="onScroll(scrollTop, scrollHeight)" always-visible="true">
                  <table class="table" ng-if="template ==='code'">
                      <thead>
                        <th></th>
                        <th>Code</th>
                        <th>Description</th>
                      </thead>
                      <tbody>
                          <tr ng-repeat="option in options | filter: filterSearch">
                              <td class="text-center"><input type="checkbox" class="custcheckbox"
                                      name="listCheckBox{{$index}}" data-ng-change="selectItem(option, $event, false)"
                                      ng-model="option.selected"></td>
                              <td>
                                  <span ng-click="selectItem(option, $event, true)">{{option.name}}</span>
                              </td>
                              <td>
                                  <span ng-click="selectItem(option, $event, true)">{{option.desc}}</span>
                              </td>
                          </tr>
                      </tbody>
                  </table>
                  <table class="table" ng-if="template ==='normal'">
                      <tbody>
                          <tr ng-repeat="option in options | filter: filterSearch" ng-click="selectItem(option, $event, true)">
                              <td class="text-left"><input type="checkbox" class="custcheckbox"
                                      name="listCheckBox{{$index}}" data-ng-change="selectItem(option, $event, false)"
                                      ng-model="option.selected"> <span class="dd-normal-lablel">{{option.name}}</span>
                              </td>
                              <td>
                                  <span ng-bind="option[key]"></span>
                              </td>
                              
                          </tr>
                      </tbody>
                  </table>
                  <table class="table nomargin" ng-if="template ==='list'">
                      <tbody>
                          <tr ng-repeat="option in options | filter: filterSearch">
                              <td class="text-left">
                                      <input type="checkbox" class="custcheckbox" 
                                      name="listCheckBox{{$index}}" data-ng-change="selectItem(option, $event, false)"
                                      ng-model="option.selected" > 
                                      <span class="dd-normal-lablel" ng-click="selectItem(option,$event,true)">{{option.name}}</span>
                              </td>                              
                          </tr>
                      </tbody>
                  </table>
                  </perfect-scrollbar>
              </li>

          </ul>

          <div class="list-popover toparrow multiSelect-option-list" style="display: none;" ng-show="result.length > limit">
              <div class="listpopover-arrow">
                  <ul class="lists">
                      <li ng-repeat="data in options | filter: {selected:true}  as result track by $index" ng-if="(($index+1) > limit)">
                      <span class="pull-left badges-text" data-toggle="tootltip" title="{{data.name}}">{{data.name}}</span>
                          <span class="pull-right" data-ng-click="cancelBadge(data)"><i class="icon icon-cancel del-badge"></i></span>
                      </li>
                  </ul>
              </div>
          </div>
          <div class="confirmation-propmt multi-confirm-prompt" style="display:none;">
              <div class="popup-arrow yellow-toast">
                  <div class="left-section">
                      <i class="icon icons-warning iconblack"></i>
                  </div>
                  <div class="rightsection dflex">
                      <p class="fnt12bold mt3">Are you sure you want to
                          clear? </p>
                      <div class="pull-right ml15">
                          <button type="button" class="btn btn-xs undobtn pull-right nomarright denyDelete"
                              name="button" data-ng-click="hidePopover($event)">No</button>
                          <button type="button" class="btn btn-xs undobtn mr10 pull-right confirmDelete"
                              name="button" data-ng-click="clearAllData($event)">Yes</button>
                      </div>
                  </div>
              </div>
          </div>

      </div>
      `,controller:function($scope){$scope.tempObj={selectAllList:false};$scope.result=[];$scope.favFilter=undefined;$scope.showPlaceholder=$scope.placeholder!=undefined?false:true;$scope.taglimit=$scope.limit!=undefined?parseInt($scope.limit)-1:0;$scope.template=$scope.templateType===undefined?'normal':$scope.templateType;$scope.keyname=$scope.key===undefined?'name':$scope.key;$scope.$watchCollection("result",function(newValue,oldValue){if(newValue!=oldValue){$scope.onChange({data:newValue});$scope.result.forEach(resultELe=>{let optionEle=$scope.options.find(el=>el.id===resultELe.id);optionEle.selected=true});$scope.showPlaceholder=$scope.options.some(item=>item.selected===true)}});$scope.triggerDropdown=function(e){$scope.open=!$scope.open;let _that=e.target;let selectBoxWidth=$(_that).parents(".main-multiSelect-wrapper").outerWidth()-3;let droplist=$(_that).parents(".main-multiSelect-wrapper").find(".list-multiSelect-search");if(e.target.value.length===0){droplist.hide();return}angular.element(droplist).width(selectBoxWidth);droplist.show().animate({},100,function(){angular.element(this).position({of:angular.element(_that).parents(".main-multiSelect-wrapper"),my:"left top",at:"left bottom",collision:"flipfit"}).animate({opacity:1},100)})};$scope.clearValues=function(e){let _that=e.target;let popover=$(_that).parents(".main-multiSelect-wrapper").find(".multi-confirm-prompt");popover.show().animate({},100,function(){angular.element(this).position({of:_that,my:"right+25 top+28",at:"right top",collision:"flipfit"}).animate({opacity:1},100)})};$scope.hidePopover=function(e){let _that=e.target;let popover=$(_that).parents(".main-multiSelect-wrapper").find(".multi-confirm-prompt");popover.hide()};$scope.clearAllData=function(e){$scope.options.filter(function(item){if(item.selected===true){item.selected=false}});let _that=e.target;let popover=$(_that).parents(".main-multiSelect-wrapper").find(".multi-confirm-prompt");popover.hide()};$scope.viewFilters=function(data,e){let _that=e.target;let popover=$(_that).parents(".main-multiSelect-wrapper").find(".multiSelect-option-list");popover.show().animate({},100,function(){angular.element(this).position({of:_that,my:"right top+28",at:"right top",collision:"flipfit"}).animate({opacity:1},100)})};$scope.openDropdown=function(e){$scope.open=!$scope.open;let _that=e.target;let selectBoxWidth=$(_that).parents(".main-multiSelect-wrapper").outerWidth()-3;let droplist=$(_that).parents(".main-multiSelect-wrapper").find(".list-multiSelect-search");angular.element(droplist).width(selectBoxWidth);droplist.show().animate({},100,function(){angular.element(this).position({of:angular.element(_that).parents(".main-multiSelect-wrapper"),my:"left top",at:"left bottom",collision:"flipfit"}).animate({opacity:1},100)})};$scope.cancelBadge=data=>{data.selected=false;$scope.showPlaceholder=$scope.options.some(item=>item.selected===true)};$scope.selectItem=function(option,e,flag){if(flag){$(e.target).parents('.main-multiSelect-wrapper').find('.multiselctID')[0].value='';option.selected=!option.selected}$scope.showPlaceholder=$scope.options.some(item=>item.selected===true)}},link:function(scope,element,attrs){function onMouseup(e){let container=angular.element(".list-multiSelect-search");if(!container.is(e.target)&&container.has(e.target).length===0){container.removeClass("open");container.hide()}let container1=angular.element(".multiSelect-option-list");if(!container1.is(e.target)&&container1.has(e.target).length===0){container1.removeClass("open");container1.hide()}let container2=angular.element(".multi-confirm-prompt");if(!container2.is(e.target)&&container2.has(e.target).length===0){container2.removeClass("open");container2.hide()}}$document.on("mouseup",onMouseup);scope.$on("$destroy",function(){$document.off("mouseup",onMouseup)})}}}).directive("tcmSecondaryCode",function($document){return{restrict:"E",scope:{model:"=",key:"@",limit:"=",patientid:"=",options:"=",updateVal:"=",placeholder:"@",badge:"=",ddarrow:"@",badgeContainer:"@",badgeContainerWidth:"@",onChange:'&',templateType:"@"},template:`
      <div class="main-multiSelect-wrapper">

          <div class="input-group input-group-sm nopadding multiSelect-input-group white-bg">

              <div class="badge-container" ng-if="badge===true && showPlaceholder===true && !tempObj.selectAllList">

                  <span class="badges"
                      ng-repeat="data in options | filter: {selected:true}  track by $index" ng-if="$index <= taglimit">
                      <span class="pull-left badges-text" data-toggle="tootltip">{{data.name}}</span>
                      <span class="pull-right">
                          <i class="icon icon-cancel del-badge" data-ng-click="cancelBadge(data)"> </i>
                      </span>
                      <div class="tooltip-box custom-tooltip">
                          <div class="tooltiparrow whitebg pad8">
                              <p class="fnt12">{{data.name}}</p>
                          </div>
                      </div>
                  </span>
              </div>

              <i class="icon icon-greysearch ml5 mr5" ng-show="result.length === 0"></i>
              <input type="text" placeholder="{{result.length===0?'Search':''}}"  class="multiselectInput form-control clearable nobrdr input-multiselect multiselctID" ng-model="filterSearch"
                  data-ng-keyup="triggerDropdown($event)" tooltip-class="whitetooltip" tooltip-enable="inputTooltip" uib-tooltip="{{showTooltipData(options)}}" tooltip-trigger="mouseenter"' +
                  'tooltip-placement="bottom-right" tooltip-append-to-body="true">

              <div class="input-group-btn d-flex w-auto ml-auto">
                  <div class="selectedlist" ng-show="$first && result.length > 1"
                      ng-repeat="data in options | filter: {selected:true} as result track by $index">
                      <span class="number" style="display:block" data-ng-click="viewFilters(data, $event)">
                          <div>+{{result.length - 1}}</div>
                      </span>
                  </div>
                  <button data-ng-click="clearValues($event)" ng-repeat="data in options | filter: {selected:true}  as result track by $index" ng-if="$first &&  result.length > 1" type="button" class="btn btn-default"><i
                          class="icon icon-cancel clear-selected"></i></button>

                  <button type="button" class="btn btn-default btnDD align-center" ng-if="ddarrow===\'caret\'"
                      ng-click="openICDfor10e($event)"><i class="icon icons-browse"></i></button>
              </div>
          </div>
          
          <div class="list-popover toparrow multiSelect-option-list" style="display: none;" ng-show="result.length > 1">
              <div class="listpopover-arrow">
                  <ul class="lists">
                      <li ng-repeat="data in options | filter: {selected:true}  as result track by $index">
                      <span class="pull-left badges-text" data-toggle="tootltip" title="{{data.name}}">{{data.name}}</span>
                          <span class="pull-right" data-ng-click="cancelBadge(data)"><i class="icon icon-cancel del-badge"></i></span>
                      </li>
                  </ul>
              </div>
          </div>
          <div class="confirmation-propmt multi-confirm-prompt" style="display:none;">
              <div class="popup-arrow yellow-toast">
                  <div class="left-section">
                      <i class="icon icons-warning iconblack"></i>
                  </div>
                  <div class="rightsection dflex">
                      <p class="fnt12bold mt3">Are you sure you want to
                          clear? </p>
                      <div class="pull-right ml15">
                          <button type="button" class="btn btn-xs undobtn pull-right nomarright denyDelete"
                              name="button" data-ng-click="hidePopover($event)">No</button>
                          <button type="button" class="btn btn-xs undobtn mr10 pull-right confirmDelete"
                              name="button" data-ng-click="clearAllData($event)">Yes</button>
                      </div>
                  </div>
              </div>
          </div>

      </div>
      `,controller:function($scope,$ocLazyLoad,$modal){$scope.tempObj={selectAllList:false};$scope.result=[];$scope.favFilter=undefined;$scope.showPlaceholder=$scope.placeholder!=undefined?false:true;$scope.taglimit=$scope.limit!=undefined?parseInt($scope.limit)-1:0;$scope.template=$scope.templateType===undefined?'normal':$scope.templateType;$scope.keyname=$scope.key===undefined?'name':$scope.key;$scope.$watchCollection("result",function(newValue,oldValue){if(newValue!=oldValue){$scope.onChange({data:newValue})}});$scope.triggerDropdown=function(e){$scope.open=!$scope.open;let _that=e.target;let selectBoxWidth=$(_that).parents(".main-multiSelect-wrapper").outerWidth()-3;let droplist=$(_that).parents(".main-multiSelect-wrapper").find(".list-multiSelect-search");if(e.target.value.length===0){droplist.hide();return}angular.element(droplist).width(selectBoxWidth);droplist.show().animate({},100,function(){angular.element(this).position({of:angular.element(_that).parents(".main-multiSelect-wrapper"),my:"left top",at:"left bottom",collision:"flipfit"}).animate({opacity:1},100)})};$scope.openICDfor10e=function(){let assessmentList=[];$ocLazyLoad.load({name:'AddICDModule',files:['/mobiledoc/jsp/webemr/progressnotes/ecwrx/RxHelper/ICD_Treatment.js','/mobiledoc/jsp/webemr/layout/css/bootbox.css','/mobiledoc/jsp/resources/jslib/bootbox/dist/bootbox.min.js']}).then(function(){let modalInstance=$modal.open({templateUrl:makeURL('/mobiledoc/jsp/webemr/progressnotes/ecwrx/RxHelper/ICD_Treatment.jsp?isGen=true&callFrom='+(isVb()?'exe':'webemr')),controller:'AddICDCtrl',windowClass:'app-modal-window bluetheme modal-width large-Modal',backdrop:"static",keyboard:false,resolve:{patientID:function(){return $scope.patientId},encounterID:function(){return 0},loginuserid:function(){return $('#TrUserId').val()},parentForm:function(){return"frmTCM"},asmtList:function(){return assessmentList}}});modalInstance.result.then(function(modalInstanceResponse){},function(modalInstanceResponse){if(modalInstanceResponse){$.each(modalInstanceResponse,function(key,value){$scope.result.push({'id':value.id,'dxCode':value.medicalcode,'dxName':value.name})})}})})};$scope.clearValues=function(e){let _that=e.target;let popover=$(_that).parents(".main-multiSelect-wrapper").find(".multi-confirm-prompt");popover.show().animate({},100,function(){angular.element(this).position({of:_that,my:"right+25 top+28",at:"right top",collision:"flipfit"}).animate({opacity:1},100)})};$scope.hidePopover=function(e){let _that=e.target;let popover=$(_that).parents(".main-multiSelect-wrapper").find(".multi-confirm-prompt");popover.hide()};$scope.clearAllData=function(e){$scope.options.filter(function(item){if(item.selected===true){item.selected=false}});let _that=e.target;let popover=$(_that).parents(".main-multiSelect-wrapper").find(".multi-confirm-prompt");popover.hide()};$scope.viewFilters=function(data,e){let _that=e.target;let popover=$(_that).parents(".main-multiSelect-wrapper").find(".multiSelect-option-list");popover.show().animate({},100,function(){angular.element(this).position({of:_that,my:"right top+28",at:"right top",collision:"flipfit"}).animate({opacity:1},100)})};$scope.openDropdown=function(e){$scope.open=!$scope.open;let _that=e.target;let selectBoxWidth=$(_that).parents(".main-multiSelect-wrapper").outerWidth()-3;let droplist=$(_that).parents(".main-multiSelect-wrapper").find(".list-multiSelect-search");angular.element(droplist).width(selectBoxWidth);droplist.show().animate({},100,function(){angular.element(this).position({of:angular.element(_that).parents(".main-multiSelect-wrapper"),my:"left top",at:"left bottom",collision:"flipfit"}).animate({opacity:1},100)})};$scope.cancelBadge=data=>{data.selected=false;$scope.showPlaceholder=$scope.options.some(item=>item.selected===true)};$scope.selectItem=function(option,e,flag){if(flag){$(e.target).parents('.main-multiSelect-wrapper').find('.multiselctID')[0].value='';option.selected=!option.selected}$scope.showPlaceholder=$scope.options.some(item=>item.selected===true)}},link:function(scope,element,attrs){function onMouseup(e){let container=angular.element(".list-multiSelect-search");if(!container.is(e.target)&&container.has(e.target).length===0){container.removeClass("open");container.hide()}let container1=angular.element(".multiSelect-option-list");if(!container1.is(e.target)&&container1.has(e.target).length===0){container1.removeClass("open");container1.hide()}let container2=angular.element(".multi-confirm-prompt");if(!container2.is(e.target)&&container2.has(e.target).length===0){container2.removeClass("open");container2.hide()}}$document.on("mouseup",onMouseup);scope.$on("$destroy",function(){$document.off("mouseup",onMouseup)})}}}).directive("tcmFacilities",function($document){return{restrict:"E",scope:{placeholder:"@",facilitytype:"=?",multiselect:"=?",badge:"=",noOfBadges:"=",isDisabled:'=?',model:'=',onChange:"&",confirmAlertPosition:"=",showConfirm:"=?",filterName:"@",showalloption:"=?"},template:`
      <div class="custom-multiselect-input infiniteFacilityScrollDiv">
    <div class="multi-select-input-group" data-ng-class="{active: isDropDownOpen, disabled:isDisabled}">
        <div class="badge-wrapper" ng-if="checkValueExist() || showalloption" style="display: block">
            <div class="badges" ng-if="!checkValueExist() && alloptions.selected"> 
                <span class="badges-text" tooltip-class="custom-white-bg arrow-right-bottom" ng-bind="alloptions.name"></span>
                <i class="icon icon-close" ng-click="alloptions.selected=false"></i>
            </div>
            <div class="badges" ng-repeat="item in selectedList | limitTo: noOfBadges?noOfBadges:2" ng-if="item.name && item.id > 0"> 
                <span class="badges-text" tooltip-enable="{{item.name.length>10?true:false}}"  tooltip-placement="top"
                uib-tooltip="{{item.name}}"  tooltip-append-to-body="true"
                tooltip-class="custom-white-bg arrow-right-bottom" ng-bind="item.name"></span>
                <i class="icon icon-close" ng-click="discardBadge(item, index)"></i>
            </div>
        </div>
        <input ng-readonly="!multiselect && checkValueExist()" type="text" placeholder="{{(!multiselect && !checkValueExist()) ? placeholder : ''}}" ng-keyup="searchFacility($event)" ng-model="searchText" > 
        <div class="selected-list"  ng-if="selectedList.length>1 && multiselect" ng-click="showSelectedPopover()">
            <span class="count">+{{selectedList.length-1}}</span>
        </div>
        <div class="multi-select-input-group-addon" ng-click="getAllFacilities()">
            <span class="icon icon-arrow"></span>      
        </div>
        <div class="multi-select-input-group-addon" ng-click="discardSelected()" ng-if="multiselect && checkValueExist()">
            <span class="icon icon-close"></span>  
        </div>
    </div>
    <perfect-scrollbar class="multiselect-dropdown-list" id= "FacilityScrollbar" wheel-propagation="true" ng-if="isDropDownOpen"
        swipe-propagation="true" refresh-on-change="someArray" on-scroll="scrollHandler(scrollTop, scrollHeight)" always-visible="true" ng-style="{'max-height': scrollerHeight}">
        <ul class="nopadding nomargin mb-0">
            <li ng-if="showalloption"  ng-click="selectListValue(alloptions)">
                <span ng-bind="alloptions.name"></span>
            </li>
            <li ng-repeat="item in options" ng-click="selectListValue(item)">
                <div class="text-ellipse" ellipses-tooltip placement="'bottom'" class-name="'multiselect-tooltip'" content="item.name" >
                  <span ng-bind="item.name" ></span>
                </div> 
            </li>
            <li class="tcnEndOfListLi" ng-if="!noRecordFound && isEndOfList">Please continue your search by typing</li>
            <li ng-if="noRecordFound">
                <span>No record found</span>
            </li>
        </ul>
        </perfect-scrollbar>
    <div class="selected-list-wrapper" ng-if="showSelectedList && selectedList.length>1">
      <perfect-scrollbar class="scroller">
      <ul class="nopadding nomargin">
          <li class="flex justify-content-between" ng-repeat="item in selectedList" ng-if="!$first">
              <span ng-bind="item.name" title="{{item.name}}" class="text-ellipse mr5"></span>
              <span class="icon-close icon-close" ng-click="discardBadge(item, index);showSelectedList=false"></span>  
          </li>
      </ul>
      </perfect-scrollbar>
    </div>

    <div class="confirmation-propmt"  ng-class="{'right': confirmAlertPosition}" ng-show="showConfirmationDelete">
      <div class="popup-arrow yellow-toast">
        <div class="left-section">
            <i class="icon pcc-icon-warning color-black"></i>
        </div>
        <div class="rightsection d-flex">
            <div class="fnt12bold">Are you sure you want to clear these selections? </div>
            <div class="d-flex ml10 gap-5">
                <button type="button" class="btn btn-xs" name="button" ng-click="showConfirmationDelete=false">No</button>
                <button type="button" class="btn btn-xs" name="button" ng-click="resetOptions();">Yes</button>
            </div>
        </div>
      </div>
    </div>                                                            
</div>`,controller:function($scope,$timeout,commonServiceFactory){$scope.isDropDownOpen=false;$scope.selectedList=[];$scope.showSelectedList=false;$scope.searchText="";$scope.showConfirmationDelete=false;$scope.isDisabled=angular.isDefined($scope.isDisabled)?$scope.isDisabled:false;$scope.showConfirm=angular.isDefined($scope.showConfirm)?$scope.showConfirm:false;$scope.multiselect=angular.isDefined($scope.multiselect)?$scope.multiselect:true;$scope.showalloption=angular.isDefined($scope.showalloption)?$scope.showalloption:false;$scope.filterName=angular.isDefined($scope.filterName)?$scope.filterName:'facility';$scope.facilitytype=angular.isDefined($scope.facilitytype)?$scope.facilitytype:"";$scope.isEndOfList=false;$scope.dropdownType=$scope.multiselect?'multiselect':'singleselect';$scope.pageNumber=0;$scope.rowPerPage=20;$scope.maxSize=100;$scope.options=[];$scope.isNoMoreRecords=false;$scope.alloptions={name:'All',id:0,selected:true};$scope.isFirstCall=true;$scope.minCharLookupVal=3;let timer="";$scope.$watch('model',function(newValue,oldValue){if(newValue){$scope.selectedList=newValue&&newValue.length>0&&newValue[0]?.id>0?newValue:[];if($scope.selectedList.length===0){$scope.alloptions.selected=true}}},true);setTimeout(function(){$('.custom-multiselect-input').find('.infiniteFacilityScrollDiv').on('scroll',$scope.scrollHandler())},500);$scope.checkValueExist=function(){return $scope.selectedList.findIndex(el=>el?.id>0)>-1};$scope.scrollHandler=(scrollTop,scrollHeight)=>{if(scrollTop+scrollHeight>480){let position=Object.keys($scope.options).length;if(position>=$scope.maxSize){$timeout(function(){$scope.isEndOfList=true})}else{if($scope.isNoMoreRecords||$scope.isEndOfList){return}$timeout(function(){$scope.pageNumber+=1;$scope.loadFacilityList()},250)}}};$scope.selectListValue=item=>{if(item.name==='All'){$scope.selectedList=[];$scope.alloptions.selected=true}else{$scope.alloptions.selected=false;if($scope.multiselect){if($scope.selectedList.findIndex(el=>el.id===item.id)===-1){$scope.selectedList.push(item);item.selected=!item.selected}}else{$scope.searchText='';$scope.isDropDownOpen=false;$scope.selectedList[0]=item}}$scope.callOnChange()};$scope.callOnChange=function(){$scope.onChange({data:{filterName:$scope.filterName,modelVal:$scope.selectedList,type:$scope.dropdownType}})};$scope.discardSelected=()=>{if($scope.showConfirm){$scope.showConfirmationDelete=true}else{$scope.selectedList.forEach(el=>el.selected=false);$scope.resetOptions()}};$scope.discardBadge=item=>{let index=$scope.selectedList.findIndex(el=>el.id===item.id);$scope.selectedList.splice(index,1);item.selected=!item.selected;$scope.showConfirmationDelete=false;$scope.callOnChange()};$scope.showSelectedPopover=()=>{$scope.showSelectedList=!$scope.showSelectedList};$scope.getAllFacilities=function(){$scope.pageNumber=1;$scope.options=[];$scope.searchText='';$scope.loadFacilityList()};$scope.searchFacility=function(e){if(e&&e.type=="keyup"){switch(e.keyCode){case 9:e.stopPropagation();break}}if($scope.searchText&&$scope.searchText.length>=$scope.minCharLookupVal){if(timer&&timer!=''){$timeout.cancel(timer)}timer=$timeout(function(){$scope.pageNumber=1;$scope.options=[];$scope.loadFacilityList()},500)}};$scope.loadFacilityList=async()=>{$scope.isDropDownOpen=true;$scope.noRecordFound=false;let reqFacType="";if($scope.facilitytype&&$scope.facilitytype>0){reqFacType=$scope.facilitytype}let param={pageNo:$scope.pageNumber,rowsPerPage:$scope.rowPerPage,hospitalType:reqFacType,term:$scope.searchText};let promiseObj=commonServiceFactory.getPromiseService({url:"/mobiledoc/emr/ecw.tcm/getAgencyFacilityList",data:param});const[error,response]=await commonServiceFactory.getCallbackData(promiseObj);if(response){if(response.data.responseData.length>0){$scope.setResponseData(response.data.responseData)}else{$timeout(function(){$scope.noRecordFound=true},100)}}else if(error){notification.show("error","TCN Facility Filters","Something went wrong",4e3)}$scope.isFirstCall=false};$scope.setResponseData=function(resList){if(resList.length<$scope.rowPerPage){$scope.isNoMoreRecords=true}$timeout(function(){if($scope.options.length>0){$scope.options.push(...resList)}else{$scope.options=resList}},100)};$scope.resetOptions=()=>{$scope.selectedList=[];$scope.isDropDownOpen=false;$scope.searchText="";$scope.callOnChange()}},link:function(scope,element,attrs){var onMouseup=function(e){var container=angular.element(element);if(!container.is(e.target)&&container.has(e.target).length===0){scope.isDropDownOpen=false;scope.showSelectedList=false}};$document.on("mouseup",onMouseup);scope.$on("$destroy",function(){$document.off("mouseup",onMouseup)})}}}).directive("tcmStructMultiSelect",function($document){return{restrict:"E",scope:{placeholder:"@",multiselect:"=?",badge:"=",noOfBadges:"=",isDisabled:'=?',model:'=',onChange:"&",itemKey:"@",itemId:'=',confirmAlertPosition:"=",showConfirm:"=?",filterName:"@",showalloption:"=?"},template:`
      <div class="custom-multiselect-input infiniteStructDataScrollDiv_{{$id}} ">
    <div class="multi-select-input-group" data-ng-class="{active: isDropDownOpen, disabled:isDisabled}">
        <div class="badge-wrapper" ng-if="selectedList.length>0 || showalloption" style="display: block">
            <div class="badges" ng-if="selectedList.length <= 0 && alloptions.selected"> 
                <span class="badges-text" tooltip-class="custom-white-bg arrow-right-bottom" ng-bind="alloptions.name"></span>
                <i class="icon icon-close" ng-click="alloptions.selected=false"></i>
            </div>
            <div class="badges" ng-repeat="item in selectedList | limitTo: noOfBadges?noOfBadges:2" ng-if="item.name && item.id > 0"> 
                <span class="badges-text" tooltip-enable="{{item.name.length>10?true:false}}"  tooltip-placement="top"
                uib-tooltip="{{item.name}}"  tooltip-append-to-body="true"
                tooltip-class="custom-white-bg arrow-right-bottom" ng-bind="item.name"></span>
                <i class="icon icon-close" ng-click="discardBadge(item, index)"></i>
            </div>
        </div>
        <input ng-readonly="selectedList.length > 0" type="text" placeholder="{{(selectedList.length <= 0) ? placeholder : ''}}" ng-keyup="searchStructData($event)" ng-model="searchText" > 
        <div class="selected-list"  ng-if="selectedList.length>1 && multiselect" ng-click="showSelectedPopover()">
            <span class="count">+{{selectedList.length-1}}</span>
        </div>
        <div class="multi-select-input-group-addon" ng-click="getAllStructData()">
            <span class="icon icon-arrow"></span>      
        </div>
        <div class="multi-select-input-group-addon" ng-click="discardSelected()" ng-if="selectedList.length>0 && multiselect">
            <span class="icon icon-close"></span>  
        </div>
    </div>
    <perfect-scrollbar class="multiselect-dropdown-list" id= "StructDataScrollbar" wheel-propagation="true" ng-if="isDropDownOpen"
        swipe-propagation="true" refresh-on-change="someArray" on-scroll="scrollHandler(scrollTop, scrollHeight)" always-visible="true" ng-style="{'max-height': scrollerHeight}">
        <ul class="nopadding nomargin mb-0">
            <li ng-if="showalloption"  ng-click="selectListValue(alloptions)">
                <span ng-bind="alloptions.name"></span>
            </li>
            <li ng-repeat="item in options" ng-click="selectListValue(item)">
                <div class="text-ellipse" ellipses-tooltip placement="'bottom'" class-name="'multiselect-tooltip'" content="item.name" >
                  <span title="{{item.name}}" ng-bind="item.name"></span>
                </div> 
            </li>
            <li class="tcnEndOfListLi" ng-if="!noRecordFound && isEndOfList">Please continue your search by typing</li>
            <li ng-if="noRecordFound">
                <span>No record found</span>
            </li>
        </ul>
        </perfect-scrollbar>
    <div class="selected-list-wrapper" ng-if="showSelectedList && selectedList.length>1">
      <perfect-scrollbar class="scroller">
      <ul class="nopadding nomargin">
          <li class="flex justify-content-between" ng-repeat="item in selectedList" ng-if="!$first">
              <span ng-bind="item.name" title="{{item.name}}" class="text-ellipse mr5"></span>
              <span class="icon-close icon-close" ng-click="discardBadge(item, index);showSelectedList=false"></span>  
          </li>
      </ul>
      </perfect-scrollbar>
    </div>

    <div class="confirmation-propmt"  ng-class="{'right': confirmAlertPosition}" ng-show="showConfirmationDelete">
      <div class="popup-arrow yellow-toast">
        <div class="left-section">
            <i class="icon pcc-icon-warning color-black"></i>
        </div>
        <div class="rightsection d-flex">
            <div class="fnt12bold">Are you sure you want to clear these selections? </div>
            <div class="d-flex ml10 gap-5">
                <button type="button" class="btn btn-xs" name="button" ng-click="showConfirmationDelete=false">No</button>
                <button type="button" class="btn btn-xs" name="button" ng-click="resetOptions();">Yes</button>
            </div>
        </div>
      </div>
    </div>                                                            
</div>`,controller:function($scope,$timeout,commonServiceFactory){$scope.isDropDownOpen=false;$scope.selectedList=[];$scope.showSelectedList=false;$scope.searchText="";$scope.showConfirmationDelete=false;$scope.isDisabled=angular.isDefined($scope.isDisabled)?$scope.isDisabled:false;$scope.showConfirm=angular.isDefined($scope.showConfirm)?$scope.showConfirm:false;$scope.multiselect=angular.isDefined($scope.multiselect)?$scope.multiselect:true;$scope.showalloption=angular.isDefined($scope.showalloption)?$scope.showalloption:false;$scope.itemKey=angular.isDefined($scope.itemKey)?$scope.itemKey:'';$scope.itemId=angular.isDefined($scope.itemId)?$scope.itemId:0;$scope.filterName=angular.isDefined($scope.filterName)?$scope.filterName:'facility';$scope.isEndOfList=false;$scope.dropdownType=$scope.multiselect?'multiselect':'singleselect';$scope.pageNumber=0;$scope.rowPerPage=20;$scope.maxSize=100;$scope.options=[];$scope.isNoMoreRecords=false;$scope.alloptions={name:'All',id:0,selected:true};$scope.isFirstCall=true;$scope.minCharLookupVal=3;let timer="";$scope.$watch('model',function(newValue,oldValue){if(newValue){$scope.selectedList=newValue;if($scope.selectedList.length===0){$scope.alloptions.selected=true}}},true);$scope.isLoading=false;setTimeout(function(){$('.infiniteStructDataScrollDiv_'+$scope.$id).on('scroll',$scope.scrollHandler())},500);$scope.scrollHandler=(scrollTop,height)=>{if($scope.isLoading){return}let _scrollObj=$('.infiniteStructDataScrollDiv_'+$scope.$id).find('#StructDataScrollbar');let scrollHeight=_scrollObj.length>0?_scrollObj[0].scrollHeight:120;if(scrollTop+height>scrollHeight-120){let position=Object.keys($scope.options).length;if(position>=$scope.maxSize){$scope.isEndOfList=true}else{if($scope.isNoMoreRecords||$scope.isEndOfList){return}$timeout(function(){$scope.pageNumber+=1;$scope.loadStructDataList()},250)}}};$scope.selectListValue=item=>{if(item.name==='All'){$scope.selectedList=[];$scope.alloptions.selected=true}else{$scope.alloptions.selected=false;$scope.searchText='';if($scope.multiselect){if($scope.selectedList.findIndex(el=>el.id===item.id)===-1){$scope.selectedList.push(item);item.selected=!item.selected}}else{$scope.isDropDownOpen=false;$scope.selectedList[0]=item}}$scope.callOnChange()};$scope.callOnChange=function(){$scope.onChange({data:{filterName:$scope.filterName,modelVal:$scope.selectedList,type:$scope.dropdownType}})};$scope.discardSelected=()=>{if($scope.showConfirm){$scope.showConfirmationDelete=true}else{$scope.selectedList.forEach(el=>el.selected=false);$scope.resetOptions()}};$scope.discardBadge=item=>{let index=$scope.selectedList.findIndex(el=>el.id===item.id);$scope.selectedList.splice(index,1);item.selected=!item.selected;$scope.showConfirmationDelete=false;$scope.callOnChange()};$scope.showSelectedPopover=()=>{$scope.showSelectedList=!$scope.showSelectedList};$scope.getAllStructData=function(){$scope.pageNumber=1;$scope.options=[];$scope.searchText='';$scope.isNoMoreRecords=false;$scope.isEndOfList=false;$scope.isLoading=false;$scope.loadStructDataList()};$scope.searchStructData=function(e){if(e&&e.type=="keyup"){switch(e.keyCode){case 9:e.stopPropagation();break}}if($scope.searchText&&$scope.searchText.length>=$scope.minCharLookupVal){if(timer&&timer!=''){$timeout.cancel(timer)}timer=$timeout(function(){$scope.pageNumber=1;$scope.options=[];$scope.loadStructDataList()},500)}};$scope.loadStructDataList=async()=>{$scope.isLoading=true;$scope.isDropDownOpen=true;$scope.noRecordFound=false;let param={pageNo:$scope.pageNumber,rowsPerPage:$scope.rowPerPage,structItemKey:$scope.itemKey,structItemId:$scope.itemId,searchTerm:$scope.searchText};let promiseObj=commonServiceFactory.getPromiseService({url:"/mobiledoc/emr/ecw.tcm/getFilterStructDataVal",data:param});const[error,response]=await commonServiceFactory.getCallbackData(promiseObj);if(response){let responseList=JSON.parse(response.data.responseData);if(responseList.length>0){$scope.setResponseData(responseList)}else{$timeout(function(){if($scope.searchText)$scope.noRecordFound=true;$scope.isLoading=false},100)}}else if(error){notification.show("error","TCN StructData Filters","Something went wrong",4e3)}$scope.isFirstCall=false};$scope.setResponseData=function(resList){if(resList.length<$scope.rowPerPage){$scope.isNoMoreRecords=true}$timeout(function(){if($scope.options.length>0){$scope.options.push(...resList)}else{$scope.options=resList}$scope.isLoading=false},100)};$scope.resetOptions=()=>{$scope.selectedList=[];$scope.isDropDownOpen=false;$scope.searchText="";$scope.callOnChange()}},link:function(scope,element,attrs){var onMouseup=function(e){var container=angular.element(element);if(!container.is(e.target)&&container.has(e.target).length===0){scope.isDropDownOpen=false;scope.showSelectedList=false}};$document.on("mouseup",onMouseup);scope.$on("$destroy",function(){$document.off("mouseup",onMouseup)})}}}).directive("tcmFacilityTypes",function($document){return{restrict:"E",scope:{placeholder:"@",multiselect:"=?",badge:"=",noOfBadges:"=",isDisabled:'=?',model:'=',onChange:"&",confirmAlertPosition:"=",showConfirm:"=?",filterName:"@",showalloption:"=?"},template:`
      <div class="custom-multiselect-input infiniteFacilityTypeDataScrollDiv_{{$id}} ">
    <div class="multi-select-input-group" data-ng-class="{active: isDropDownOpen, disabled:isDisabled}">
        <div class="badge-wrapper" ng-if="checkValueExist() || showalloption" style="display: block">
            <div class="badges" ng-if="!checkValueExist() && alloptions.selected"> 
                <span class="badges-text" tooltip-class="custom-white-bg arrow-right-bottom"  ng-bind="alloptions.name"></span>
                <i class="icon icon-close" ng-click="alloptions.selected=false"></i>
            </div>
            <div class="badges" ng-repeat="item in selectedList | limitTo: noOfBadges?noOfBadges:2" ng-if="item.name && item.id > 0"> 
                <span class="badges-text" tooltip-enable="{{item.name.length>27?true:false}}"  tooltip-placement="top"
                uib-tooltip="{{item.name}}"  tooltip-append-to-body="true"
                tooltip-class="custom-white-bg arrow-right-bottom" ng-bind="item.name" ></span>
                <i class="icon icon-close" ng-click="discardBadge(item, index)"></i>
            </div>
        </div>
        <input ng-readonly="!multiselect && checkValueExist()" type="text" placeholder="{{(!multiselect && !checkValueExist()) ? placeholder : ''}}" ng-keyup="searchFacilityTypeData($event)" ng-model="searchText" > 
        <div class="selected-list"  ng-if="selectedList.length>1 && multiselect" ng-click="showSelectedPopover()">
            <span class="count">+{{selectedList.length-1}}</span>
        </div>
        <div class="multi-select-input-group-addon" ng-click="getAllFacilityTypeData()">
            <i class="fa fa-caret-down fa-lg"></i>
        </div>
        <div class="multi-select-input-group-addon" ng-click="discardSelected()" ng-if="multiselect && checkValueExist()">
            <span class="icon icon-close"></span>  
        </div>
    </div>
    <perfect-scrollbar class="multiselect-dropdown-list" id= "FacilityTypeDataScrollbar" wheel-propagation="true" ng-if="isDropDownOpen"
        swipe-propagation="true" refresh-on-change="someArray" on-scroll="scrollHandler(scrollTop, scrollHeight)" always-visible="true" ng-style="{'max-height': scrollerHeight}">
        <ul class="nopadding nomargin mb-0">
            <li ng-if="showalloption"  ng-click="selectListValue(alloptions,$event)">
                <span ng-bind="alloptions.name"></span>
            </li>
            <li ng-repeat="item in options" ng-click="selectListValue(item,$event)">
                <div ng-show="multiselect" class="form-check-inline">
                    <input type="checkbox" ng-click="selectListValue(item,$event)" ng-disabled="isDisabled" ng-model="item.selected">
                </div>
                <div class="text-ellipse" ellipses-tooltip placement="'bottom'" class-name="'multiselect-tooltip'" content="item.name" >
                  <span title="{{item.name}}" ng-bind="item.name"></span>
                </div> 
            </li>
            <li class="tcnEndOfListLi" ng-if="!noRecordFound && isEndOfList">Please continue your search by typing</li>
            <li ng-if="noRecordFound">
                <span>No record found</span>
            </li>
        </ul>
        </perfect-scrollbar>
    <div class="selected-list-wrapper" ng-if="showSelectedList && selectedList.length>1">
      <perfect-scrollbar class="scroller">
      <ul class="nopadding nomargin">
          <li class="flex justify-content-between" ng-repeat="item in selectedList" ng-if="!$first">
              <span ng-bind="item.name" title="{{item.name}}" class="text-ellipse w120px mr5"></span>
              <span class="icon-close icon-close" ng-click="discardBadge(item, index);showSelectedList=false"></span>  
          </li>
      </ul>
      </perfect-scrollbar>
    </div>

    <div class="confirmation-propmt"  ng-class="{'right': confirmAlertPosition}" ng-show="showConfirmationDelete">
      <div class="popup-arrow yellow-toast">
        <div class="left-section">
            <i class="icon pcc-icon-warning color-black"></i>
        </div>
        <div class="rightsection d-flex">
            <div class="fnt12bold">Are you sure you want to clear these selections? </div>
            <div class="d-flex ml10 gap-5">
                <button type="button" class="btn btn-xs" name="button" ng-click="showConfirmationDelete=false">No</button>
                <button type="button" class="btn btn-xs" name="button" ng-click="resetOptions();">Yes</button>
            </div>
        </div>
      </div>
    </div>                                                            
</div>`,controller:function($scope,$timeout,commonServiceFactory){$scope.isDropDownOpen=false;$scope.selectedList=[];$scope.showSelectedList=false;$scope.searchText="";$scope.showConfirmationDelete=false;$scope.isDisabled=angular.isDefined($scope.isDisabled)?$scope.isDisabled:false;$scope.showConfirm=angular.isDefined($scope.showConfirm)?$scope.showConfirm:false;$scope.multiselect=angular.isDefined($scope.multiselect)?$scope.multiselect:true;$scope.showalloption=angular.isDefined($scope.showalloption)?$scope.showalloption:false;$scope.filterName=angular.isDefined($scope.filterName)?$scope.filterName:'facility';$scope.isEndOfList=false;$scope.dropdownType=$scope.multiselect?'multiselect':'singleselect';$scope.pageNumber=0;$scope.rowPerPage=100;$scope.maxSize=100;$scope.options=[];$scope.isNoMoreRecords=false;$scope.alloptions={name:'All',id:0,selected:true};$scope.isFirstCall=true;$scope.minCharLookupVal=3;let timeoutArr={timerForScroll:"",timerForSearch:"",timerForNotFound:"",timerForResponse:"",timerForCloseDropdown:""};$scope.checkValueExist=function(){return $scope.selectedList.findIndex(el=>el?.id>0)>-1};$scope.$watch('model',function(newValue,oldValue){if(newValue){$scope.selectedList=newValue&&newValue.length>0&&newValue[0]?.id>0?newValue:[];if($scope.selectedList.length===0){$scope.alloptions.selected=true}}},true);$scope.isLoading=false;setTimeout(function(){$('.infiniteFacilityTypeDataScrollDiv_'+$scope.$id).on('scroll',$scope.scrollHandler())},500);$scope.scrollHandler=(scrollTop,height)=>{if($scope.isLoading){return}let _scrollObj=$('.infiniteFacilityTypeDataScrollDiv_'+$scope.$id).find('#FacilityTypeDataScrollbar');let scrollHeight=_scrollObj.length>0?_scrollObj[0].scrollHeight:120;if(scrollTop+height>scrollHeight-120){let position=Object.keys($scope.options).length;if(position>=$scope.maxSize){$scope.isEndOfList=true}else{if($scope.isNoMoreRecords||$scope.isEndOfList){return}cancelTimeout(timeoutArr.timerForScroll);timeoutArr.timerForScroll=$timeout(function(){$scope.pageNumber+=1;$scope.loadFacilityTypeDataList()},250)}}};$scope.selectListValue=(item,$event)=>{if($event){$event.stopPropagation()}if(item.name==='All'){$scope.selectedList=[];$scope.alloptions.selected=true;$scope.options.forEach(item=>{$scope.isDropDownOpen=false})}else{$scope.alloptions.selected=false;$scope.searchText='';if($scope.multiselect){let selectedIndex=$scope.selectedList.findIndex(el=>el.id===item.id);if(selectedIndex===-1){$scope.selectedList.push(item);item.selected=!item.selected}else{$scope.discardBadge(item)}}else{$scope.isDropDownOpen=false;$scope.selectedList[0]=item}}$scope.callOnChange()};$scope.callOnChange=function(){$scope.onChange({data:{filterName:$scope.filterName,modelVal:$scope.selectedList,type:$scope.dropdownType}})};$scope.discardSelected=()=>{if($scope.showConfirm){$scope.showConfirmationDelete=true}else{$scope.selectedList.forEach(el=>el.selected=false);$scope.options.forEach(el=>el.selected=false);$scope.resetOptions()}};$scope.discardBadge=item=>{let index=$scope.selectedList.findIndex(el=>el.id===item.id);$scope.selectedList.splice(index,1);item.selected=!item.selected;$scope.options.forEach(item=>{if($scope.selectedList.findIndex(el=>el.id===item.id)>-1){item.selected=true}});$scope.showConfirmationDelete=false;$scope.callOnChange()};$scope.showSelectedPopover=()=>{$scope.isDropDownOpen=false;$scope.showSelectedList=true};$scope.getAllFacilityTypeData=function(){$scope.pageNumber=1;$scope.options=[];$scope.searchText='';$scope.isNoMoreRecords=false;$scope.isEndOfList=false;$scope.isLoading=false;$scope.loadFacilityTypeDataList()};$scope.searchFacilityTypeData=function(e){if(e&&e.type=="keyup"){switch(e.keyCode){case 9:e.stopPropagation();break}}if($scope.searchText&&$scope.searchText.length>=$scope.minCharLookupVal){cancelTimeout(timeoutArr.timerForSearch);timeoutArr.timerForSearch=$timeout(function(){$scope.pageNumber=1;$scope.options=[];$scope.loadFacilityTypeDataList()},250)}};$scope.loadFacilityTypeDataList=async()=>{$scope.isLoading=true;$scope.isDropDownOpen=true;$scope.showSelectedList=false;$scope.noRecordFound=false;let param={pageNo:$scope.pageNumber,rowsPerPage:$scope.rowPerPage,searchText:$scope.searchText};let promiseObj=commonServiceFactory.getPromiseService({url:"/mobiledoc/emr/ecw.tcm/getAgencyFacilityTypeList",data:param});const[error,response]=await commonServiceFactory.getCallbackData(promiseObj);if(response&&response.data){let responseList=response.data.responseData;if(responseList.length>0){$scope.setResponseData(responseList)}else{cancelTimeout(timeoutArr.timerForNotFound);timeoutArr.timerForNotFound=$timeout(function(){if($scope.searchText){$scope.noRecordFound=true}$scope.isLoading=false},250)}}else if(error){notification.show("error","TCM facility type","Something went wrong",4e3)}$scope.isFirstCall=false};$scope.setResponseData=function(resList){if(resList.length<$scope.rowPerPage){$scope.isNoMoreRecords=true}cancelTimeout(timeoutArr.timerForResponse);timeoutArr.timerForResponse=$timeout(function(){if($scope.options.length>0){$scope.options.push(...resList)}else{$scope.options=resList}$scope.options.forEach(item=>{if($scope.selectedList.findIndex(el=>el.id===item.id)>-1){item.selected=true}});$scope.isLoading=false},100)};$scope.resetOptions=()=>{$scope.selectedList=[];$scope.isDropDownOpen=false;$scope.searchText="";$scope.callOnChange()};$scope.closeDropdown=function(){cancelTimeout(timeoutArr.timerForCloseDropdown);timeoutArr.timerForCloseDropdown=$timeout(function(){$scope.isDropDownOpen=false;$scope.showSelectedList=false},100)};function cancelTimeout(timeoutObj){if(timeoutObj)$timeout.cancel(timeoutObj)}function cleanup(){for(let timer in timeoutArr){cancelTimeout(timeoutArr[timer])}removeScopePropertyAndMethod($scope)}$scope.$on("$destroy",cleanup)},link:function(scope,element,attrs){function onMouseup(e){var container=angular.element(element);if(!container.is(e.target)&&container.has(e.target).length===0){scope.closeDropdown()}}$document.on("mouseup",onMouseup);scope.$on("$destroy",function(){$document.off("mouseup",onMouseup)})}}}).directive("tcmEdiFacilities",function($document){return{restrict:"E",scope:{placeholder:"@",multiselect:"=?",badge:"=",noOfBadges:"=",isDisabled:'=?',model:'=',onChange:"&",confirmAlertPosition:"=",showConfirm:"=?",filterName:"@",showalloption:"=?"},template:`
      <div class="custom-multiselect-input infiniteEdiFacilityDataScrollDiv_{{$id}} ">
        <div class="multi-select-input-group" data-ng-class="{active: isDropDownOpen, disabled:isDisabled}">
            <div class="badge-wrapper" ng-if="checkValueExist() || showalloption" style="display: block">
                <div class="badges" ng-if="!checkValueExist() && alloptions.selected"> 
                    <span class="badges-text" tooltip-class="custom-white-bg arrow-right-bottom" ng-bind="alloptions.name"></span>
                    <i class="icon icon-close" ng-click="alloptions.selected=false"></i>
                </div>
                <div class="badges" ng-repeat="item in selectedList | limitTo: noOfBadges?noOfBadges:2" ng-if="item.name && item.id > 0"> 
                    <span class="badges-text" tooltip-enable="{{item.name.length>10?true:false}}"  tooltip-placement="top"
                    uib-tooltip="{{item.name}}"  tooltip-append-to-body="true"
                    tooltip-class="custom-white-bg arrow-right-bottom" ng-bind="item.name"></span>
                    <i class="icon icon-close" ng-click="discardBadge(item, index)"></i>
                </div>
            </div>
            <input ng-readonly="!multiselect && checkValueExist()" type="text" placeholder="{{(!multiselect && !checkValueExist()) ? placeholder : ''}}" ng-keyup="searchEdiFacilityData($event)" ng-model="searchText" > 
            <div class="selected-list"  ng-if="selectedList.length>1 && multiselect" ng-click="showSelectedPopover()">
                <span class="count">+{{selectedList.length-1}}</span>
            </div>
            <div class="multi-select-input-group-addon" ng-click="getAllEdiFacilityData()">
                <i class="fa fa-caret-down fa-lg"></i>
            </div>
            <div class="multi-select-input-group-addon" ng-click="discardSelected()" ng-if="multiselect && checkValueExist()">
                <span class="icon icon-close"></span>  
            </div>
        </div>
        <perfect-scrollbar class="multiselect-dropdown-list" id= "EdiFacilityDataScrollbar" wheel-propagation="true" ng-if="isDropDownOpen"
            swipe-propagation="true" refresh-on-change="someArray" on-scroll="scrollHandler(scrollTop, scrollHeight)" always-visible="true" ng-style="{'max-height': scrollerHeight}">
            <ul class="nopadding nomargin mb-0">
                <li ng-if="showalloption"  ng-click="selectListValue(alloptions)">
                    <span ng-bind="alloptions.name"></span>
                </li>
                <li ng-repeat="item in options" ng-click="selectListValue(item)">
                    <div class="form-check-inline" ng-if="multiselect">
                        <input type="checkbox" ng-change="selectListValue(item)" ng-disabled="isDisabled" ng-model="item.selected">
                    </div>
                    <div class="text-ellipse" ellipses-tooltip placement="'bottom'" class-name="'multiselect-tooltip'" content="item.name" >
                      <span title="{{item.name}}" ng-bind="item.name"></span>
                    </div> 
                </li>
                <li class="tcnEndOfListLi" ng-if="!noRecordFound && isEndOfList">Please continue your search by typing</li>
                <li ng-if="noRecordFound">
                    <span>No record found</span>
                </li>
            </ul>
            </perfect-scrollbar>
        <div class="selected-list-wrapper" ng-if="showSelectedList && selectedList.length>1">
          <perfect-scrollbar class="scroller">
          <ul class="nopadding nomargin">
              <li class="flex justify-content-between" ng-repeat="item in selectedList" ng-if="!$first">
                  <span ng-bind="item.name" title="{{item.name}}" class="text-ellipse w120px mr5"></span>
                  <span class="icon-close icon-close" ng-click="discardBadge(item, index);showSelectedList=false"></span>  
              </li>
          </ul>
          </perfect-scrollbar>
        </div>
    
        <div class="confirmation-propmt"  ng-class="{'right': confirmAlertPosition}" ng-show="showConfirmationDelete">
          <div class="popup-arrow yellow-toast">
            <div class="left-section">
                <i class="icon pcc-icon-warning color-black"></i>
            </div>
            <div class="rightsection d-flex">
                <div class="fnt12bold">Are you sure you want to clear these selections? </div>
                <div class="d-flex ml10 gap-5">
                    <button type="button" class="btn btn-xs" name="button" ng-click="showConfirmationDelete=false">No</button>
                    <button type="button" class="btn btn-xs" name="button" ng-click="resetOptions();">Yes</button>
                </div>
            </div>
          </div>
        </div>                                                            
    </div>`,controller:function($scope,$http,$timeout){$scope.isDropDownOpen=false;$scope.selectedList=[];$scope.showSelectedList=false;$scope.searchText="";$scope.showConfirmationDelete=false;$scope.facilitylookup={};$scope.facilitylookup.name='';$scope.isDisabled=angular.isDefined($scope.isDisabled)?$scope.isDisabled:false;$scope.showConfirm=angular.isDefined($scope.showConfirm)?$scope.showConfirm:false;$scope.multiselect=angular.isDefined($scope.multiselect)?$scope.multiselect:true;$scope.showalloption=angular.isDefined($scope.showalloption)?$scope.showalloption:false;$scope.filterName=angular.isDefined($scope.filterName)?$scope.filterName:'facility';$scope.isEndOfList=false;$scope.dropdownType=$scope.multiselect?'multiselect':'singleselect';$scope.pageNumber=0;$scope.rowPerPage=20;$scope.maxSize=100;$scope.options=[];$scope.isNoMoreRecords=false;$scope.alloptions={name:'All',id:0,selected:true};$scope.isFirstCall=true;$scope.minCharLookupVal=3;let timeoutArr={timerAttachedScroll:"",timerForScroll:"",timerForSearch:"",timerForNotFound:"",timerForResponse:"",timerForCloseDropdown:""};$scope.checkValueExist=function(){return $scope.selectedList.findIndex(el=>el?.id>0)>-1};$scope.$watch('model',function(newValue,oldValue){if(newValue){$scope.selectedList=newValue&&newValue.length>0&&newValue[0]?.id>0?newValue:[];if($scope.selectedList.length===0){$scope.alloptions.selected=true}}},true);$scope.isLoading=false;cancelTimeout(timeoutArr.timerAttachedScroll);timeoutArr.timerAttachedScroll=$timeout(function(){$('.infiniteEdiFacilityDataScrollDiv_'+$scope.$id).on('scroll',$scope.scrollHandler())},500);$scope.scrollHandler=(scrollTop,height)=>{if($scope.isLoading){return}let _scrollObj=$('.infiniteEdiFacilityDataScrollDiv_'+$scope.$id).find('#EdiFacilityDataScrollbar');let scrollHeight=_scrollObj.length>0?_scrollObj[0].scrollHeight:120;if(scrollTop+height>scrollHeight-120){let position=Object.keys($scope.options).length;if(position>=$scope.maxSize){$scope.isEndOfList=true}else{if($scope.isNoMoreRecords||$scope.isEndOfList){return}cancelTimeout(timeoutArr.timerForScroll);timeoutArr.timerForScroll=$timeout(function(){$scope.pageNumber+=1;$scope.loadEdiFacilityDataList()},250)}}};$scope.selectListValue=item=>{if(item.name==='All'){$scope.selectedList=[];$scope.alloptions.selected=true}else{$scope.alloptions.selected=false;$scope.searchText='';if($scope.multiselect){if($scope.selectedList.findIndex(el=>el.id===item.id)===-1){$scope.selectedList.push(item);item.selected=!item.selected}}else{$scope.isDropDownOpen=false;$scope.selectedList[0]=item}}$scope.callOnChange()};$scope.callOnChange=function(){$scope.onChange({data:{filterName:$scope.filterName,modelVal:$scope.selectedList,type:$scope.dropdownType}})};$scope.discardSelected=()=>{if($scope.showConfirm){$scope.showConfirmationDelete=true}else{$scope.selectedList.forEach(el=>el.selected=false);$scope.resetOptions()}};$scope.discardBadge=item=>{let index=$scope.selectedList.findIndex(el=>el.id===item.id);$scope.selectedList.splice(index,1);item.selected=!item.selected;$scope.showConfirmationDelete=false;$scope.callOnChange()};$scope.showSelectedPopover=()=>{$scope.showSelectedList=true;$scope.isDropDownOpen=false};$scope.getAllEdiFacilityData=function(){$scope.pageNumber=1;$scope.options=[];$scope.searchText='';$scope.isNoMoreRecords=false;$scope.isEndOfList=false;$scope.isLoading=false;$scope.loadEdiFacilityDataList('RETRIEVE_ALL')};$scope.searchEdiFacilityData=function(e){if(e&&e.type=="keyup"){switch(e.keyCode){case 9:e.stopPropagation();break}}if($scope.searchText&&$scope.searchText.length>=$scope.minCharLookupVal){cancelTimeout(timeoutArr.timerForSearch);timeoutArr.timerForSearch=$timeout(function(){$scope.pageNumber=1;$scope.options=[];$scope.loadEdiFacilityDataList('CUSTOM')},250)}};$scope.getURL=function(conditionVar){let url="/mobiledoc/jsp/catalog/xml/edi/getFacilityList.jsp?counter="+($scope.pageNumber-1)*$scope.rowPerPage+"&MAXCOUNT="+$scope.rowPerPage+"&callingForm=AgencyFacility";$scope.facilitylookup.searchby=0;$scope.facilitylookup.facilitytype="0";if($scope.facilitylookup.name!=null&&$scope.facilitylookup.name.trim().length>0){if(conditionVar&&conditionVar==='RETRIEVE_ALL'&&$scope.facilitylookup.name.trim()==="All"){url+="&name=&searchby="+$scope.facilitylookup.searchby}else{url+="&name="+encodeURIComponent($scope.facilitylookup.name)+"&searchby="+$scope.facilitylookup.searchby}}url+="&FacilityType="+$scope.facilitylookup.facilitytype;return url};$scope.loadEdiFacilityDataList=async RETRIEVE_ALL=>{$scope.isDropDownOpen=true;$scope.showSelectedList=false;$scope.noRecordFound=false;$scope.facilitylookup.name=$scope.searchText;const url=makeURL($scope.getURL(RETRIEVE_ALL));try{$scope.isLoading=true;const response=await $http({method:'GET',url:url,headers:{'Content-Type':'application/x-www-form-urlencoded'}});if(response&&response.data){const jsonData=convertInJSON(response.data.trim());const status=jsonData.Envelope.Body['return'].status;if(status==="success"){const facilities=jsonData.Envelope.Body['return'].facilities.facility;$scope.ediFacilityArr=returnDataArray(facilities);if($scope.ediFacilityArr&&$scope.ediFacilityArr.length>0){const responseList=$scope.ediFacilityArr.map(item=>({id:item.Id,name:item.Name}));$scope.setResponseData(responseList)}}else{handleError("An error occurred while getting Facilities.")}}}catch(error){handleError("An error occurred while getting Facilities.")}finally{$scope.isLoading=false}};function handleError(msg){alert(msg)}$scope.setResponseData=function(resList){if(resList.length<$scope.rowPerPage){$scope.isNoMoreRecords=true}cancelTimeout(timeoutArr.timerForResponse);timeoutArr.timerForResponse=$timeout(function(){if($scope.options.length>0){$scope.options.push(...resList)}else{$scope.options=resList}if($scope.multiselect){$scope.options.forEach(item=>{if($scope.selectedList.findIndex(el=>el.id===item.id)>-1){item.selected=true}})}$scope.isLoading=false},100)};$scope.resetOptions=()=>{$scope.selectedList=[];$scope.isDropDownOpen=false;$scope.searchText="";$scope.callOnChange()};$scope.closeDropdown=function(){cancelTimeout(timeoutArr.timerForCloseDropdown);timeoutArr.timerForCloseDropdown=$timeout(function(){$scope.isDropDownOpen=false;$scope.showSelectedList=false},100)};function cancelTimeout(timeoutObj){if(timeoutObj)$timeout.cancel(timeoutObj)}function cleanup(){for(let timer in timeoutArr){cancelTimeout(timeoutArr[timer])}$('.infiniteEdiFacilityDataScrollDiv_'+$scope.$id).off('scroll',$scope.scrollHandler());removeScopePropertyAndMethod($scope)}$scope.$on("$destroy",cleanup)},link:function(scope,element,attrs){function onMouseup(e){let container=angular.element(element);if(!container.is(e.target)&&container.has(e.target).length===0){scope.closeDropdown()}}$document.on("mouseup",onMouseup);scope.$on("$destroy",function(){$document.off("mouseup",onMouseup)})}}});