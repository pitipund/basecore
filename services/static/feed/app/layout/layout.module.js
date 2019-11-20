/**
 * layout modules declaration
 * @namespace feed.layout
 */
(function () {
    'use strict';

    angular.module('feed.layout', [
        'feed.layout.controllers',
        'feed.layout.directives',
        'feed.layout.modals',
        'feed.layout.services'
    ]);

    angular.module('feed.layout.controllers', []);

    angular.module('feed.layout.directives', []);

    angular.module('feed.layout.modals', ['ngCookies']);

    angular.module('feed.layout.services', ['ngFileUpload']);
})();