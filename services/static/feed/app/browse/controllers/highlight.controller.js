/**
 * HighlightChannelController
 * @namespace feed.browse.controllers
 */
(function () {
    'use strict';

    angular
        .module('feed.browse.controllers')
        .controller('HighlightChannelController', HighlightChannelController);

    HighlightChannelController.$inject = ['$scope', '$location', '$routeParams', 'BrowseService'];

    /**
     * @namespace HighlightChannelController
     */
    function HighlightChannelController($scope, $location, $routeParams, BrowseService) {
        var vm = this;

        // console.log($routeParams);

        vm.hotTopics = [{text: '', weight:1}];
        vm.requestedTopics = false;
        vm.latestVideos = [];
        vm.latestVideosFromFollowedChannelsByUser = [];
        vm.latestChannels = [];
        vm.latestChannelsByUser = [];
        vm.unwatchSavedVideos = [];
        vm.highlightChannels = [];
        vm.highlightVideos = [];
        vm.otherChannels = [];
        vm.contributers = [];

        vm.loading = false;

        vm.loadMoreContents = loadMoreVideo;

        activate();

        ////////////////////////////////////////

        function activate(){
            //if ($scope.follow != []) {
            //    getEveryChannelsNewestVideo();
            //}
            getUnwatchSavedVideos();
            getLatestVideos();
            getLatestVideosFromFollowedChannelsByUser();
            getLatestChannels();
            getLatestChannelsByUser();
            getHighlightChannels();
            getHighlightVideos();
            getMostContributers();
            $scope.$watch(
                function(scope){return scope.follow},
                getEveryChannelsNewestVideo);
        }

        function getEveryChannelsNewestVideo() {
            vm.otherChannels = $scope.follow;
            if (!vm.otherChannels) return;

            for (var i = 0, l = vm.otherChannels.length; i < l; i++) {
                BrowseService.getVideoFromChannel(vm.otherChannels[i].id, 1, 4)
                    .success(onSuccess);
            }

            if(!vm.requestedTopics) {
                vm.requestedTopics = true;
                setTimeout(getHotTopics, 500);
            }

            function onSuccess(data) {
                for (var _i = 0, _l = vm.otherChannels.length; _i < _l; _i++) {
                    if (vm.otherChannels[_i].id == data.id) {
                        vm.otherChannels[_i] = data;
                        break;
                    }
                }
            }
        }

        function getLatestVideos() {
            BrowseService.getLatestVideos(1, 8)
                .success(onSuccess);

            function onSuccess(data) {
                vm.latestVideos = data.playlists;
            }
        }

        function getUnwatchSavedVideos() {
            BrowseService.getUnwatchSavedVideos(1, 8)
                .success(onSuccess);

            function onSuccess(data) {
                vm.unwatchSavedVideos = data.playlists;
            }   
        }

        function getLatestVideosFromFollowedChannelsByUser() {
            BrowseService.getLatestVideosFromFollowedChannelsByUser(1, 4)
                .success(onSuccess);

            function onSuccess(data) {
                vm.latestVideosFromFollowedChannelsByUser = data.playlists;
            }
        }

        function getLatestChannels() {
            BrowseService.getLatestChannels(1, 6)
                .success(onSuccess);

            function onSuccess(data) {
                vm.latestChannels = data.channels;
            }
        }

        function getLatestChannelsByUser() {
            BrowseService.getLatestChannelsByUser(1, 6)
                .success(onSuccess);

            function onSuccess(data) {
                vm.latestChannelsByUser = data.channels;
            }
        }

        function getMostContributers() {
            BrowseService.getMostContributers(8)
                .success(onSuccess);

            function onSuccess(data) {
                vm.contributers = data;
            }
        }

        function getHighlightChannels() {
            BrowseService.getRandomChannels(6)
                .success(onSuccess);

            function onSuccess(data) {
                vm.highlightChannels = data.channels;
            }
        }

        function getHighlightVideos() {
            BrowseService.getHighlightVideos(1, 8)
                .success(onSuccess);

            function onSuccess(data) {
                vm.highlightVideos = data.playlists;
            }
        }

        function getHotTopics() {
            BrowseService.getHotTopics()
                .success(onSuccess);

            function onSuccess(data) {
                vm.hotTopics = data;
            }   
        }

        function loadMoreVideo() {
            if (vm.loading || vm.mode != "videos" || vm.video_page==vm.video_num_page)
                return;
            vm.loading = true;
            BrowseService.getVideoFromChannels(vm.channel_ids, vm.video_page+1)
                .success(onSuccess);

            function onSuccess(data) {
                // console.log(data);
                vm.playlists = $.merge(vm.playlists, data.playlists);
                vm.video_page = data.page;
                vm.video_num_page = data.num_page;
                vm.loading = false;
            }
        }

    }
})();
