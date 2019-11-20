/**
 * OwnChannelController
 * @namespace feed.browse.controllers
 */
(function () {
    'use strict';

    angular
        .module('feed.browse.controllers')
        .controller('ChannelViewController', ChannelViewController);

    ChannelViewController.$inject = ['$scope', '$routeParams' , '$window', 'BrowseService', 'PostboxModal', 'PostService',
                                     'SuggestionBoxModal', 'UserSuggestionService', 'CreateChannelModal', 'EditPostModal'];

    /**
     * @namespace OwnChannelController
     */
    function ChannelViewController($scope, $routeParams, $window, BrowseService, PostboxModal, PostService,
                                   SuggestionBoxModal, UserSuggestionService, CreateChannelModal, EditPostModal) {
        var vm = this;

        console.log($routeParams);

        vm.channel_id = $routeParams.channel_id;
        vm.channel_name = '';
        if($routeParams.c_name) {
            vm.channel_name = '-'+$routeParams.c_name ;
        }
        vm.video_page = 0;
        vm.video_num_page = 1;
        vm.playlists = [];
        vm.title = "ชื่อแชนแนล";
        vm.suggestions = [];

        vm.loading = true;
        vm.loadMoreContents = loadMoreVideo;

        vm.editChannel = editChannel;
        vm.deleteChannel = deleteChannel;

        vm.followChannel = followChannel;
        vm.subscribeChannel = subscribeChannel;
        vm.likePlaylist = likePlaylist;

        vm.openPostbox = openPostbox;
        vm.openSuggestionBox = openSuggestionBox;
        vm.suggestionApprove = suggestionApprove;
        vm.suggestionDisapprove = suggestionDisapprove;

        vm.editPost = editPost;
        vm.deletePost = deletePost;

        vm.alerts = [];
        vm.closeAlert = function(index) {
            vm.alerts.splice(index, 1);
        };

        activate();

        ////////////////////////////////////////

        function activate(){


            BrowseService.getChannel(vm.channel_id)
                .success( function(data){
                    vm.title = data.name;
                    vm.detail = data.detail;
                    vm.follower = data.follower;
                    vm.icon = data.real_icon;
                    vm.subscribed = data.subscribed;
                    if (vm.channel_id) {
                        loadMoreVideo();
                    }
                });

            $scope.$watch(
                function(scope){return scope.own},
                getSuggestionsList);

            function getSuggestionsList() {
                if ($scope.channelArrayContains(vm.channel_id, $scope.own)) {
                    UserSuggestionService.getSuggestVideo(vm.channel_id)
                        .success(function (data) {
                            console.log('suggestion');
                            console.log(data);
                            vm.suggestions = data;

                            var channel = $scope.channelArrayContains(vm.channel_id, $scope.own);
                            channel.unread_count = 0;
                            $scope.updateSuggestionCount();

                        })
                        .error(function (data) {
                            console.log(data.detail);
                        });
                }
            }
        }

        function loadMoreVideo() {
            console.log("loadmore called");
            if ((vm.loading && vm.video_page>0) || !vm.channel_id || vm.video_page==vm.video_num_page)
                return;
            console.log("begin load");
            vm.loading = true;
            //console.log(vm.channel_id + " " + vm.video_page + " " + vm.video_num_page);
            BrowseService.getVideoFromChannels([vm.channel_id], vm.video_page+1)
                .success(onSuccess);

            function onSuccess(data) {
                $.merge(vm.playlists, data.playlists);
                vm.video_page = data.page;
                vm.video_num_page = data.num_page;
                vm.loading = false;
            }
        }

        function followChannel(channel_id, isfollowing) {
            if (!$scope.didLogin) {
                $("#guestModal").modal();
                return;
            }

            if(isfollowing) {
                BrowseService.unfollowChannel(channel_id)
                    .then( function(result) {
                        vm.subscribed = false;
                    }, function(result) {
                        alert("เกิดความผิดพลาดบางประการ กรุณาลองใหม่ภายหลัง"); 
                    });
            } else {
                BrowseService.followChannel(channel_id)
                    .then( function(result) {
                        vm.subscribed = true;
                    }, function(result) {
                        alert("เกิดความผิดพลาดบางประการ กรุณาลองใหม่ภายหลัง"); 
                    });
            }
        }

        function subscribeChannel(channel_id, isSubscribing){
            if (!$scope.didLogin) {
                $("#guestModal").modal();
                return;
            }
            if(isSubscribing) { // unsubscribe 
                BrowseService.unsubscribeChannel(channel_id)
                    .success( function(result){
                        vm.subscribed = false;
                    })
                    .error( function(result){
                        alert("เกิดความผิดพลาดบางประการ กรุณาลองใหม่ภายหลัง");
                    });
            } else { // subscribe
                BrowseService.subscribeChannel(channel_id)
                    .success( function(result) {
                        vm.subscribed = true;
                    })
                    .error( function(result) {
                        alert("คุณต้อง follow channel ก่อนที่จะ subscribe"); 
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

        function openPostbox() {
            PostboxModal.open(vm.channel_id, [])
                .then(onSuccess);

            function onSuccess(data) {
                vm.playlists = $.merge([data], vm.playlists);
            }
        }

        function openSuggestionBox() {
            if (!$scope.didLogin) {
                $("#guestModal").modal();
                return;
            }

            SuggestionBoxModal.open(vm.channel_id)
                .then(onSuccess);

            function onSuccess(data) {
                vm.alerts.push({type: 'success', msg: 'ขอบคุณ  คุณแนะนำวีดีโอไปยังแชนแนล ' + vm.title + ' แล้ว'});
            }
        }


        function suggestionApprove(index){
            UserSuggestionService.approveSuggestion(vm.suggestions[index].id)
                .success(onSuccess);

            function onSuccess(data) {
                vm.suggestions.splice(index, 1);
                vm.playlists = $.merge([data], vm.playlists);
            }
        }

        function suggestionDisapprove(index){
            UserSuggestionService.disapproveSuggestion(vm.suggestions[index].id)
                .success(onSuccess);

            function onSuccess(data) {
                vm.suggestions.splice(index, 1);
            }
        }

        function editChannel() {
            CreateChannelModal.open(vm.channel_id)
                .then(onModalClose);

            function onModalClose(data) {
                vm.title = data.name;
                vm.detail = data.detail;
                vm.icon = data.real_icon;
            }
        }

        function deleteChannel(){
            if(confirm("คุณต้องการลบแชนแนลนี้ใช่หรือไม่?")){
                PostService.deleteChannel(vm.channel_id)
                    .success(onSuccess);
            }

            function onSuccess() {
                for(var i= 0,l=$scope.own.length; i<l; i++){
                    if($scope.own[i].id == vm.channel_id){
                        $scope.own.splice(i,1);
                        break;
                    }
                }
                $scope.goTo("/own/",{'mode':'channels'});
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
    }
})();
