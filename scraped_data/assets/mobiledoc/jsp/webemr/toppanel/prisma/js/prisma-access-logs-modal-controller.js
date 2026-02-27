(function(){angular.module('prismaAppAccessLog',[]).controller('accessLogModalInstanceCtrl',['$scope','requestParam','$modalInstance','prismaAccessLogService','$sce',function($scope,requestParam,$modalInstance,PrismaAccessLogService,$sce){let logs=this;logs.propertyName='dateTime';logs.reverse=true;logs.patientId=requestParam.patientId||-1;logs.recordCount=0;logs.currentPage=1;logs.recordPerPage=20;let patientData=getPatientInfo($.trim(logs.patientId));logs.sortBy=propertyName=>{logs.reverse=logs.propertyName===propertyName?!logs.reverse:false;logs.propertyName=propertyName;return logs.reverse};logs.cancel=()=>{$modalInstance.dismiss('cancel')};logs.getAccessLog=()=>{PrismaAccessLogService.getAccessLog(logs.patientId,logs.currentPage,logs.recordPerPage).then(response=>{if(response.data&&response.data.result){const records=response.data.result.records||[];records.forEach(record=>{if(record.section&&record.section.toLowerCase()==='prisma_highlights'){record.section='PRISMA Highlights'}});logs.accessLogs=records;logs.recordCount=response.data.result.totalRecords||0;angular.element('.access-log-scroll').scrollTop(0)}},error=>{logs.accessLogs=[];logs.recordCount=0;if(error.data.keyName==="PSAC Settings"&&error.status===403){logs.cancel()}})};logs.printDiv=function(divName){let tableContents=document.getElementById(divName).innerHTML;let patientIdentifierTitle=getPatientIdentifier();let printContents=`
                <br><br>
                <div class="simpleTable" >
                    <table class="table table-bordered">
                        <thead>
                            <tr><th colspan="5" id="prisma-print-page-header">${patientIdentifierTitle}</th></tr>
                            <tr id="prisma-print-table-header">
                                <th class="w25p"><div class="pull-left">Date Time</div></th>
                                <th class="w20p"><div class="pull-left">User Name</div></th>
                                <th class="w10p"><div class="pull-left">Section</div></th>
                                <th class="w15p"><div class="pull-left">Action</div></th>
                                <th><div class="pull-left">Details</div></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tableContents}
                        </tbody>
                    </table>
                </div>
            `;openPrintWithoutPreviewDialog('<style>'+printStyles+'</style>'+printContents.trim());return true};function getPatientIdentifier(){let patientObject={};patientObject.ulname=patientData.lname;patientObject.ufname=patientData.fname;patientObject.uminitial=patientData.mname;patientObject.suffix=patientData.suffix;patientObject.dob=patientData.dob;patientObject.sex=patientData.sex;patientObject.acNo=patientData.ControlNo||"";let patientTitle=getPatientTitle(patientObject,false);return $sce.trustAsHtml(patientTitle)}let printStyles=`
            @media print {
                #prisma-print-page-header {
                    text-align: center;
                    padding: 0px 0px 10px 0px;
                    font-weight: normal;
                    font-size: 16px;
                    color: #394556;
                }
                #prisma-print-table-header {
                    background-color: #c9e5f3 !important;
                    -webkit-print-color-adjust: exact; 
                }
                .simpleTable .table {
                    margin: 10px 0px 0px 0px;
                    table-layout: fixed;
                    border: none !important;
                    border-collapse: collapse;
                    border-spacing: 0;
                }
                .table-bordered > thead > tr:not(:first-child) > th {
                    padding: 15px 10px;
                    color: #394556;
                    opacity: .6;
                    line-height: 16px;
                    height: 27px;
                    font-weight: 600;
                    border: 1px solid #f1f1f1 !important;
                }
                .table-bordered > tbody > tr > td {
                    border: 1px solid #f1f1f1 !important;
                    padding: 5px 10px;
                    color: #394556;
                    vertical-align: middle;
                    white-space: normal!important;
                }
                .w15p{ width:15%;} .w20p{ width:20%;} .w10p{ width:10%;} .pull-left { float: left; } .w25p{ width:25%;}
            }
        `}]).filter('capitalize',function(){return function(input){return!!input?input.charAt(0).toUpperCase()+input.substr(1).toLowerCase():''}})})();