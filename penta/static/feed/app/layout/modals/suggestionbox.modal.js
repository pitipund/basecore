/**
 * SuggestionBoxService & SuggestionBoxController
 * @namespace feed.layout.modals
 */
(function () {
    'use strict';

    angular.module('feed.layout.modals')
        .factory('SuggestionBoxModal', SuggestionBoxModal);

    SuggestionBoxModal.$inject = ['$modal'];

    /**
     * @namespace SuggestionBoxModal
     * @returns {Factory}
     */
    function SuggestionBoxModal($modal) {
        /**
         * @name SuggestionBoxService
         * @desc The Factory to be returned
         */
        var SuggestionBoxService = {
            open: open
        };

        return SuggestionBoxService;

        ////////////////////////////////////

        /**
         *
         * @param channel_id
         * @returns promise after get result
         */
        function open(channel_id) {
            var modalInstance = $modal.open({
                templateUrl: '/static/feed/templates/layout/modals/suggestionbox.html',
                controller: 'SuggestionBoxController',
                controllerAs: 'vm',
                resolve: {
                    channel_id: function () { return channel_id }
                }
            });

            return modalInstance.result;
        }
    }


    angular
        .module('feed.layout.modals')
        .controller('SuggestionBoxController', SuggestionBoxController);

    SuggestionBoxController.$inject = ['$modalInstance', 'UserSuggestionService', 'channel_id'];

    /**
     * @namespace PostboxController
     */
    function SuggestionBoxController($modalInstance, UserSuggestionService, channel_id) {
        var vm = this;

        vm.channel_id = channel_id;
        vm.channelInit = vm.channel_id!=undefined;
        vm.isSubmitting = false;

        vm.alerts = [];
        vm.closeAlert = function(index){vm.alerts.splice(index, 1)};

        vm.postClick = postClick;
        vm.dismiss = function () {$modalInstance.dismiss('cancel')};

        activate();

        ////////////////////////////////////////

        function activate() {

        }

        function post(channel_id, url, detail) {

            UserSuggestionService.suggestVideoToChannel(channel_id, url, detail)
                .success(onSuccess)
                .error(onError);

            function onSuccess(data) {
                vm.isSubmitting = false;
                $modalInstance.close(data)
            }

            function onError(data) {
                vm.isSubmitting = false;
                if ('detail' in data)
                    vm.alerts.push({ type: 'danger', msg: data.detail });
                else {
                    for(var prop in data){
                        vm.alerts.push({ type: 'danger', msg: prop + ' ' + data[prop] });
                    }
                }
            }
        }

        function postClick(){
            console.log("post clicked...");
            vm.isSubmitting = true;
            post(vm.channel_id, vm.url, vm.detail);
        }
    }
})();
