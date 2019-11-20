/**
 * BrowseService
 * @namespace feed.browse.services
 */
(function () {
    'use strict';

    angular.module('feed.browse.services')
        .factory('BrowseService', BrowseService);

    BrowseService.$inject = ['$http', '$rootScope'];

    /**
     * @namespace SidebarService
     * @returns {Factory}
     */
    function BrowseService($http, $rootScope) {
        /**
         * @name BrowseService
         * @desc The Factory to be returned
         */
        var BrowseService = {
            getChannel: getChannel,
            getCreateChannelInitData: getCreateChannelInitData,
            getChannelFromTag: getChannelFromTag,
            getNewVideoFromTag: getNewVideoFromTag,
            getGroupVideoFromTag: getGroupVideoFromTag,
            getLatestVideos: getLatestVideos,
            getLatestVideosFromFollowedChannelsByUser: getLatestVideosFromFollowedChannelsByUser,
            getLatestChannels: getLatestChannels,
            getLatestChannelsByUser: getLatestChannelsByUser,
            getHighlightChannels: getHighlightChannels,
            getRandomChannels: getRandomChannels,
            getHighlightVideos: getHighlightVideos,
            getHotTopics: getHotTopics,
            getVideoFromChannel: getVideoFromChannel,
            getVideoFromChannels: getVideoFromChannels,
            getVideoFromFollowedChannels: getVideoFromFollowedChannels,
            getUnwatchSavedVideos: getUnwatchSavedVideos,
            getMostContributers: getMostContributers,
            saveVideo: saveVideo,
            unsaveVideo: unsaveVideo,
            followChannel: followChannel,
            unfollowChannel: unfollowChannel,
            subscribeChannel: subscribeChannel,
            unsubscribeChannel: unsubscribeChannel,
            getPlaylist: getPlaylist,
            likePlaylist: likePlaylist,
            unlikePlaylist: unlikePlaylist,
            searchPlaylist: searchPlaylist,
            searchChannel: searchChannel,
            shareVideoToChannel: shareVideoToChannel,
            updateLastVisitFollowedPage: updateLastVisitFollowedPage
        };

        return BrowseService;

        ////////////////////////////////////

        function getChannel(channel_id) {
            return $http.get("/api/v2/channel/"+channel_id+"/");
        }

        function getCreateChannelInitData() {
            return $http.get("/api/v2/channel/createinitdata/");
        }

        function getChannelFromTag(tag_id, page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/channel/tag/" + tag_id + "/?page=" + page + "&per_page=" + per_page);
        }

        function getNewVideoFromTag(tag_id, page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/playlist/tag/" + tag_id + "/?page=" + page + "&per_page=" + per_page);
        }

        function getGroupVideoFromTag(tag_id, page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/link/tag/" + tag_id + "/?page=" + page + "&per_page=" + per_page);
        }


        function getLatestVideos(page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/playlist/latest_videos/?page=" + page +"&per_page="+per_page);
        }

        function getLatestVideosFromFollowedChannelsByUser(page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/playlist/latest_videos_by_user/?page=" + page +"&per_page="+per_page);
        }

        function getLatestChannels(page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/channel/latest_channels/?page=" + page +"&per_page="+per_page);
        }

        function getLatestChannelsByUser(page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/channel/latest_channels_by_user/?page=" + page +"&per_page="+per_page);
        }

        function getHighlightChannels(page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/channel/highlight/?page=" + page + "&per_page=" + per_page);
        }

        function getRandomChannels(amount) {
            amount = amount || 20;
            return $http.get("/api/v2/channel/random/?amount=" + amount);
        }

        function getHighlightVideos(page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/playlist/highlight/?page=" + page + "&per_page=" + per_page);
        }

        function getHotTopics() {
            return $http.post("/api/v2/hottopic/");
        }

        function getVideoFromChannel(channel_id, page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/channel/"+channel_id+"/playlist/?page=" + page + "&per_page=" + per_page);
        }

        function getVideoFromChannels(channel_ids, page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/playlist/?channel=" + channel_ids.join() + "&page=" + page + "&per_page=" + per_page);
        }

        function getVideoFromFollowedChannels(page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/playlist/followed/?page=" + page + "&per_page=" + per_page);
        }

        function getUnwatchSavedVideos(page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/playlist/saved_unwatched/?page=" + page + "&per_page=" + per_page);
        }

        function getMostContributers(amount) {
            amount = amount || 10;
            return $http.get("/api/v2/account/mostcontributers/?amount=" + amount);
        }

        function saveVideo(playlist_id) {
            return $http.post("/api/v2/playlist/save/"+playlist_id+"/");
        }

        function unsaveVideo(playlist_id) {
            return $http.post("/api/v2/playlist/unsave/"+playlist_id+"/");
        }

        function followChannel(channel_id) {
            return $http.post("/api/v2/channel/follow/"+channel_id+"/")
                    .then( function(result) {
                        $rootScope.follow.push(result.data.channel);
                    });
        }

        function unfollowChannel(channel_id) {
            return $http.post("/api/v2/channel/unfollow/"+channel_id+"/")
                    .then(function(result){
                        for(var index in $rootScope.follow) {
                            if($rootScope.follow[index].id == result.data.channel.id){
                                $rootScope.follow.splice(index,1);
                                break;
                            }
                        }
                    });
        }

        function subscribeChannel(channel_id) {
            return $http.post("/api/v2/channel/subscribe/"+channel_id+"/");
        }

        function unsubscribeChannel(channel_id) {
            return $http.post("/api/v2/channel/unsubscribe/"+channel_id+"/");   
        }

        function getPlaylist(playlist_id) {
            return $http.get("/api/v2/playlist/"+playlist_id+"/");
        }

        function likePlaylist(playlist_id) {
            return $http.post("/api/v2/playlist/like/"+playlist_id+"/");
        }

        function unlikePlaylist(playlist_id) {
            return $http.post("/api/v2/playlist/unlike/"+playlist_id+"/");
        }

        function searchPlaylist(search_text, page, per_page, save_history) {
            page = page || 1;
            per_page = per_page || 20;
            save_history = save_history || true;
            return $http.get("/api/v2/search/?q="+search_text+"&page=" + page + "&per_page=" + per_page + "&save_history=" + save_history);
        }

        function searchChannel(search_text, page, per_page) {
            page = page || 1;
            per_page = per_page || 20;
            return $http.get("/api/v2/search_channel/?q="+search_text+"&page=" + page + "&per_page=" + per_page);
        }

        function shareVideoToChannel(channel_id, playlist_id) {
            return $http.post('/api/v2/channel/'+channel_id+'/playlist/',
            {
                'playlist': playlist_id,
                'detail': ""
            });
        }

        function updateLastVisitFollowedPage() {
            return $http.get("/api/v2/account/update_visit_follow_page/");
        }
    }
})();
