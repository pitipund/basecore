/**
 * SearchViewController
 * @namespace feed.browse.controllers
 */
(function () {
    'use strict';

    angular
        .module('feed.browse.controllers')
        .controller('SearchViewController', SearchViewController);

    SearchViewController.$inject = ['$scope', '$location', '$routeParams', 'BrowseService', 'SidebarService', 'PostService', 'EditPostModal'];

    /**
     * @namespace SearchViewController
     */
    function SearchViewController($scope, $location, $routeParams, BrowseService, SidebarService, PostService, EditPostModal) {
        var vm = this;

        console.log($routeParams);

        // mode must be "channels" or "videos"
        vm.isOwnChannel = false;
        vm.hasNoMode = true;
        vm.searchText = $routeParams.q;
        vm.mode = $routeParams.mode || "videos";
        vm.video_page = 0;
        vm.video_num_page = 1;
        vm.playlists = [];
        vm.channels = [];
        vm.title = "ผลการค้นหา - "+vm.searchText;

        vm.loading = false;
        vm.loadMoreContents = loadMoreVideo;
        vm.likePlaylist = likePlaylist;
        SidebarService.setSelectedIndex(-99);

        vm.editPost = editPost;
        vm.deletePost = deletePost;
        vm.changeMode = changeMode;

        activate();

        ////////////////////////////////////////

        function activate(){
           loadMoreVideo();
        }

        function loadMoreVideo() {
            if(vm.loading) return;
            if(vm.video_page==vm.video_num_page) 
                return;
            console.log('loadMoreVideo called')
            vm.loading = true;

            if(vm.mode == "videos") {
                BrowseService.searchPlaylist(vm.searchText, vm.video_page+1)
                             .success(onSuccess);
                function onSuccess(data) {
                    vm.playlists = $.merge(vm.playlists, data.playlists);
                    vm.video_page = data.page;
                    vm.video_num_page = data.num_page;
                    vm.loading = false;
                }
            } else {
                BrowseService.searchChannel(vm.searchText, vm.video_page+1)
                             .success(function(data) {
                    vm.channels = $.merge(vm.channels, data.channels);
                    vm.video_page = data.page;
                    vm.video_num_page = data.num_page;
                    vm.loading = false;
                 });
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

        function changeMode(mode) {
            $("#searchForm > input[name='mode']").val(mode);
            vm.mode = mode;
            loadMoreVideo();
            $location.search('mode', mode);
        }

    }
})();
