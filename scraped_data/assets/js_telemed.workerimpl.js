(function(window){
    'use strict';

    function TelemedWorker(){
        var respStatus = "";

        this.checkSummaryStatus = function(checkSummaryStatusUrl, checkSummaryStatusPayload, workerUrl){
            var worker = createWorker(workerUrl);
            return new Promise(function(resolve, reject){
                worker.postMessage({
                    url : checkSummaryStatusUrl,
                    payload : checkSummaryStatusPayload
                });
                worker.onmessage = function(e){
                    respStatus = e.data.responseStatus;
                    resolve(respStatus);
                };
                worker.onerror = function(err) {
                    reject('There is an error with worker!');
                }
            });
        }
    }

    function TranslationWorker(){
        var response = "";

        this.checkTranslationStatus = function(url, payload, workerUrl){
            var worker = createWorker(workerUrl);
            return new Promise(function(resolve, reject){
                worker.postMessage({
                    url : url,
                    payload : payload
                });
                worker.onmessage = function(e){
                    response = e.data.responseStatus;
                    resolve({
                        status:response.status,
                        transcript:response.transcript,
                        isSecondaryLang:response.isSecondaryLang,
                        translatedContentExist:response.translatedContentExist,
                        secondaryLanguage:response.secondaryLanguage
                    });
                };
                worker.onerror = function(err) {
                    reject('There is an error with worker!');
                }
            });
        }
    }

    function OscillographWorker(){
        var response = "";

        this.drawAudioData = function(payload, workerUrl){
            var worker = createWorker(workerUrl);
            return new Promise(function(resolve, reject){
                worker.postMessage({
                    payload : payload
                });
                worker.onmessage = function(e){
                    response = e.data.responseStatus;
                    resolve({
                        drawAudioData:response
                    });
                };
                worker.onerror = function(err) {
                    reject('There is an error with worker!');
                }
            });
        }
    }

    let telemedWorkerInstance = null;

    function createWorker(workerUrl) {
        if (!telemedWorkerInstance) {
            try {
                telemedWorkerInstance = new Worker(workerUrl);
            } catch (e) {
                console.log(e);
            }
        }
        return telemedWorkerInstance;
    }

    window.telemedWorker = new TelemedWorker();
    window.translationWorker = new TranslationWorker();
    window.oscillographWorker = new OscillographWorker();

})(window);