/**
 * UserReport
 * @namespace reports.user.services
 */
(function () {
    'use strict';

    angular.module('reports.user.services')
        .factory('UserReport', UserReport);

    UserReport.$inject = ['$http'];

    /**
     * @namespace UserReport
     * @returns {Factory}
     */
    function UserReport($http) {
        /**
         * @name UserReport
         * @desc The Factory to be returned
         */
        var UserReport = {
            getTotalUser: getTotalUser,
            getRecentUser: getRecentUser,
            getRegisteredUserWeek: getRegisteredUserWeek,
            getRegisteredUserMonth: getRegisteredUserMonth,
            getRegisteredUserYear: getRegisteredUserYear
        };

        return UserReport;

        ////////////////////////////////////

        function getTotalUser() {
            return $http.get('/curator/admin/reports/api/user_register/total/');
        }

        function getRecentUser() {
            return $http.get('/curator/admin/reports/api/user_register/recently/')
        }

        function getRegisteredUserWeek() {
            return $http.get('/curator/admin/reports/api/user_register/week_count/')
        }

        function getRegisteredUserMonth() {
            return $http.get('/curator/admin/reports/api/user_register/month_count/')
        }

        function getRegisteredUserYear() {
            return $http.get('/curator/admin/reports/api/user_register/year_count/')
        }
    }
})();