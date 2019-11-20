/**
 * Curator modules declaration
 * @namespace reports.user
 */
(function () {
    'use strict';

    angular.module('reports.channel', [
        'reports.channel.services',
        'reports.channel.controllers'
    ]);

    angular.module('reports.channel.services', []);
    angular.module('reports.channel.controllers', ['chart.js']);

})();
