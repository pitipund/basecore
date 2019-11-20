/**
 * editPostModal & EditPostController
 * @namespace feed.layout.modals
 */
(function () {
    'use strict';

    angular.module('feed.layout.modals')
        .factory('EditPostModal', EditPostModal);

    EditPostModal.$inject = ['$modal'];

    /**
     * @namespace EditPostModal
     * @returns {Factory}
     */
    function EditPostModal($modal) {
        /**
         * @name EditPostModal
         * @desc The Factory to be returned
         */
        var EditPostModal = {
            open: open
        };

        return EditPostModal;

        ////////////////////////////////////

        /**
         *
         * @param playlist_id
         * @returns promise after get result
         */
        function open(playlist_id) {
            var modalInstance = $modal.open({
                templateUrl: '/static/feed/templates/layout/modals/editpostmodal.html',
                controller: 'EditPostController',
                controllerAs: 'vm',
                size: 'lg',
                resolve: {
                    playlist_id: function () { return playlist_id }
                }
            });

            return modalInstance.result;
        }
    }


    angular
        .module('feed.layout.modals')
        .controller('EditPostController', EditPostController);

    EditPostController.$inject = ['$log', '$modalInstance', '$cookieStore', 'PostService', 'BrowseService', 'playlist_id'];

    /**
     * @namespace EditPostController
     */
    function EditPostController($log, $modalInstance, $cookieStore, PostService, BrowseService, playlist_id) {
        var vm = this;

        vm.playlist_id = playlist_id;
        vm.name = "";
        vm.detail = "";
        vm.real_thumbnail = "";
        vm.isSubmitting = false;

        vm.alerts = [];
        vm.closeAlert = function(index){vm.alerts.splice(index, 1)};
        vm.dismiss = function () {$modalInstance.dismiss('cancel')};

        vm.deleteClick = deleteClick;
        vm.editClick = editClick;

        activate();

        ////////////////////////////////////////

        function activate() {
            BrowseService.getPlaylist(vm.playlist_id)
                .success(onSuccess)
                .error(onError);

            function onSuccess(data) {
                $log.debug(data);
                vm.name = data.name;
                vm.detail = data.detail;
                vm.real_thumbnail = data.link.real_thumbnail;
            }
        }

        function deleteClick() {
            if (!confirm("คุณแน่ใจว่าจะลบวีดีโอนี้?")){
                return;
            }

            PostService.deletePost(vm.playlist_id)
                .success(onSuccess)
                .error(onError);

            function onSuccess(data) {
                $modalInstance.close(null);
            }
        }

        function editClick() {
            vm.isSubmitting = true;
            PostService.editPost(vm.playlist_id, {
                    name: vm.name,
                    detail: vm.detail
                })
                .success(onSuccess)
                .error(onError);

            function onSuccess(data) {
                vm.isSubmitting = false;
                $modalInstance.close(data);
            }
        }

        function onError(data) {
            vm.isSubmitting = false;
            if ('detail' in data) {
                var detail = data.detail;
                vm.alerts.push({type: 'danger', msg: detail});
            } else {
                for(var prop in data){
                    vm.alerts.push({ type: 'danger', msg: prop + ' ' + data[prop] });
                }
            }
        }
    }
})();
