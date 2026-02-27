(function(){
    function emarOrderOptionsController($modalInstance,emarOptions) {
        var vm=this;
        vm.emarOptions=emarOptions;
        vm.closeModal = function(){
            $modalInstance.dismiss('close');
        }
        vm.placeOrder = function () {
            vm.emarOptions={administeredOrder:0,dispenseOrder:0,placeOrder:1}
            $modalInstance.dismiss(vm.emarOptions);
        };

        vm.administeredOrder = function () {
            vm.emarOptions={administeredOrder:1,dispenseOrder:0,placeOrder:0}
            $modalInstance.dismiss(vm.emarOptions);
        };

        vm.dispenseOrder = function () {
            vm.emarOptions={administeredOrder:0,dispenseOrder:1,placeOrder:0}
            $modalInstance.dismiss(vm.emarOptions);
        };
    }
    angular.module('emarOrderOptions', [])
        .controller('emarOrderOptionsController', ['$modalInstance','emarOptions',emarOrderOptionsController]);
})();