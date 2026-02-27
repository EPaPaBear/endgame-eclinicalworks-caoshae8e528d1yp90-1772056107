 var callToSetProblemList = function(row,patientId) {
        var xw =  new XMLWriter();
        startSoapPacket(xw);
        let count = 0;
        angular.forEach(row,function(ItemId){
            var itemid = ItemId.id;//param
            xw.writeStartElement( 'item' );
            xw.writeAttributeString( 'xsi:type', 'xsd:string');

            addElement(xw, 'logtime',moment().format('HH:mm:ss'), 'xsi:type', 'xsd:string');  //log time

            var assmtId = itemid;
            addElement(xw, 'asmtId',assmtId, 'xsi:type', 'xsd:string');

            var icode = ItemId.code;//param
            addElement(xw, 'code',icode, 'xsi:type', 'xsd:string');
            var itype = "";
            if(ItemId.SelType !== undefined){
                itype = ItemId.SelType.option;
            }
            addElement(xw, 'probtype',itype, 'xsi:type', 'xsd:string');

            var iname = ItemId.itemName;//param
            addElement(xw, 'name',"<![CDATA[" + iname+"]]>",'xsi:type', 'xsd:string');

            var ispc = ItemId.specify? ItemId.specify :'';//param
            addElement(xw, 'specify',escapeXml(ispc),'xsi:type', 'xsd:string');

            var onsetdate = ItemId.onset && ItemId.onset!=='null'?ItemId.onset:'';
            addElement(xw, 'onsetdate',onsetdate, 'xsi:type', 'xsd:string');

            var logdate = ItemId.logdate?ItemId.logdate:moment().format('MM/DD/YYYY');//param//  moment().format('MM/DD/YYYY') should we consider current date
            addElement(xw, 'logdate',logdate, 'xsi:type', 'xsd:string');

            var addeddate =  ItemId.AddedDate? ItemId.AddedDate:'';//param
            addElement(xw, 'AddedDate',addeddate,'xsi:type', 'xsd:string');

            var snowMedCode =  ItemId.snowMedCode? ItemId.snowMedCode:'';//param
            addElement(xw, 'snowMedCode',snowMedCode,'xsi:type', 'xsd:string');

            var notes = ItemId.notes?ItemId.notes:'';//param
            addElement(xw, 'notes',escapeXml(notes), 'xsi:type', 'xsd:string');
            var wustatus = "";
            if(ItemId.SelWuStatus !== undefined){
                wustatus = ItemId.SelWuStatus.option;
            }
            addElement(xw, 'WUStatus', wustatus, 'xsi:type', 'xsd:string');
            var condition = "";
            if(ItemId.selected !== undefined && ItemId.selected.option !== undefined){//param
                condition = ItemId.selected.option;
            }
            if(wustatus!='confirmed') condition = "";
            addElement(xw, 'condition',condition, 'xsi:type', 'xsd:string');

            var resolveddate = ItemId.resolvedon?ItemId.resolvedon:'';//param
            addElement(xw, 'resolveddate',resolveddate , 'xsi:type', 'xsd:string');

            var modBy = global.TrUserId;
            addElement(xw, 'modifiedby',modBy, 'xsi:type', 'xsd:string');
            var risk = "";
            if(ItemId.risk !== undefined){//param
                risk = ItemId.risk;
            }
            addElement(xw, 'risk',risk, 'xsi:type', 'xsd:string');

            addElement(xw, 'DisplayOrder', ++count, 'xsi:type', 'xsd:string');
            xw.writeEndElement();  //item tag
        });
        var xml = "";
        endSoapPacket(xw);
        xml = xw.flush();

        var param1 = {ptId: patientId};
        var dbEncId = 0;
        var response = urlPost('/mobiledoc/jsp/dashboard/GetDBEncounterId.jsp', param1);
        if (response != null && response.trim() != '') {
            var x2js = new X2JS();
            var jsonData = x2js.xml_str2json(response.trim());
            dbEncId = jsonData.Envelope.Body.return.data.row.encounterid;
        }

        var param = {FormData: xml , patientId: patientId , encounterId:0 , dbEncId: dbEncId , TrUserId:global.TrUserId};
        var strProblemXMLResponse = urlPost('/mobiledoc/jsp/catalog/xml/setProblemList.jsp',param);
        var x2js = new X2JS();
        var strProblemJsonData = x2js.xml_str2json(strProblemXMLResponse).Envelope.Body.return;
        return strProblemJsonData.status.trim().toUpperCase();
    };
