/**
 * PostboxModal & PostboxController
 * @namespace feed.layout.modals
 */
(function () {
    'use strict';

    angular.module('feed.layout.modals')
        .factory('PostboxModal', PostboxModal);

    PostboxModal.$inject = ['$modal', 'ngToast'];

    /**
     * @namespace PostboxModal
     * @returns {Factory}
     */
    function PostboxModal($modal) {
        /**
         * @name PostboxService
         * @desc The Factory to be returned
         */
        var PostboxService = {
            open: open
        };

        return PostboxService;

        ////////////////////////////////////

        /**
         *
         * @param channel_id
         * @param tags
         * @returns promise after get result
         */
        function open(channel_id, tags) {
            var modalInstance = $modal.open({
                templateUrl: '/static/feed/templates/layout/modals/postbox.html',
                controller: 'PostboxController',
                controllerAs: 'vm',
                resolve: {
                    channel_id: function () { return channel_id },
                    tags: function () { return tags }
                }
            });

            return modalInstance.result;
        }
    }


    angular
        .module('feed.layout.modals')
        .controller('PostboxController', PostboxController);

    PostboxController.$inject = ['$scope', '$modalInstance', '$cookieStore', 'PostService', 'channel_id', 'tags', 'ngToast'];

    /**
     * @namespace PostboxController
     */
    function PostboxController($scope, $modalInstance, $cookieStore, PostService, channel_id, tags, ngToast) {
        var vm = this;

        vm.channel_id = channel_id;
        vm.channelInit = vm.channel_id!=undefined;
        vm.tags = tags;
        vm.own = [$scope.share];
        vm.own = $.merge(vm.own, $scope.own);
        vm.isSubmitting = false;

        vm.getPayload = getPayload;
        vm.isGettingPayload = false

        vm.alerts = [];
        vm.closeAlert = function(index){vm.alerts.splice(index, 1)};

        vm.postClick = postClick;
        vm.dismiss = function () {$modalInstance.dismiss('cancel')};

        activate();

        ////////////////////////////////////////

        function activate() {
            if (!vm.channelInit) {
                var last_post_channel = $cookieStore.get('last_post_channel'), i, l;
                for (i = 0, l = vm.own.length; i < l; i++) {
                    if (last_post_channel == vm.own[i].id) {
                        vm.channel_id = last_post_channel;
                    }
                }
            }
        }

        function post(channel_id, url, detail, tags) {
            PostService.postVideoToChannel(channel_id, url, detail, tags)
                .success(onSuccess)
                .error(onError);

            function onSuccess(data) {
                $modalInstance.close(data)
                vm.isSubmitting = false;
            }

            function onError(data) {
                vm.isSubmitting = false;
                if ('detail' in data) {
                    var detail = data.detail;
                    if (detail == "needs channel")
                        detail = "กรุณาเลือกแชนแนลที่ต้องการแชร์วีดีโอ";
                    else if (detail == "needs url")
                        detail = "กรุณาใส่ลิงค์ของวีดีโอ";
                    else if (detail == "Type not supported")
                        detail = "ลิงค์ไม่สนับสนุนหรือไม่ถูกต้อง";
                    vm.alerts.push({type: 'danger', msg: detail});
                } else {
                    for(var prop in data){
                        vm.alerts.push({ type: 'danger', msg: prop + ' ' + data[prop] });
                    }
                }
            }
        }

        function postClick(){
            vm.isSubmitting = true;
            console.log("post clicked...");
            if (!vm.channelInit) {
                $cookieStore.put('last_post_channel', vm.channel_id);
            }
            post(vm.channel_id, vm.url, vm.detail, vm.tags);
        }

        function getPayloadEmpty() {
            ngToast.create({
                        content: 'ไม่พบคำบรรยายของวิดีโอจาก url ที่ระบุ'
                    });
            vm.isGettingPayload = false;
        }

        function getPayloadFail() {
            ngToast.create({
                        className: 'danger',   
                        content: 'ไม่สามารถดึงข้อความจากวิดีโอได้ กรุณาตรวจสอบ url'
                    });
            vm.isGettingPayload = false;
        }

        function getPayload(){
            console.log("getPayload called")
            console.log(vm.url)
            vm.isGettingPayload = true;
            PostService.getPayloadFromUrl(vm.url)
                .success(function(data){
                    if(data) {
                        vm.detail = data
                    } else {
                        getPayloadEmpty();
                    }
                    vm.isGettingPayload = false;
                })
                .error(getPayloadFail);   
        }
    }
})();
