/**
 * application modules declaration
 * @namespace reports
 */
(function () {
    'use strict';

    angular
        .module('reports', [
            'reports.config',
            'reports.routes',
            'reports.layout',
            'reports.curator',
            'reports.user',
            'reports.channel'
        ]);

    angular
        .module('reports.config', []);

    angular
        .module('reports.routes', ['ngRoute']);

    angular
        .module('reports')
        .run(run);

    run.$inject = ['$http'];

    /**
     * @name run
     * @desc Action performed when application instantiated
     */
    function run($http) {
        $http.defaults.xsrfHeaderName = 'X-CSRFToken';
        $http.defaults.xsrfCookieName = 'csrftoken';
    }
})();