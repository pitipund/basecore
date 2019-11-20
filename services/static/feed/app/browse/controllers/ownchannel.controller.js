/**
 * OwnChannelController
 * @namespace feed.browse.controllers
 */
(function () {
    'use strict';

    angular
        .module('feed.browse.controllers')
        .controller('OwnChannelController', OwnChannelController);

    OwnChannelController.$inject = ['$scope', '$location', '$routeParams', 'BrowseService', 'SidebarService',
                                    'CreateChannelModal', 'EditPostModal', 'ngToast'];

    /**
     * @namespace OwnChannelController
     */
    function OwnChannelController($scope, $location, $routeParams, BrowseService, SidebarService,
                                  CreateChannelModal, EditPostModal, ngToast) {
        var vm = this;

        console.log($routeParams);

        // mode must be "channels" or "videos"
        vm.needToShowNew = false;
        vm.isOwnChannel = true;
        vm.mode = "channels" //$routeParams.mode || "videos";
        vm.video_page = 0;
        vm.video_num_page = 1;
        vm.channels = [];
        vm.channel_ids = [];
        vm.playlists = [];
        vm.title = "แชนแนลของฉัน";

        vm.loading = false;

        vm.changeMode = changeMode;
        vm.loadMoreContents = loadMoreVideo;
        vm.followChannel = $scope.followChannel;
        vm.likePlaylist = likePlaylist;
        vm.createChannel = createChannel;
        vm.editPost = editPost;
        SidebarService.setSelectedIndex(-2);

        activate();

        ////////////////////////////////////////

        function activate(){
            $scope.$watch(
                function($scope) {return $scope.own||$scope.share},
                function(){
                    if($scope.share == undefined) return;
                    vm.channels = [$scope.share];
                    $.merge(vm.channels, $scope.own);
                    vm.channel_ids = [];
                    if (vm.channels) {
                        for (var i = 0, l = vm.channels.length; i < l; i++) {
                            vm.channel_ids.push(vm.channels[i].id);
                        }
                        loadMoreVideo();
                    }
                }, true);
        }

        function changeMode(mode) {
            vm.mode = mode;
            //TODO(pB): update route
            if (vm.mode == "videos" && vm.video_page == 0) {
                loadMoreVideo();
            }
            $location.search('mode', mode);
        }

        function loadMoreVideo() {
            if (vm.loading || vm.mode != "videos" || vm.video_page==vm.video_num_page || vm.channel_ids.length==0) 
                return;
            vm.loading = true;
            BrowseService.getVideoFromChannels(vm.channel_ids, vm.video_page+1)
                .success(onSuccess);

            function onSuccess(data) {
                console.log(data);
                vm.playlists = $.merge(vm.playlists, data.playlists);
                vm.video_page = data.page;
                vm.video_num_page = data.num_page;
                vm.loading = false;
            }
        }

        function likePlaylist(playlist){
            if(!$scope.didLogin){
                $("#guestModal").modal();
                return;
            }
            var isLike = playlist.liked;
            if(isLike) {
                BrowseService.unlikePlaylist(playlist.id)
                    .success(function(){
                        playlist.liked = false;
                        playlist.user_like_count--;
                    })
                    .error(function(){
                        //handle error
                    });
            } else {
                BrowseService.likePlaylist(playlist.id)
                    .success(function(){
                        playlist.liked = true;
                        playlist.user_like_count++;
                    })
                    .error(function(){
                        //handle error
                    });

            }
        }

        function createChannel(){
            CreateChannelModal.open().then(modalClose, modalDismiss);

            function modalClose(data) {
                $scope.own.splice(0,0,data);
                vm.needToShowNew = true;
                ngToast.create({
                    'timeout': 5000,
                    'content': "ขอบคุณที่สร้างแชนแนล เพื่อแบ่งปันสิ่งดีๆกับชาวเพนต้าทุกคน :)"
                });  
            }

            function modalDismiss() {

            }
        }

        function editPost(index) {
            var playlist = vm.playlists[index];
            EditPostModal.open(playlist.id)
                .then(onClose);

            function onClose(data) {
                if (data == null) {
                    vm.playlists.splice(index, 1);
                } else {
                    playlist.detail = data.detail;
                }
            }
        }
    }
})();
