/**
 * Curator modules declaration
 * @namespace reports.user
 */
(function () {
    'use strict';

    angular.module('reports.user', [
        'reports.user.services',
        'reports.user.controllers'
    ]);

    angular.module('reports.user.services', []);
    angular.module('reports.user.controllers', []);

})();