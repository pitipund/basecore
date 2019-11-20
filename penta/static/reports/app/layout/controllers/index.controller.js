/**
 * IndexController
 * @namespace reports.layout.controllers
 */
(function () {
    'use strict';

    angular
        .module('reports.layout.controllers')
        .controller('IndexController', IndexController);

    IndexController.$inject = ['$scope', 'Curator'];

    /**
     * @namespace IndexController
     */
    function IndexController($scope, Curator) {
        var vm = this;

    }
})();
