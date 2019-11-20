/**
 * application configurations
 * @namespace feed.config
 */
(function () {
    'use strict';

    angular
        .module('feed.config')
        .config(config);

    config.$inject = ['$locationProvider', '$analyticsProvider', 'ngToastProvider'];

    /**
     * @name config
     * @desc Define configurations for the application
     */
    function config($locationProvider, $analyticsProvider, ngToast) {

        // Enable HTML5 routing
        // which remove hash tag '#' from url
        $locationProvider.html5Mode(true);
        // when fallback user tag '#!' instead
        $locationProvider.hashPrefix('!');

        $analyticsProvider.withBase(true); // relate to base tag in feed/index.html
        $analyticsProvider.settings.pageTracking.basePath = '/th';

        ngToast.configure({
            animation: 'fade',
            verticalPosition: 'bottom',
            timeout: 3000
        });
    }
})();