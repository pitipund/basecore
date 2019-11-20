/**
 * ngRoute configure
 * @namespace feed.routes
 */
(function () {
    'use strict';

    angular
        .module('feed.routes')
        .config(config);

    config.$inject = ['$routeProvider'];

    /**
     * @name config
     * @desc Define valid application routes
     */
    function config($routeProvider) {
        $routeProvider
            .when('/', {
                controller: 'HighlightChannelController',
                controllerAs: 'vm',
                templateUrl: '/static/feed/templates/browse/highlight.html'
            })
            .when('/new/', {
                controller: 'UpdateChannelController',
                controllerAs: 'vm',
                templateUrl: '/static/feed/templates/browse/byupdates.html'
            })
            .when('/browse/:tag_id/:t_name?/', {
                controller: 'BrowseController',
                controllerAs: 'vm',
                templateUrl: '/static/feed/templates/browse/browse.html',
                reloadOnSearch: false
            })
            .when('/follow/', {
                controller: 'FollowChannelController',
                controllerAs: 'vm',
                templateUrl: '/static/feed/templates/browse/bychannel.html'
            })
            .when('/own/', {
                controller: 'OwnChannelController',
                controllerAs: 'vm',
                templateUrl: '/static/feed/templates/browse/bychannel.html'
            })
            .when('/search/', {
                controller: 'SearchViewController',
                controllerAs: 'vm',
                templateUrl: '/static/feed/templates/browse/bychannel.html'
            })
            .when('/channel/:channel_id/:c_name?/', {
                controller: 'ChannelViewController',
                controllerAs: 'vm',
                templateUrl: '/static/feed/templates/browse/channelview.html'
            })
            .otherwise({redirectTo: '/'});
    }

})();