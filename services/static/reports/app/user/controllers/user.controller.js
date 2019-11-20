/**
 * User report controller
 * @namespace reports.user.controllers
 */
(function () {
    'use strict';

    angular
        .module('reports.user.controllers')
        .controller('UserReportController', UserReportController);

    UserReportController.$inject = ['UserReport','$location'];

    function UserReportController (UserReport, $location) {
        var vm = this;

        vm.totalUser = 0;
        vm.recentUser = [];
        vm.registeredUserWeek = [];
        vm.registeredUserMonth = [];
        vm.registeredUserYear = [];

        activate();

        return vm;

        ////////////////////////////////////

        function activate() {
            UserReport.getTotalUser()
                .success(function(data){
                    vm.totalUser = data['registered']
                });
            UserReport.getRecentUser()
                .success(function(data) {
                    vm.recentUser = data
                });
            UserReport.getRegisteredUserWeek()
                .success(function(data) {
                    vm.registeredUserWeek = data;
                });
            UserReport.getRegisteredUserMonth()
                .success(function(data) {
                    vm.registeredUserMonth = data;
                });
            UserReport.getRegisteredUserYear()
                .success(function(data) {
                    vm.registeredUserYear = data;
                });
        }
    }
})();