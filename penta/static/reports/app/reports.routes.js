/**
 * ngRoute configure
 * @namespace reports.routes
 */
(function () {
    'use strict';

    angular
        .module('reports.routes')
        .config(config);

    config.$inject = ['$routeProvider'];

    /**
     * @name config
     * @desc Define valid application routes
     */
    function config($routeProvider) {
        $routeProvider
            .when('/', {redirectTo: '/new_user'})
            .when('/new_user', {
                controller: 'UserReportController',
                controllerAs: 'vm',
                templateUrl: '/static/reports/templates/user/index.html'
            })
            .when('/access', {
                controller: 'ChannelReportController',
                controllerAs: 'vm',
                templateUrl: '/static/reports/templates/channel/index.html'
            })
            .when('/playlist', {
                controller: 'IndexController',
                templateUrl: '/static/reports/templates/layout/under_construction.html'
            })
            .otherwise({redirectTo: '/new_user'});
    }

})();