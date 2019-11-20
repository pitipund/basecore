/**
 * Authentication
 * @namespace feed.account.services
 */
(function () {
    'use strict';

    angular.module('feed.account.services')
        .factory('AccountService', AccountService);

    AccountService.$inject = ['$http'];

    /**
     * @namespace AccountService
     * @returns {Factory}
     */
    function AccountService($http) {
        /**
         * @name Authentication
         * @desc The Factory to be returned
         */
        var AccountService = {
            getAccountChannels: getAccountChannels
        };

        return AccountService;

        ///////////////////////

        function getAccountChannels() {
            return $http.get('/api/v2/channel/');
        }
    }

})();