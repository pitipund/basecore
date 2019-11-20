/**
 * Created by napat on 5/12/15.
 */

(function () {
    'use strict';

    angular.module('reports.curator.services')
        .factory('Curator', Curator);

    Curator.$inject = ['$http'];

    function Curator($http) {
        
        var Curator = {
            getChannelList: getChannelList,
            getPlaylistList: getPlaylistList
        };

        return Curator;

        //////////////////////

        function getChannelList () {
            $http
                .get('/api/v2/channel/')
        }

        function getPlaylistList (channel) {
            channel = channel | null;

        }
    }
})();