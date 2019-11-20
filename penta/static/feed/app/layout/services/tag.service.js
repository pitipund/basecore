/**
 * TagService
 * @namespace feed.layout.services
 */
(function () {
    'use strict';

    angular.module('feed.layout.services')
        .factory('TagService', TagService);

    TagService.$inject = ['$http'];

    /**
     * @namespace TagService
     * @returns {Factory}
     */
    function TagService($http) {
        /**
         * @name TagService
         * @desc The Factory to be returned
         */
        var TagService = {
            getHighlightTags: getHighlightTags,
            getTags: getTags,
            createTag: createTag
        };

        return TagService;

        ////////////////////////////////////

        function getHighlightTags() {
            return $http.get('/api/v2/tag/query/');
        }

        function getTags(word) {
            if (word == undefined) return getHighlightTags();
            return $http.get('/api/v2/tag/query/?q=' + word);
        }

        function createTag(word) {
            return $http.post('/api/v2/tag/add/', {'word': word})
        }
    }
})();
