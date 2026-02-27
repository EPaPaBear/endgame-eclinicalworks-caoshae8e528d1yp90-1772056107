(()=>{'use strict';angular.module('prisma.clinicalInsights.imagingProcedureTile',['oc.lazyLoad','prismaCiSiUtils']).directive('imagingProcedureTile',imagingProcedureTile);function imagingProcedureTile(){let directive={restrict:'E',transclude:true,scope:{tests:'=',error:'=',patientId:'=',prismaSummary:'=?'},templateUrl:'/mobiledoc/jsp/webemr/toppanel/prisma/template/imagingProcedureTile.html',controller:ImagingProcedureTileController,controllerAs:'vm',bindToController:true};return directive}ImagingProcedureTileController.$inject=['$scope','$ocLazyLoad','$modal','PrismaCiSiUtilsService','$timeout','$sce','PrismaAppService'];function ImagingProcedureTileController($scope,$ocLazyLoad,$modal,PrismaCiSiUtilsService,$timeout,$sce,PrismaAppService){let vm=this;vm.test={};vm.viewMode='box';vm.selectedMonth=12;vm.selectedSource='all';vm.canGoNext=false;vm.canGoPrevious=false;let timer=null;let dataLoadingTimer=null;vm.patientData='';const renderTile=()=>{vm.isDataPrepapred=false;vm.filteredTests=vm.tests;if(vm.prismaSummary){vm.selectedSource='external'}vm.filteredTests.forEach(testLabs=>{testLabs.resultObtainedOn=vm.checkDate(testLabs.resultObtainedOn);testLabs.collectionDate=vm.checkDate(testLabs.collectionDate)});dataLoadingTimer=$timeout(function(){vm.isDataPrepapred=true;vm.patientData=getPatientInfo(vm.patientId.trim())},100)};let listener=$scope.$watch('vm.tests',function(newData,oldData){let leftMenu=$('input[id=selectedLeftMenuParentName]').val();if(leftMenu==='Results'){renderTile()}});vm.checkDate=date=>{return date?.replace('12:00 AM','').trim()};vm.testClicked=test=>{vm.currentTestId=test.id;vm.test=test;if(!test.external){vm.testClosed(test);vm.openInternalLabDIScreen(test);return}vm.isTestActive=true;vm.test.procedureAttributes.forEach(attribute=>{attribute.abnormal=PrismaCiSiUtilsService.checkIfValueIsAbnormal(attribute.resultValue,attribute.lowRangeValue,attribute.highRangeValue);attribute.resultValue=PrismaCiSiUtilsService.stripCdata(attribute.resultValue)});vm.test['seemsLabPanel']=seemsLabPanel(vm.test.procedureAttributes);let currentIndex=vm.filteredTests.findIndex(test=>test.id===vm.currentTestId);vm.canGoPrevious=currentIndex>0;vm.canGoNext=currentIndex<vm.filteredTests.length-1;let elementFullViewSection=angular.element(`.card-fullview-sec-scroll`);if(elementFullViewSection){elementFullViewSection.animate({scrollTop:0},1)}if(vm.viewMode==='box'){timer=$timeout(()=>{let container=angular.element('#imaging-procedure-tile-cls .full-width-section .cardscroll-panel');let testClickedElement=angular.element('#imaging-procedure-tile-cls .full-width-section .cardscroll-panel').find(".prs-img-pro-"+test.id);let top=testClickedElement.eq(0).position().top,currentScroll=container.scrollTop();container.animate({scrollTop:currentScroll+top-40},500)},500)}vm.switchViewMode('box-card')};$scope.$on("$destroy",function(){if(timer){$timeout.cancel(timer)}if(dataLoadingTimer){$timeout.cancel(dataLoadingTimer)}listener()});vm.openInternalLabDIScreen=procedure=>{if(window.screen.availWidth<1366){ecwAlert("This feature is not available in this device. Please use Web version.");return}$ocLazyLoad.load({name:'labreport',files:getDependencies('labreport')}).then(function(){const url=makeURL('/mobiledoc/jsp/webemr/labs/report/LabReport.jsp?ReportId='+procedure.reportId+'&ccDoctorId=0&tabId=0&EncounterId='+procedure.encounterId+'&Type='+procedure.type+'&ProviderId='+procedure.doctorId+'&TrUserId='+global.TrUserId+'&patientId='+vm.patientId+'&rowIndex=0&randomId='+(new Date).getTime()+'&context=CIImagingProcTile');let modalInstance=$modal.open({animation:true,templateUrl:url,size:'sm',windowClass:'prisma-lab-report',backdrop:'static',keyboard:false});modalInstance.result.then(function(response){})})};vm.showPtDocModel=procedure=>{if(window.screen.availWidth<1366){ecwAlert("This feature is not available in this device. Please use Web version.");return}const encId=procedure.encounterId;const ReportId=procedure.reportId;let DocType='lab_doc';const pncatId=0;const itemId=0;if(procedure.type==0){DocType='lab_doc'}else if(procedure.type==1){DocType='XRay_doc'}else if(procedure.type==3){DocType='lab_proc_doc'}$ocLazyLoad.load({name:'ptdocListModule',files:["/mobiledoc/jsp/webemr/toppanel/patientdoclist/patientdocList.js","/mobiledoc/jsp/webemr/templates/savePrompt-tpl.js"]}).then(function(){let url=makeURL("/mobiledoc/jsp/webemr/toppanel/patientdoclist/patientdocList.jsp?patientId="+vm.patientId+"&ReportId="+ReportId+"&DocType="+DocType+"&EncounterId="+encId+"&pncatId="+pncatId+"&pnitemId="+itemId+"&TrUserId="+global.TrUserId+"&callingFrom=PrismaProcedureTile"+"&nd="+(new Date).getTime());let modalInstance=$modal.open({animation:true,templateUrl:url,size:'sm',windowClass:'prisma-proc-grey-clip',backdrop:'static',keyboard:false});modalInstance.result.then(function(response){})})};vm.pinkPaperClipClick=procedure=>{if(window.screen.availWidth<1366){ecwAlert("This feature is not available in this devise. Please use Web version.");return}const nReportId=procedure.reportId;const nType=procedure.type;$ocLazyLoad.load({name:'PinkPaperClip',files:['/mobiledoc/jsp/webemr/labs/pinkpaperclip/js/pinkPaperClip.js']}).then(function(){let url=makeURL('/mobiledoc/jsp/webemr/labs/pinkpaperclip/pinkPaperClipModal.jsp?Src=PrismaProcedureTile&showpatinfo=1&reportId='+nReportId+'&patientId='+vm.patientId+'&TrUserId='+global.TrUserId+'&randomId='+Math.random()+'&labType='+nType);let modalInstance=$modal.open({animation:true,templateUrl:url,size:'sm',windowClass:'prisma-proc-pink-clip',backdrop:'static',keyboard:false});modalInstance.result.then(function(response){})})};vm.isLargeResultValue=resultValue=>{return resultValue?resultValue.length>200:false};vm.testClosed=testClosed=>{vm.isTestActive=false;vm.switchViewMode('box');if(testClosed){timer=$timeout(()=>{let container=angular.element('#imaging-procedure-tile-cls .full-width-section .cardscroll-panel');let testClickedElement=angular.element('#imaging-procedure-tile-cls .full-width-section .cardscroll-panel').find(".prs-img-pro-"+testClosed.id);let top=testClickedElement.eq(0).position().top,currentScroll=container.scrollTop();container.animate({scrollTop:currentScroll+top-40},1)},1)}else{let container=angular.element('#imaging-procedure-tile-cls .full-width-section .cardscroll-panel');if(container){container.animate({scrollTop:0},1)}}};vm.filterByMonthAndSource=(months,source)=>{if(months){vm.selectedMonth=months}if(source){vm.selectedSource=source}let currentDate=new Date;vm.filteredTests=vm.tests.filter(test=>{let testDate=new Date(test.collectionDate);let monthsDifference=Math.floor((currentDate-testDate)/(1e3*60*60*24*30));let filteredBySource=false;if(vm.selectedSource==='all'){filteredBySource=true}else if(vm.selectedSource==='external'){filteredBySource=test.external}else{filteredBySource=!test.external}return monthsDifference<=vm.selectedMonth&&filteredBySource});vm.testClosed(null);vm.test={};vm.currentTestId=-1};vm.switchViewMode=mode=>{vm.viewMode=mode};vm.showRange=attribute=>{return attribute?.stReferenceValue?attribute?.stReferenceValue:attribute?.lowRangeValue+' - '+attribute?.highRangeValue+'  '+attribute?.resultValueUnit};const seemsLabPanel=arr=>{for(let i=0;i<arr.length;i++){const{name,lowRangeValue,highRangeValue,stReferenceValue,resultValueUnit}=arr[i];if(name&&name.trim()!==''||lowRangeValue&&lowRangeValue.trim()!==''||highRangeValue&&highRangeValue.trim()!==''||stReferenceValue!==null&&stReferenceValue!==undefined&&stReferenceValue.trim()!==''||resultValueUnit&&resultValueUnit.trim()!==''){return true}}return false};vm.printCIResultsData=()=>{var content=angular.element('.prismaview #ImagingProcedures .prisma-ci-results-data').html();let tempDiv=document.createElement('div');tempDiv.innerHTML=content;$(tempDiv).find('#printCIResults').remove();content=tempDiv.innerHTML;var htmlString='<head>';let cssFiles=['/mobiledoc/jsp/webemr/toppanel/prisma/css/prisma-style.css','/mobiledoc/jsp/webemr/toppanel/prisma/css/prisma-style-internal.css'];var style=`  
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
                }  
          
                /* Layout Table Styles */  
                .layout-table {  
                    width: 100%;  
                    border-collapse: collapse;  
                    /* No border on the outer layout table */  
                    border: none;  
                }  
          
                /* Header and footer styles */  
                .header, .footer {  
                    background-color: #f1f1f1;  
                    color: #000;  
                    padding: 5px; /* Reduce padding to minimize extra space */  
                    text-align: center;  
                }  
          
                /* Content styles */  
                #content {  
                    margin: 0;  
                    padding: 5px; /* Reduce padding */  
                }  
          
                /* Content Table Styles */  
                /* Apply styles only to tables within the #content div */  
                #content table {  
                    width: 100%;  
                    border-collapse: collapse;  
                    border: 1px solid #ddd;  
                    table-layout: fixed; 
                }  
          
                #content th, #content td {  
                    border: 1px solid #ddd;  
                    padding: 8px;  
                    text-align: left;  
                    vertical-align: top;  
                    word-wrap: break-word;
                }  
          
                #content th {  
                    background-color: #f2f2f2;  
                    font-weight: bold;  
                }  
                
                 #selectedResultValue .results-results-table td {
                          padding: 7px 0px 7px 0px !important;
                    }
                    
                 #selectedResultValue.procedure-panel-data .results-results-table th,
                     #selectedResultValue.procedure-panel-data .results-results-table td{
                        border: none !important;
                        padding: 7px 0px 7px 0px !important;
                  }
                  
                    #selectedResultValue.lab-panel-data .results-results-table th,
                     #selectedResultValue.lab-panel-data .results-results-table td{
                          padding: 7px !important;
                    }
                
                /* Adjust page margins */  
                @page {  
                    size: auto;  
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
                /* Styles for printing */  
                @media print {  
                
                    /* Ensure Bootstrap grid classes apply in print */  
                    .col-sm-6, .col-sm-12 {  
                        float: left;  
                    }  
                      
                    .col-sm-12 {  
                        width: 100%;  
                    }  
                      
                    .col-sm-6 {  
                        width: 50%;  
                    }  
                    .mt10 {
                      margin-top: 10px;
                    } 
                    
                    .pb10 {
                      padding-bottom: 10px;
                    }
                      
                    .col-sm-1, .col-sm-2, .col-sm-3, .col-sm-4, .col-sm-5, .col-sm-6,  
                    .col-sm-7, .col-sm-8, .col-sm-9, .col-sm-10, .col-sm-11, .col-sm-12 {  
                        position: relative;  
                        min-height: 1px;  
                    }  
                    body {  
                        margin: 0;  
                        font-family: "Times New Roman", Times, serif;
                        font-size: 13px;
                    }  
          
                    thead {  
                        display: table-header-group;  
                    }  
          
                    tfoot {  
                        display: table-footer-group;  
                    }  
          
                    /* Avoid page breaks inside table rows */  
                    tr {  
                        page-break-inside: auto;  
                    }  
          
                    /* Handle page breaks in content tables */  
                    #content table {  
                        page-break-inside: auto;  
                    }  
          
                    /* Control orphans and widows */  
                    p, h1, h2, h3, h4, h5, h6 {  
                        orphans: 0;  
                        widows: 0;  
                    }  
          
                      .fnt13bold {
                         font-family: "Times New Roman", Times, serif;
                         font-weight: 800;
                     }
                     
                     .fnt13semibold {
                       font-family: "Times New Roman", Times, serif;
                       font-weight: 600;
                        }
                        
                        .red-color {
                        color: #fd333a;
                        }
                    /* Remove unnecessary margins or paddings in print */  
                    .header, .footer, #content {  
                        margin: 0;  
                        padding: 5px;  
                    }  
                    
                    .header {
                        float: left;
                        margin-bottom: 5px !important;
                    }
                    
                   #selectedResultValue .results-results-table td {
                        padding: 7px 0px 7px 0px !important;
                    }
          
                   #selectedResultValue.procedure-panel-data .results-results-table th,
                    #selectedResultValue.procedure-panel-data .results-results-table td{
                        border: none !important;
                   }
                    
                   #selectedResultValue.lab-panel-data .results-results-table th,
                    #selectedResultValue.lab-panel-data .results-results-table td{
                          padding: 7px !important;
                   }
                
                    /* Prevent empty last page */  
                    body:after {  
                        content: '';  
                        display: block;  
                        height: 0;  
                        page-break-after: auto;  
                    }  
                }  
                
                </style>  
            `;htmlString+=style;htmlString+='</head><body>';var bodyContent=`  
            <table class="layout-table">  
                <!-- Header -->  
                <thead>  
                    <tr>  
                        <td>  
                            <div class="header">  
                               ${PrismaCiSiUtilsService.getPatientIdentifier(vm.patientData)}<br>
                            </div>  
                        </td>  
                    </tr>  
                </thead>  
                <!-- Content -->  
                <tbody>  
                    <tr>  
                        <td>  
                            <div id="content">  
                            <h3 style="float: left">External Results</h3>
                             <br><br>
                                ${content}  
                            </div>  
                        </td>  
                    </tr>  
                </tbody>  
            </table>  
            `;htmlString+=bodyContent;htmlString+='</body></html>';openPrintWithoutPreviewDialog(htmlString);let logData={'section':'Clinical Insights','subSection':'External Result'};PrismaAppService.insertPrismaAuditLog(vm.patientId,global.TrUserId,logData,true).then(function(response){},function(errorMsg){ecwAlert(errorMsg)})}}})();