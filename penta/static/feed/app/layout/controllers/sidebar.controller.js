/**
 * SidebarController
 * @namespace feed.layout.controllers
 */
(function () {
    'use strict';

    angular
        .module('feed.layout.controllers')
        .controller('SidebarController', SidebarController);

    SidebarController.$inject = ['$scope', '$location', 'SidebarService'];

    /**
     * @namespace SidebarController
     */
    function SidebarController($scope, $location, SidebarService) {
        var vm = this;

        vm.highlightTags = [];
        vm.suggestionCount = 0;
        vm.sidebarItemIndex = SidebarService.sidebarItemIndex;
        vm.selectedIndex = SidebarService.getSelectedIndex;
        vm.setSelected = SidebarService.setSelected;
        vm.setSelectedIndex = SidebarService.setSelectedIndex;
        vm.suggestionCount = SidebarService.getSuggestionCount;
        vm.countNewFollowedVideos = SidebarService.getCountNewFollowedVideos;

        activate();

        ////////////////////////////////////////

        function activate(){
            setHighlightTags();
            SidebarService.updateCountNewFollowedVideos();
        }

        function setHighlightTags(){
            SidebarService.getHighlightTags()
                .success(onSuccess);

            function onSuccess (data) {
                vm.highlightTags = data;
            }
        }
    }
})();
