(function(){

    this.onmessage = function(e){
        checkSummaryStatusUrl = e.data.url;
        checkSummaryStatusPayload = e.data.payload;

        if(checkSummaryStatusPayload && checkSummaryStatusPayload.rawData){
            const {rawData, samples, offsetWidth, offsetHeight} = e.data.payload;
            const blockSize = Math.floor(rawData.length / samples);
            const filteredData = [];
            for (let i = 0; i < samples; i++) {
                filteredData.push(rawData[i * blockSize]);
            }

            // draw the line segments
            const drawAudioData = [];
            const width = offsetWidth / filteredData.length;
            for (let i = 0; i < filteredData.length; i++) {
                const x = width * i;
                let height = filteredData[i] * offsetHeight;
                if (height < 0) {
                    height = 0;
                } else if (height > offsetHeight / 2) {
                    height = height > offsetHeight / 2;
                }

                drawAudioData.push({
                    x: x,
                    h: height,
                    w: width,
                    isEven: (i + 1) % 2
                });
            }
            sendMessage(drawAudioData);
        }else{
            var http = new XMLHttpRequest();
            var url = checkSummaryStatusUrl;
            var params = checkSummaryStatusPayload;
            http.open('POST', url, false);

            //Send the proper header information along with the request
            http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

            http.onreadystatechange = function() {//Call a function when the state changes.
                if(http.readyState == 4 && http.status == 200) {
                    var result = JSON.parse(this.responseText);
                    if(url.indexOf('/additional-info') > 0){//need whole response in case of translation
                        sendMessage(result);
                    }else{
                        sendMessage(result.status);
                    }
                }
            }

            http.send(params);
        }
    }

    var sendMessage = function(result){
        this.postMessage({
            responseStatus: result
        });
    }

})();