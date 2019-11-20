/**
 * FollowChannelController
 * @namespace feed.browse.controllers
 */
(function () {
    'use strict';

    angular
        .module('feed.browse.controllers')
        .controller('FollowChannelController', FollowChannelController);

    FollowChannelController.$inject = ['$scope', '$location', '$routeParams', 'BrowseService', 'SidebarService', 'EditPostModal'];

    /**
     * @namespace FollowChannelController
     */
    function FollowChannelController($scope, $location, $routeParams, BrowseService, SidebarService, EditPostModal) {
        var vm = this;

        console.log($routeParams);

        // mode must be "channels" or "videos"
        vm.isOwnChannel = false;
        vm.mode = $routeParams.mode || "videos";
        vm.video_page = 0;
        vm.video_num_page = 1;
        vm.channels = [];
        vm.channel_ids = [];
        vm.playlists = [];
        vm.title = "แชนแนลที่ติดตาม";

        vm.empty = false;
        vm.loading = false;

        vm.changeMode = changeMode;
        vm.loadMoreContents = loadMoreVideo;
        vm.followChannel = $scope.followChannel;
        vm.likePlaylist = likePlaylist;
        vm.editPost = editPost;
        vm.deletePost = deletePost;

        SidebarService.setSelectedIndex(-3);

        activate();

        ////////////////////////////////////////

        function activate(){
            $scope.$watch(
                function(scope){return scope.follow},
                function(){
                    vm.channels = $scope.follow;
                    vm.channel_ids = [];
                    if (vm.channels) {
                        for (var i = 0, l = vm.channels.length; i < l; i++) {
                            vm.channel_ids.push(vm.channels[i].id);
                        }
                        loadMoreVideo();
                    }
                });
            updateLastVisitFollowedPage();
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
            BrowseService.getVideoFromFollowedChannels(vm.video_page+1)
                .success(onSuccess);

            function onSuccess(data) {
                console.log(data);
                vm.playlists = $.merge(vm.playlists, data.playlists);
                vm.video_page = data.page;
                vm.video_num_page = data.num_page;
                vm.loading = false;
                if(vm.playlists.length == 0) {
                    vm.empty = true;
                }
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

        function editPost(index) {
            var playlist = vm.playlists[index];
            EditPostModal.open(playlist.id)
                .then(onClose);

            function onClose(data) {
                if (data == null) {
                    vm.playlists.splice(index, 1);
                } else {
                    playlist.name = data.name;
                    playlist.detail = data.detail;
                }
            }
        }

        function deletePost(playlist) {
            if(!confirm("คุณต้องการลบใช่หรือไม่")){
                return;
            }

            PostService.deletePost(playlist.id)
                .success(onSuccess)
                .error(onError);

            function onSuccess(data) {
                vm.playlists.splice(vm.playlists.indexOf(playlist),1);
            }

            function onError(data){
                alert("เกิดความผิดพลาดบางประการ กรุณาทดลองใหม่ภายหลัง")
            }
        }

        function updateLastVisitFollowedPage() {
            BrowseService.updateLastVisitFollowedPage().success(onSuccess);

            function onSuccess(data) {
                SidebarService.setCountNewFollowedVideos(0);
            }
        }

    }
})();
