/**
 * ChannelReport
 * @namespace reports.channel.services
 */
(function () {
    'use strict';

    angular.module('reports.channel.services')
        .factory('ChannelReport', ChannelReport);

    ChannelReport.$inject = ['$http'];

    /**
     * @namespace ChannelReport
     * @returns {Factory}
     */
    function ChannelReport($http) {
        /**
         * @name ChannelReport
         * @desc The Factory to be returned
         */
        var ChannelReport = {
            getUserPerDay: getUserPerDay,
            getChannelPerDay: getChannelPerDay
        };

        return ChannelReport;

        ////////////////////////////////////

        function getUserPerDay() {
            return $http.get('/curator/admin/reports/api/access/user_per_day/');
        }

        function getChannelPerDay() {
            return $http.get('/curator/admin/reports/api/access/channel_per_day/');
        }
    }
})();