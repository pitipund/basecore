/**
 * browse modules declaration
 * @namespace feed.browse
 */
(function () {
    'use strict';

    angular.module('feed.browse', [
        'angular-inview',
        'feed.browse.controllers',
        'feed.browse.directives',
        'feed.browse.services'
    ]);

    angular.module('feed.browse.controllers', []);

    angular.module('feed.browse.directives', []);

    angular.module('feed.browse.services', []);
}());