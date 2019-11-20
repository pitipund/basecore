/**
 * UserSuggestionService
 * @namespace feed.layout.services
 */
(function () {
    'use strict';

    angular.module('feed.layout.services')
        .factory('UserSuggestionService', UserSuggestionService);

    UserSuggestionService.$inject = ['$http'];

    /**
     * @namespace UserSuggestionService
     * @returns {Factory}
     */
    function UserSuggestionService($http) {
        /**
         * @name UserSuggestionService
         * @desc The Factory to be returned
         */
        var UserSuggestionService = {
            suggestVideoToChannel: suggestVideoToChannel,
            getSuggestVideo: getSuggestVideo,
            getSuggestVideoUnreadCount: getSuggestVideoUnreadCount,
            approveSuggestion: approveSuggestion,
            disapproveSuggestion: disapproveSuggestion
        };

        return UserSuggestionService;

        ////////////////////////////////////

        function suggestVideoToChannel(channel_id,  url, detail) {
            detail = detail || "";
            return $http.post('/api/v2/suggestion/'+channel_id+'/', {
                detail: detail,
                url: url
            });
        }

        function getSuggestVideo(channel_id) {
            if (channel_id==undefined)
                return $http.get('/api/v2/suggestion/');
            return $http.get('/api/v2/suggestion/'+channel_id+'/');
        }

        function getSuggestVideoUnreadCount(channel_id) {
            if (channel_id==undefined)
                return $http.get('/api/v2/suggestion/count_unread/');
            return $http.get('/api/v2/suggestion/count_unread/'+channel_id+'/');
        }

        function approveSuggestion(suggestion_id) {
            return $http.post('/api/v2/suggestion/approve/'+suggestion_id+'/');
        }

        function disapproveSuggestion(suggestion_id) {
            return $http.post('/api/v2/suggestion/disapprove/'+suggestion_id+'/');
        }
    }
})();
