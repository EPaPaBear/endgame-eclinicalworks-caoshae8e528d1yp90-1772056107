angular.module('prisma.clinicalInsights.cumulativelabsTile',['prisma.clinicalInsights.labsTile.service','prismaCiSiUtils']).directive('cumulativelabsTile',['prismaLabTileService','$timeout','$sce','PrismaAppService','PrismaCiSiUtilsService',(PrismaLabTileService,$timeout,$sce,PrismaAppService,PrismaCiSiUtilsService)=>{return{restrict:'E',scope:{cumulativeLabs:'=',allCumulativeLabs:'=',error:'=',header:"@",duplicateLabs:'=',showOrderLabPanel:'=',isFromSearchInsights:'=',highlightCallback:'&',loincClassNames:'=',orderingDetails:'=',patientId:'='},templateUrl:'/mobiledoc/jsp/webemr/toppanel/prisma/template/cumulativeLabsTile.html',link:scope=>{scope.randomId=PrismaLabTileService.getRandomId();scope.isGraph=false;scope.selMonths=PrismaLabTileService.DEFAULT_MONTHS_VIEW;scope.dataPresent=false;scope.attributeName='';scope.isLabDataPrepapred=false;let dataLoadingTimer=null;scope.patientData='';scope.monthFilterClicked=function(months){scope.cumulativeLabs=_.cloneDeep(scope.allCumulativeLabs);scope.selMonths=months;renderTile()};scope.toggleLegendPopup=event=>{PrismaLabTileService.toggleLegendPopup(event,scope.randomId,scope.isGraph)};scope.closeLegendPopup=()=>{PrismaLabTileService.closeLegendPopup(scope.randomId,scope.isGraph)};scope.toggleRecordsPopup=(event,toggleDisplay,data,attributeName)=>{if(data.totalCount<=0){return}scope.totalCount=data?.totalCount;scope.yAll=data?.yAll;scope.attributeName=attributeName;getLabPanelAndSiblings(scope.yAll,scope.yAll[0],scope.patientId,event)};scope.closeLabRecordsPopup=()=>{angular.element(`#cumu-labs-grid-value-popup-${scope.randomId}`).hide(false);scope.dataPresent=false};scope.getLabPanelAndSiblings=(allLabs,lab,patientId,event)=>{return getLabPanelAndSiblings(allLabs,lab,patientId,event)};const getLabPanelAndSiblings=(allLabs,lab,patientId,event)=>{PrismaLabTileService.getLabPanelAndSiblings(allLabs,lab,patientId,event).then(panelAndSiblings=>{scope.panelName=panelAndSiblings?.panelName;scope.collectionDate=PrismaLabTileService.checkDate(panelAndSiblings?.collectionDate);scope.siblings=panelAndSiblings?.siblings;scope.labInterpretation=panelAndSiblings?.labInterpretation;scope.clickedAttrSrc=panelAndSiblings?.siblings?panelAndSiblings?.siblings[0].source:undefined;scope.dataPresent=panelAndSiblings?.dataPresent;allLabs?.forEach(l=>l.status='');lab.status='attributeSelected';let _that=event.target;let currentTarget=event?.currentTarget;scope.clickedElemId=angular.element(currentTarget)?.attr("data-id");let clickedElement=angular.element(_that);if(clickedElement.attr('id')==='attribute-view'){return}const popUpSelector=$(`#cumu-labs-grid-value-popup-${scope.randomId}`);const popupHeight=popUpSelector.height();const popupWeight=popUpSelector.width();const leftBarWidth=$('.leftcontent').width();const rightContentHeight=$('.rightcontent').height();let my='right top';let at=`left+${leftBarWidth+20} bottom`;if($(window).height()-$(_that).offset().top<popupHeight){my='left bottom';at='left top-15';if($(_that).offset().left-leftBarWidth<popupWeight){my='left bottom';at='left top-15'}else if($(_that).offset().left+popupWeight+200-$(window).width()>0){my='right-30 bottom';at='right top-15'}}else if($(_that).offset().top+popupHeight-rightContentHeight>0){my='left top';at='left bottom';if($(_that).offset().left+popupWeight+200-$(window).width()>0){my='right-30 top';at='right bottom'}else if($(_that).offset().left-leftBarWidth<popupWeight){my='left top';at='left bottom'}}else if($(_that).offset().left-leftBarWidth<popupWeight){my='left+15 top';at='right top'}else if($(_that).offset().left+popupWeight+200-$(window).width()>0){my='right-20 top';at='left top'}angular.element(`#cumu-labs-grid-value-popup-${scope.randomId}`).show().animate({},100,function(){angular.element(this).position({of:_that,collision:"flipfit",my:my,at:at,within:".prismaview"}).animate({"opacity":1},10)})})};scope.groupAttributeByPanelWithDuplicate=(jsonArray,loincClassNames)=>{const outputArray=[];jsonArray.forEach(attr=>{attr.masterPanelName.forEach(panel=>{const panelName=panel?.masterPanelName;const className=panel?.panelClass;if(!panelName||!className)return;let found=outputArray.find(item=>item.panel===panelName&&item.category===className);if(!found){found={panel:panelName,category:className,attributes:[],classDisplayName:loincClassNames[className],panelLoinc:panel?.parentLoinc};outputArray.push(found)}found.attributes.push(attr)})});return outputArray.sort((a,b)=>{if(a.classDisplayName===PrismaLabTileService.CATEGORY_OTHERS){if(b.classDisplayName===PrismaLabTileService.CATEGORY_OTHERS){return a.panel.localeCompare(b.panel)}else{return 1}}else{if(b.classDisplayName===PrismaLabTileService.CATEGORY_OTHERS){return-1}else{return(a?.classDisplayName+' '+a?.panel).localeCompare(b?.classDisplayName+' '+b?.panel)}}})};scope.groupAttributeByPanelAndKeepUnique=(jsonArray,loincClassNames)=>{const processOutput=output=>{output=Object.entries(output).sort(([a],[b])=>a!==PrismaLabTileService.CATEGORY_OTHERS&&b!==PrismaLabTileService.CATEGORY_OTHERS?a.localeCompare(b):a===PrismaLabTileService.CATEGORY_OTHERS?1:-1).reduce((acc,[category,data])=>{acc[category]=data;return acc},{});Object.keys(output).forEach(category=>{output[category]=Object.entries(output[category]).sort(([a],[b])=>a.localeCompare(b)).reduce((acc,[panel,data])=>{acc[panel]=data;return acc},{});let seenAttributes=new Map;const SEPARATOR='$$$';Object.keys(output).forEach(category=>{Object.keys(output[category]).forEach(panel=>{output[category][panel].attributes=output[category][panel].attributes.reduce((attributes,attribute)=>{const key=`${category}${SEPARATOR}${attribute.loinc}`;const seenHere=`${category}${SEPARATOR}${panel}`;if(!seenAttributes.has(key)){seenAttributes.set(key,seenHere);attributes.push(attribute)}else{const[wasSeenCategory,wasSeenPanel]=seenAttributes.get(key).split(SEPARATOR);if(category==wasSeenCategory&&panel==wasSeenPanel){attributes.push(attribute)}else if(category==wasSeenCategory&&panel!=wasSeenPanel){const index=output[category][panel].attributes.findIndex(attr=>attr?.labObsPk===attribute?.labObsPk);if(index>-1){delete output[category][panel].attributes[index]}}else if(category!=wasSeenCategory){attributes.push(attribute)}else{}}return attributes},[])})});output[category]=Object.entries(output[category]).reduce((acc,[panel,data])=>{if(data.attributes.length>0){acc[panel]=data}return acc},{})});const outputArray=Object.keys(output).map(className=>{return Object.keys(output[className]).map(panel=>{const panelAttributes=output[className][panel]?.attributes;return{category:className,panel:panel,attributes:panelAttributes,classDisplayName:loincClassNames[className],panelLoinc:panelAttributes.flatMap(({masterPanelName})=>masterPanelName.filter(({masterPanelName:name})=>name===panel)).find(({parentLoinc})=>parentLoinc)?.parentLoinc}})});return[].concat.apply([],outputArray)};const output=jsonArray.reduce((acc,attr)=>{attr.masterPanelName.forEach(panel=>{const panelName=panel?.masterPanelName;const category=panel?.panelClass;const panelLoinc=panel?.parentLoinc;if(!acc[category]){acc[category]={}}if(!acc[category][panelName]){acc[category][panelName]={attributes:[]}}acc[category][panelName].attributes.push(attr)});return acc},{});return processOutput(output)};scope.groupAttributeByAlphabetically=(labs,monthsExpected,cumulativeLabs,months)=>{PrismaLabTileService.processLabAttributes(labs,monthsExpected,cumulativeLabs,months,scope.isGraph,scope.duplicateLabs);cumulativeLabs?.body?.sort((a,b)=>a?.name?.localeCompare(b?.name));return cumulativeLabs};scope.orderLabAttributesWithinPanel=(labData,orderingDetails)=>{const response=_.cloneDeep(labData);response.body.forEach(panel=>{const panelLoinc=panel?.panelLoinc;let matchedOrderingDetail=orderingDetails.find(od=>od.panelLoinc===panelLoinc);if(matchedOrderingDetail){let sortedAttributes=[];let remainingAttributes=[];panel.body.forEach(attribute=>{if(matchedOrderingDetail.attributes[attribute.loinc]!==undefined){if(sortedAttributes[matchedOrderingDetail.attributes[attribute.loinc]-1]!==undefined){let i=matchedOrderingDetail.attributes[attribute.loinc]-1;while(sortedAttributes[i]!==undefined){i++}sortedAttributes[i]=attribute}else{sortedAttributes[matchedOrderingDetail.attributes[attribute.loinc]-1]=attribute}}else{remainingAttributes.push(attribute)}});sortedAttributes=sortedAttributes.filter(a=>a!==undefined);remainingAttributes.sort((a,b)=>a.name.localeCompare(b.name));panel.body=[...sortedAttributes,...remainingAttributes]}else{panel.body.sort((a,b)=>a.name.localeCompare(b.name))}});return response};const initProcessPanels=(parentArray,monthsExpected,months,cumulativeLabs)=>{if(parentArray&&parentArray.length>0){parentArray.forEach(panel=>{const preparedLabsPerPanel={header:[],body:[]};let obj={name:panel?.panel,category:panel?.category,classDisplayName:panel?.classDisplayName,panelLoinc:panel?.panelLoinc,body:[]};PrismaLabTileService.processLabAttributes(panel.attributes,monthsExpected,preparedLabsPerPanel,months,scope.isGraph,scope.duplicateLabs);angular.copy(preparedLabsPerPanel.body,obj.body);if(obj.body.length>0){cumulativeLabs.body.push(obj)}})}};const preparePanelData=(sortedDates,cumulativeLabs)=>{if(cumulativeLabs.body.length>0){const sortedDatesArr=[...sortedDates];const dates=new Set;cumulativeLabs.body.forEach(panel=>{panel.body.forEach(attr=>{attr.data.forEach(d=>{if(d.lineChtDate){const labDate=moment(d.lineChtDate).format(PrismaLabTileService.MMMYYYY);dates.add(labDate)}})})});const datesArr=[...dates];datesArr.sort((a,b)=>sortedDatesArr.indexOf(a)-sortedDatesArr.indexOf(b));datesArr.forEach(date=>{cumulativeLabs.header.push({month:date,display:moment(date,PrismaLabTileService.MMMYYYY).format(PrismaLabTileService.MMDDYYYY)})});cumulativeLabs.body.forEach(panel=>{panel.body.forEach(attr=>{const attrData=Array(cumulativeLabs.header.length).fill({lineChtDate:null,totalCount:0,y:null,yAll:[]});attr.data.forEach(d=>{const labDate=moment(d.lineChtDate).format(PrismaLabTileService.MMMYYYY);const index=cumulativeLabs.header?.findIndex(header=>header.month===labDate);attrData[index]=d});attr.data=attrData})})}};const prepareLabsForGrid=(labs=[],months=PrismaLabTileService.DEFAULT_MONTHS_VIEW)=>{const cumulativeLabs={header:[],body:[]};let monthsExpected=PrismaLabTileService.getExpectedMonths(months);let sortedDates;labs.sort((a,b)=>moment(b?.resultTime,PrismaLabTileService.YYYYMMDDHHMMSS)-moment(a?.resultTime,PrismaLabTileService.YYYYMMDDHHMMSS));let parentArray;sortedDates=PrismaLabTileService.getHeaderForGrid(months,labs,monthsExpected);if(scope.showOrderLabPanel===1){parentArray=scope.groupAttributeByPanelWithDuplicate(labs,scope.loincClassNames);initProcessPanels(parentArray,monthsExpected,months,cumulativeLabs);preparePanelData(sortedDates,cumulativeLabs);return scope.orderLabAttributesWithinPanel(cumulativeLabs,scope.orderingDetails)}else if(scope.showOrderLabPanel===2){parentArray=scope.groupAttributeByPanelAndKeepUnique(labs,scope.loincClassNames);initProcessPanels(parentArray,monthsExpected,months,cumulativeLabs);preparePanelData(sortedDates,cumulativeLabs);return scope.orderLabAttributesWithinPanel(cumulativeLabs,scope.orderingDetails)}else{scope.groupAttributeByAlphabetically(labs,monthsExpected,cumulativeLabs,months);return cumulativeLabs}};let listener=scope.$watch('cumulativeLabs',(newData,oldData)=>{let leftMenu=$('input[id=selectedLeftMenuParentName]').val();if(leftMenu==='cumulative-labs'){get12MonthCount();scope.patientData=getPatientInfo(scope.patientId.trim())}});scope.$on("$destroy",function(){if(dataLoadingTimer){$timeout.cancel(dataLoadingTimer)}listener()});const renderTile=()=>{scope.isGraph?scope.showGraph():scope.showGrid()};const get12MonthCount=()=>{scope.isLabDataPrepapred=false;renderTile();dataLoadingTimer=$timeout(function(){scope.isLabDataPrepapred=true;scope.isLabGridDataPrepapred=true},300)};scope.showGrid=()=>{scope.isLabGridDataPrepapred=false;scope.isGraph=false;scope.options=prepareLabsForGrid(scope.cumulativeLabs,scope.selMonths,scope.isGraph);if(scope.isFromSearchInsights){scope.highlightCallback()}dataLoadingTimer=$timeout(function(){scope.isLabGridDataPrepapred=true},300)};scope.showGraph=()=>{scope.isLabGraphDataPrepapred=false;scope.isGraph=true;scope.options=PrismaLabTileService.prepareLabsForGraph(scope.cumulativeLabs,scope.selMonths,scope.isGraph,scope.duplicateLabs,scope.isFromSearchInsights);dataLoadingTimer=$timeout(function(){scope.isLabGraphDataPrepapred=true},300);if(scope.isFromSearchInsights){scope.highlightCallback()}};scope.getPrintLabTitle=()=>{return"This will only print lab value trending over time and will not print collection dates, qualifiers and reference ranges."};scope.printCumulativeLabs=()=>{var content=angular.element('.prismaview #cumulative-labs .prisma-cumulative-labs-table-data').html();var monthHeaderDivHtml=angular.element('.prismaview #cumulative-labs #cumulative-lab-print-grid-months').html();let tempDiv=document.createElement('div');tempDiv.innerHTML=content;$(tempDiv).find('#cumulative-lab-print-grid-months').remove();content=tempDiv.innerHTML;var cumulativeLab_title=angular.element('.prismaview #cumulative-labs #ci-cumulative-lab-header').html();var htmlString='<head>';let cssFiles=['/mobiledoc/jsp/webemr/toppanel/prisma/css/prisma-style.css','/mobiledoc/jsp/webemr/toppanel/prisma/css/prisma-style-internal.css'];var style=`  
                    <style>    
                    /* Reset styles */      
                    * {    
                        margin: 0;    
                        padding: 0;    
                        box-sizing: border-box;    
                    }    
                      
                    /* General styles */      
                    body {      
                        font-family: Arial, sans-serif;      
                        margin: 0;      
                        font-size: 10pt; /* Adjust font size */  
                    }    
                      
                    /* Layout Table Styles */    
                    .layout-table {    
                        width: 100%;    
                        border-collapse: collapse;    
                        border: none;    
                        margin: 0;  
                        padding: 0;  
                    }    
                      
                    /* Header and Footer */    
                    .header, .footer {    
                        background-color: #f1f1f1;    
                        color: #000;    
                        padding: 5px;    
                        text-align: center;    
                    }    
                      
                    /* Content Styles */    
                    #content,#monthTableHeader {    
                        margin: 0;    
                        padding: 0;    
                    }    
                      
                    /* Content Table Styles */    
                    #content table, #monthTableHeader table{    
                        width: 100%;    
                        border-collapse: collapse;    
                        border: 1px solid #ddd;    
                        table-layout: fixed; /* Ensure fixed layout */  
                    }    
                      
                    #content th, #content td, #monthTableHeader th, #monthTableHeader td {    
                        border: 1px solid #ddd;    
                        padding: 5px;    
                        text-align: left;    
                        vertical-align: top;    
                        width: 7%; /* Adjust based on number of columns */  
                        word-wrap: break-word; /* Allow text to wrap */  
                    }    
                      
                    #content th, #monthTableHeader th {    
                        background-color: #f2f2f2;    
                        font-weight: bold;    
                    }    
                      
                    /* Adjust page margins and orientation */    
                    @page {    
                        size: landscape; /* Or Letter landscape */  
                        margin: 1cm;
                    }    
                      
                    @page { 
                      @bottom-right{
                        content: counter(page) "/" counter(pages);
                      }
                     }
                    body {    
                        margin: 0;    
                    }    
                      
                    /* External CSS */    
                    ${PrismaAppService.getCSSStyleFromDocumentStyleSheets(cssFiles)}    
                      
                    /* Styles for Printing */    
                    @media print {    
                        body {    
                            margin: 0;    
                            font-family: "Times New Roman", Times, serif;
                        }    
                      
                    .fnt13bold {
                        font-family: "Times New Roman", Times, serif;
                        font-weight: 600 !important;
                      }
                      
                      .red-color {
                    color: #fd333a;
                                }
                      
                         /* Avoid page breaks inside table rows */  
                    tr {  
                        page-break-inside: auto;  
                    }  
                        #content {    
                            margin-top: 15px;    
                            margin-bottom: 1px;    
                        }    
                      
                        .header, .footer, #content {    
                            margin: 0;    
                            padding: 0;    
                        } 
                           
                            .footer  {
                             float: left;
                             margin-top: 1px;
                        }
                       .header {
                        float: left;
                        margin-bottom: 5px;
                       }
          
                        body::after {    
                            content: '';    
                            display: block;    
                            height: 0;    
                            page-break-after: auto;    
                        }    
                    }    
                      
                    </style>    
                    `;htmlString+=style;htmlString+='</head><body>';var bodyContent=`  
                    <table class="layout-table" id="ciLabPrintContent">  
                        <!-- Header -->  
                        <thead>  
                            <tr>  
                                <td>  
                                    <div class="header" >  
                                         <p style="float: left">${PrismaCiSiUtilsService.getPatientIdentifier(scope.patientData)}</p><br><br><br>
                                           <div class="simpleTable" id="monthTableHeader" >
                                            <div class="tablehead labtile-sticky-header" id="cumulative-lab-print-grid-months">
                                                 ${monthHeaderDivHtml}
                                             </div>
                                            </div>  
                                      </div>
                                </td>  
                            </tr>  
                        </thead>  
                        <!-- Content -->  
                        <tbody>  
                            <tr>  
                                <td>  
                                    <div id="printCilabTitle"> <h4>${cumulativeLab_title}</h4>  </div>
                                    <div id="content" style="border-top: black">  
                                        ${content}  
                                    </div>  
                                </td>  
                            </tr>  
                        </tbody>  
                        <!-- Footer (optional) -->  
                       <tfoot>  
                            <tr>  
                                <td>
                                    <div class="footer" style="float: left"><br>This printout shows lab values trending over time and does NOT include individual lab collection dates, qualifiers, or reference ranges.</div>  
                                </td>  
                            </tr>  
                        </tfoot> 
                    </table>  
                 `;htmlString+=bodyContent;htmlString+='</body></html>';openPrintWithoutPreviewDialog(htmlString);let logData={'section':'Clinical Insights','subSection':'Cumulative Lab Results'};PrismaAppService.insertPrismaAuditLog(scope.patientId,global.TrUserId,logData,true).then(function(response){},function(errorMsg){ecwAlert(errorMsg)})}}}}]);