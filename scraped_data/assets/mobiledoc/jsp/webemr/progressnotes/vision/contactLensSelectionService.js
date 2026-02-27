angular.module('ecw.service.ContactLensSelectionService', []).service('ContactLensSelectionService', function() {
    /**
     * Requestor register check.
     * @type Boolean
     */
    var registerFlag = false;

    /**
     * To use service, Requestor has to register itself and implement below function :
     *      - loadProductData()
     *          Once data has been submitted by service provider, this function will be called for further processing to be handled by Requestor.
     * @type requestor - Requestor object requesting for service to use.
     */
    var requestor = null;

    /**
     * Contact lens product data that is to be shared.
     * @type productData
     */
    var productData = {};

    /**
     * Function to register for service.
     * @param Requestor - Requestor object requesting for service to use.
     */
    var registerRequestor = function(Requestor) {
        registerFlag = true;
        requestor = Requestor;
        productData = {
            productId : 0,
            productName : '',
            isGPLens : '0',
            tint : '',
            BC : '',
            Dia : ''
        };
    };

    /**
     * Clear cache.
     */
    var resetProductData = function() {
        productData = {};
        registerFlag = false;
    };

    /**
     * Notify requestor that Contact Lens selection process has been completed.
     */
    var notifyRequestor = function() {
        if(requestor != null) {
            requestor.loadProductData();
        }
    };

    /**
     * Deregister the requestor and wipe out product data. This will be called by service provider on close.
     */
    var deregisterRequestor = function() {
        requestor = null;
        resetProductData();
    };

    /**
     * Once data have been submitted, This will be called by service provider.
     * @param data - It contains details of selected Contact Lens.
     */
    var saveProductData = function(data) {
        productData.productId = data.productId;
        productData.productName = data.productName;
        productData.isGPLens = data.isGPLens;
        productData.tint = data.tint;
        productData.BC = data.BC;
        productData.Dia = data.Dia;
        notifyRequestor();
    };

    /**
     * Provides Contact Lens data.
     * @returns {productData}
     */
    var getProductData = function() {
        return productData;
    };

    /**
     * @returns {registerFlag}
     */
    var isRegistered = function() {
        return registerFlag;
    };

    return {    // List of available behaviors in service
        registerRequestor   : registerRequestor,
        saveProductData     : saveProductData,
        getProductData      : getProductData,
        deregisterRequestor : deregisterRequestor,
        isRegistered        : isRegistered
    };
});