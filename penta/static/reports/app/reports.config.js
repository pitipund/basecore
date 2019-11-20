/**
 * application configurations
 * @namespace reports.config
 */
(function () {
    'use strict';

    angular
        .module('reports.config')
        .config(config);

    config.$inject = ['$locationProvider'];

    /**
     * @name config
     * @desc Define configurations for the application
     */
    function config($locationProvider) {
        // Enable HTML5 routing
        // which remove hash tag '#' from url
        //$locationProvider.html5Mode(true);
        // when fallback user tag '#!' instead
        //$locationProvider.hashPrefix('!');
    }
})();