/**
 * BrowseController
 * @namespace feed.browse.controllers
 */
(function () {
    'use strict';

    angular
        .module('feed.browse.controllers')
        .controller('BrowseController', BrowseController);

    BrowseController.$inject = ['$scope','$location', '$routeParams', 'BrowseService', 'SidebarService', 'PostboxModal',
                                'EditPostModal','PostService'];

    /**
     * @namespace SidebarController
     */
    function BrowseController($scope, $location, $routeParams, BrowseService, SidebarService, PostboxModal,
                              EditPostModal, PostService) {
        var vm = this;

        console.log($routeParams);
        vm.tag_id = $routeParams.tag_id || 39;
        vm.tag_name = null;

        // mode must be "channels" or "videos"
        vm.mode = $routeParams.mode || "channels";
        vm.video_page = 0;
        vm.channel_page = 0;
        vm.video_num_page = 1;
        vm.channel_num_page = 1;
        vm.channels = [];
        vm.videos = [];

        vm.loading = false;

        vm.changeMode = changeMode;
        vm.loadMoreContents = loadMoreContents;
        vm.followChannel = $scope.followChannel;
        vm.likeDescription = likeDescription;
        vm.openPostbox = openPostbox;
        vm.expandMore = expandMore;

        vm.editPost = editPost;
        vm.deletePost = deletePost;

        vm.deleteChannel = deleteChannel;

        activate();

        ////////////////////////////////////////

        function changeMode(mode) {
            vm.mode = mode;
            //TODO(pB): update route
            if (vm.mode == "videos" && vm.video_page == 0 ||
                    vm.mode == "channels" && vm.channel_page == 0) {
                loadMoreContents();
            }
            $location.search('mode', mode);
        }

        function activate(){
            SidebarService.getHighlightTags()
                .success( function(tags){
                    for(var index in tags){
                        var tag = tags[index];
                        console.log("vm.tag_id: "+vm.tag_id+" tag.id: "+tag.id);
                        if(vm.tag_id==tag.id) {
                            SidebarService.setSelectedIndex(index);
                            break;
                        }
                    }
                    loadMoreContents();
                })
            
        }

        function loadMoreContents() {
            if (vm.mode == "videos") {
                loadMoreVideo();
            } else {
                loadMoreChannel();
            }
        }

        function loadMoreChannel() {
            if (vm.loading || vm.mode == "videos" || vm.channel_page==vm.channel_num_page)
                return;
            vm.loading = true;
            BrowseService.getChannelFromTag(vm.tag_id, vm.channel_page+1)
                .success(onSuccess);

            function onSuccess(data) {
                vm.tag_name = data.tag;
                vm.channels = vm.channels.concat(data.channels);
                vm.channel_page = data.page;
                vm.channel_num_page = data.num_page;
                vm.loading = false;
            }
        }

        function generate_video_description(playlist){
            return {id: playlist.id,
                    channel_id: playlist.channel,
                    channel_name: playlist.channel_name,
                    channel_image: playlist.channel_image,
                    create_at: playlist.create_at,
                    views: playlist.views,
                    likes: playlist.user_like_count,
                    liked: playlist.liked,
                    detail: playlist.detail};
        }

        function loadMoreVideo() {
            if (vm.loading || vm.mode != "videos" || vm.video_page==vm.video_num_page)
                return;
            vm.loading = true;
            BrowseService.getGroupVideoFromTag(vm.tag_id, vm.video_page+1)
                .success(onSuccess);

            function onSuccess(data) {
                vm.tag_name = data.tag;
                $.merge(vm.videos, data.links
                    );
                vm.video_page = data.page;
                vm.video_num_page = data.num_page;
                vm.loading = false;
            }
        }

        function likeDescription(description) {
            if(!$scope.didLogin){
                $("#guestModal").modal();
                return;
            }
            var isLike = description.liked;
            // console.log(description);
            // return;
            if(isLike) {
                BrowseService.unlikePlaylist(description.id)
                .success( function(){
                    description.liked = false;
                    description.likes--;
                })
                .error( function(){
                    // handel error
                });
            } else {
                BrowseService.likePlaylist(description.id)
                .success( function(){
                    description.liked = true;
                    description.likes++;
                })
                .error( function(){
                    // handel error
                });
            }

        }

        function openPostbox () {
            if (!$scope.didLogin) {
                $("#guestModal").modal();
                return;
            }

            PostboxModal.open(null, [vm.tag_id])
                .then(onSuccess);

            function onSuccess(data) {
                var video = data.link;
                video.playlist_id = data.id;
                video.description = [generate_video_description(data)];
                vm.videos = $.merge([video], vm.videos);
            }
        }

        function expandMore(video_index) {
            var insert_index = video_index+1;
            var expands = vm.videos[video_index].extra_links;
            for(var index in expands) {
                var expand_item = expands[index];
                vm.videos.splice(insert_index, 0, expand_item);
                insert_index++;
            }

            vm.videos[video_index].extra_links = [];
        }

        function editPost(video, index) {
            var desc = video.description[index];
            console.log(desc);
            EditPostModal.open(desc.id)
                .then(onClose);

            function onClose(data) {
                if (data == null) {
                    video.description.splice(index, 1);
                    if (video.description.length == 0){
                        vm.videos.splice(vm.videos.indexOf(video), 1);
                    }
                } else {
                    video.name = data.name;
                    desc.detail = data.detail;
                }
            }
        }

        function deletePost(video, description) {
            if(!confirm("คุณต้องการลบใช่หรือไม่")){
                return;
            }

            PostService.deletePost(description.id)
                .success(onSuccess)
                .error(onError);

            function onSuccess(data) {
                var current_descriptions = video.description;
                current_descriptions.splice(current_descriptions.indexOf(description),1);
                if(current_descriptions.length==0) {
                    vm.videos.splice(vm.videos.indexOf(video),1);
                }
            }

            function onError(data){
                alert("เกิดความผิดพลาดบางประการ กรุณาทดลองใหม่ภายหลัง");
            }
        }

        function deleteChannel(channel){
            var check = prompt("ถ้าคุณต้องการลบแชนแนลนี้ \"" + channel.name + "\" โปรดใส่ชื่อแชนแนล");
            if(check == channel.name){
                PostService.deleteChannel(channel.id)
                    .success(onSuccess)
                    .error(onError);
            } else if (check != null){
                alert("ใส่ชื่อแชนแนลไม่ถูกต้อง")
            }

            function onSuccess(data){
                var i,l;
                for (i=0, l=vm.channels.length; i<l; i++){
                    if (vm.channels[i] == channel){
                        vm.channels.splice(i, 1);
                        return;
                    }
                }
            }

            function onError(data){
                console.error(data);
            }
        }
    }
})();
