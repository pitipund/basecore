/**
 * PostService
 * @namespace feed.layout.services
 */
(function () {
    'use strict';

    angular.module('feed.layout.services')
        .factory('PostService', PostService);

    PostService.$inject = ['$http', 'Upload'];

    /**
     * @namespace PostService
     * @returns {Factory}
     */
    function PostService($http, Upload) {
        /**
         * @name PostService
         * @desc The Factory to be returned
         */

        var googleApiKey = "AIzaSyATc0O5KNI5ZQDuq9T2eelREIAl7ZSxzGs";

        var PostService = {
            createChannel: createChannel,
            editChannel: editChannel,
            deleteChannel: deleteChannel,
            postVideoToChannel: postVideoToChannel,
            editPost: editPost,
            deletePost: deletePost,
            deleteAllInChannel: deleteAllInChannel,
            deletePostInChannel: deletePostInChannel,
            reorderPlaylist: reorderPlaylist,
            inversePlaylistOrder: inversePlaylistOrder,
            sortPlaylistByPattern: sortPlaylistByPattern,
            getPayloadFromUrl: getPayloadFromUrl,
            validateYoutubeChannelId: validateYoutubeChannelId,
            validateYoutubePlaylistId: validateYoutubePlaylistId,
            validateYoutubeUserId: validateYoutubeUserId,
        };

        return PostService;

        ////////////////////////////////////

        function createChannel(name, detail, icon, icon_url, tags, enable_auto, auto_params) {
            /*
              'name'     STRING     channel name
              'icon'     IMAGE      icon of channel
              'icon_url' URL        optional url of icon of channel
              'detail'   STRING     detail of channel
              'url_name' STRING     look at /<user id>/channel/create/ and open advance for more detail
              'tags'     [INT, ...] list of id of tags (room id)
              'enable_auto'     BOOLEAN     to indicate that auto system should fetch video from rules
              'rule_include'    STRING      rule for auto system to include these keyword in result
              'rule_exclude'    STRING      rule for auto system to exclude these keyword in result
              'youtube_channel_id_auto'  STRING  auto system search videos in this youtube channel id
              'youtube_playlist_id_auto'  STRING  auto system search videos in this youtube playlist id
             */
            if (icon != undefined) {
                var fields = {};
                if (name != undefined) fields.name = name;
                if (detail != undefined) fields.detail = detail;
                if (icon_url != undefined) fields.icon_url = icon_url;
                if (auto_params.first_video != undefined) fields.first_video = auto_params.first_video;
                if (tags != undefined) fields.tags = tags;
                if (enable_auto) {
                    fields.enable_auto = enable_auto;
                    fields.rule_include = auto_params.rule_include;
                    fields.rule_exclude = auto_params.rule_exclude;
                    fields.youtube_channel_id_auto = auto_params.youtube_channel_id_auto;
                    fields.youtube_playlist_id_auto = auto_params.youtube_playlist_id_auto;
                    fields.youtube_user_id_auto = auto_params.youtube_user_id_auto;
                    fields.instant_add = auto_params.instant_add;
                    fields.latest_first = auto_params.latest_first;
                    fields.publish_before = auto_params.publish_before;
                    fields.publish_after = auto_params.publish_after;
                }
                if (auto_params.permission_group != undefined) {
                    fields.access_level = auto_params.permission_group;
                }
                return Upload.upload({
                    url: '/api/v2/channel/',
                    method: 'POST',
                    fields: fields,
                    sendFieldsAs: 'form',
                    file: icon,
                    fileFormDataName: 'icon'
                });
            } else {
                return $http.post('/api/v2/channel/',
                    {
                        name: name,
                        icon_url: icon_url,
                        detail: detail,
                        tags: tags,
                        enable_auto: enable_auto,
                        rule_include: auto_params.rule_include,
                        rule_exclude: auto_params.rule_exclude,
                        youtube_channel_id_auto: auto_params.youtube_channel_id_auto,
                        youtube_playlist_id_auto: auto_params.youtube_playlist_id_auto,
                        youtube_user_id_auto: auto_params.youtube_user_id_auto,
                        instant_add : auto_params.instant_add,
                        latest_first: auto_params.latest_first,
                        publish_before: auto_params.publish_before,
                        publish_after: auto_params.publish_after,
                        first_video: auto_params.first_video,
                        access_level: auto_params.permission_group,
                        enable_sort_pattern: auto_params.enable_sort_pattern,
                        episode_pattern: auto_params.episode_pattern,
                        use_date_pattern: auto_params.use_date_pattern,
                        video_part_pattern: auto_params.video_part_pattern,
                        auto_sort: auto_params.auto_sort,
                        desc_sort: auto_params.desc_sort
                    });
            }
        }

        function editChannel(channel_id, name, detail, icon, icon_url, tags, removeIcon, enable_auto, auto_params) {
            var fields;
            if (icon != undefined) {
                console.log(tags);
                fields = {};
                if (name != undefined) fields.name = name;
                if (detail != undefined) fields.detail = detail;
                if (icon_url != undefined) fields.icon_url = icon_url;
                //if (tags != undefined) fields.tags = tags;
                fields.tags = tags.length == 0 ? null:tags;
                if (enable_auto) {
                    fields.enable_auto = enable_auto;
                    fields.rule_include = auto_params.rule_include;
                    fields.rule_exclude = auto_params.rule_exclude;
                    fields.youtube_channel_id_auto = auto_params.youtube_channel_id_auto;
                    fields.youtube_playlist_id_auto = auto_params.youtube_playlist_id_auto;
                    fields.youtube_user_id_auto = auto_params.youtube_user_id_auto;
                    fields.instant_add = auto_params.instant_add;
                    fields.latest_first = auto_params.latest_first;
                    fields.publish_before = auto_params.publish_before;
                    fields.publish_after = auto_params.publish_after;
                }
                if (auto_params.permission_group != undefined) fields.access_level = auto_params.permission_group;
                console.log(fields);
                return Upload.upload({
                    url: '/api/v2/channel/' + channel_id + '/',
                    headers: {'Content-Type': 'multipart/form-data' },
                    method: 'POST',
                    fields: fields,
                    sendFieldsAs: 'form',
                    file: icon,
                    fileFormDataName: 'icon'
                });
            } else {
                fields = {
                          name: name,
                          icon_url: icon_url,
                          detail: detail,
                          tags: tags,
                          enable_auto: enable_auto,
                          rule_include: auto_params.rule_include,
                          rule_exclude: auto_params.rule_exclude,
                          youtube_channel_id_auto: auto_params.youtube_channel_id_auto,
                          youtube_playlist_id_auto: auto_params.youtube_playlist_id_auto,
                          youtube_user_id_auto: auto_params.youtube_user_id_auto,
                          instant_add : auto_params.instant_add,
                          latest_first: auto_params.latest_first,
                          publish_after: auto_params.publish_after,
                          publish_before: auto_params.publish_before,
                          access_level: auto_params.permission_group,
                          enable_sort_pattern: auto_params.enable_sort_pattern,
                          episode_pattern: auto_params.episode_pattern,
                          use_date_pattern: auto_params.use_date_pattern,
                          video_part_pattern: auto_params.video_part_pattern,
                          auto_sort: auto_params.auto_sort,
                          desc_sort: auto_params.desc_sort
                      };

                if (removeIcon) {
                    fields['icon'] = null;
                }
                return $http.post('/api/v2/channel/' + channel_id + '/', fields);
            }
        }

        function deleteChannel(channel_id) {
            return $http.delete('/api/v2/channel/'+channel_id+'/');
        }

        function postVideoToChannel(channel_id, url, detail, tags) {
            detail = detail || "";
            tags = tags || [];
            return $http.post('/api/v2/playlist/', {
                channel:channel_id,
                detail: detail,
                url: url,
                tags: tags
            });
        }

        function editPost(playlist_id, params) {
            return $http.post('/api/v2/playlist/' + playlist_id + '/', params);
        }

        function deletePost(playlist_id) {
            return $http.delete('/api/v2/playlist/' + playlist_id + '/');
        }

        function deleteAllInChannel(channel_id) {
            return $http.post('/api/v2/channel/remove_playlist/' + channel_id + '/', { 'all': true });
        }

        function deletePostInChannel(channel_id, playlists) {
            var ids;
            if (typeof(playlists) === 'object') {
                ids = playlists.join(',');
            }
            else {
                ids = playlists;
            }
            return $http.post('/api/v2/channel/remove_playlist/' + channel_id + '/', { 'id': ids});
        }

        function reorderPlaylist(channel_id, ordered_id) {
            return $http.post('/api/v2/channel/reorder_playlist/' + channel_id + '/', { 'ordered_id': ordered_id });
        }

        function inversePlaylistOrder(channel_id) {
            return $http.post('/api/v2/channel/inverseorder_playlist/' + channel_id + '/');   
        }

        function sortPlaylistByPattern(channel_id) {
            return $http.post('/api/v2/channel/pattern_order_playlist/' + channel_id + '/');
        }

        function getPayloadFromUrl(url) {
            var params = {'url': url};
            return $http.post('/api/v2/util/video_description/', params);
        }

        function validateYoutubeChannelId(youtube_channel_id) {
            return $http.get('https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id='+youtube_channel_id+'&key='+googleApiKey);
        }

        function validateYoutubePlaylistId(youtube_playlist_id) {
            return $http.get('https://www.googleapis.com/youtube/v3/playlists?part=id&id='+youtube_playlist_id+'&key='+googleApiKey);
        }
        
        function validateYoutubeUserId(youtube_user_id) {
            return $http.get('https://www.googleapis.com/youtube/v3/channels?part=id&forUsername='+youtube_user_id+'&key='+googleApiKey);
        }
    }
})();
