app.service('MessageRoutingService', function () {
    let saveFunction = null;

    return {
        setSaveFunction(fn) {
            saveFunction = fn;
        },
        callSave() {
            if(saveFunction) saveFunction();
        }
    }
})