/**
 * SidebarService
 * @namespace feed.layout.services
 */
(function () {
    'use strict';

    angular.module('feed.layout.services')
        .factory('SidebarService', SidebarService);

    SidebarService.$inject = ['$http'];

    /**
     * @namespace SidebarService
     * @returns {Factory}
     */
    function SidebarService($http) {
        /**
         * @name SidebarService
         * @desc The Factory to be returned
         */

        var sidebarItemIndex = { 'suggest' :-1,
                                 'own'     :-2,
                                 'follow'  :-3,
                                 'update'  :-4};
        var selectedIndex = -1;

        var suggestCount = 0;
        var newFollowedVideosCount = 0;

        var SidebarService = {
            sidebarItemIndex: sidebarItemIndex,

            getHighlightTags: getHighlightTags,
            setSelected     : setSelected,
            setSelectedIndex: setSelectedIndex,
            getSelectedIndex: getSelectedIndex,
            setSuggestionCount : setSuggestionCount,
            getSuggestionCount : getSuggestionCount,
            getCountNewFollowedVideos: getCountNewFollowedVideos,
            setCountNewFollowedVideos: setCountNewFollowedVideos,
            updateCountNewFollowedVideos: updateCountNewFollowedVideos
        };

        return SidebarService;

        ////////////////////////////////////

        function getHighlightTags() {
            return $http.get('/api/v2/tag/query/?mode=all');
        }

        function setSelected(string) {
            var index = sidebarItemIndex[string];
            if(index) {
                setSelectedIndex(index);
            }
        }

        function setSelectedIndex(index) {
            selectedIndex = index;
        }

        function getSelectedIndex(){
            return selectedIndex;
        }


        function setSuggestionCount(count) {
            suggestCount = count;
        }
        function getSuggestionCount() {
            return suggestCount;
        }

        function setCountNewFollowedVideos(count) {
            newFollowedVideosCount = count;
        }
        function getCountNewFollowedVideos() {
            return newFollowedVideosCount;
        }
        function updateCountNewFollowedVideos() {
            $http.get('/api/v2/playlist/followed/?no_detail=true&new_only=true').success(function(data) {
                newFollowedVideosCount = data.count;
            })
        }
    }
})();
