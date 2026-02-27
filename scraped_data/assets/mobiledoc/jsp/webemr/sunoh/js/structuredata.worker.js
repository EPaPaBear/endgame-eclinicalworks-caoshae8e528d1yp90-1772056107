(function(){

    this.onmessage = function(e){
        let reqUrl = e.data.url;
        let reqPayload = e.data.payload;
        var http = new XMLHttpRequest();
        var url = reqUrl;
        var params = reqPayload;
        http.open('POST', url, false);

        //Send the proper header information along with the request
        http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

        http.onreadystatechange = function() {//Call a function when the state changes.
            if(http.readyState == 4 && http.status == 200) {
                let result = this.responseText;
                sendMessage(result);
            }
        }
        http.send(params);
    }

    var sendMessage = function(result){
        this.postMessage({
            responseData: result
        });
    }

})();