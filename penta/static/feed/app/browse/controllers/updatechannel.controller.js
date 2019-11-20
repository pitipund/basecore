/**
 * HighlightChannelController
 * @namespace feed.browse.controllers
 */
var X;
(function () {
    'use strict';

    angular
        .module('feed.browse.controllers')
        .controller('UpdateChannelController', UpdateChannelController);

    UpdateChannelController.$inject = ['$scope', '$location', '$routeParams', 'BrowseService', 'SidebarService'];

    /**
     * @namespace UpdateChannelController
     */
    function UpdateChannelController($scope, $location, $routeParams, BrowseService, SidebarService) {
        var vm = this;

        vm.title = "แชนแนลอัพเดท";
        vm.otherChannels = [];

        SidebarService.setSelectedIndex(-4);
        activate();

        ////////////////////////////////////////

        function activate(){
            //if ($scope.follow != []) {
            //    getEveryChannelsNewestVideo();
            //}
            $scope.$watch(
                function(scope){return scope.follow},
                getEveryChannelsNewestVideo);
        }

        function getEveryChannelsNewestVideo() {
            vm.otherChannels = $scope.own.concat($scope.follow);

            vm.otherChannels.sort(compare);

            for (var i = 0, l = vm.otherChannels.length; i < l; i++) {
                BrowseService.getVideoFromChannel(vm.otherChannels[i].id, 1, 4)
                    .success(onSuccess);
            }

            function compare(a, b) {
                var date_a = new Date(a.update_at),
                    date_b = new Date(b.update_at);
                if (date_a > date_b)
                    return -1;
                if (date_a < date_b)
                    return 1;
                return 0;
            }

            function onSuccess(data) {
                for (var _i = 0, _l = vm.otherChannels.length; _i < _l; _i++) {
                    if (vm.otherChannels[_i].id == data.id) {
                        vm.otherChannels[_i] = data;
                        break;
                    }
                }
            }
            X = vm.otherChannels
        }

    }
})();
