/**
 * SaveButtonController
 * @namespace feed.layout.controllers
 */
(function () {
    'use strict';

    angular
        .module('feed.layout.controllers')
        .controller('SaveButtonController', SaveButtonController);

    SaveButtonController.$inject = ['$scope', '$rootScope', '$log'];

    /**
     * @namespace SaveButtonController
     */
    function SaveButtonController($scope, $rootScope, $log) {
        var vm = this;

        vm.saved = false;
        vm.disabled = true;
        vm.didLogin = $rootScope.didLogin;
        vm.save = save;
        vm.saveToChannel = saveToChannel;
        vm.channels = $rootScope.own;

        $rootScope.$watch('didLogin', function(){
            activate();    
        }, false);
        
        ////////////////////////////////////////

        function activate(){
            if (!vm.didLogin) {
                vm.disabled = false;
                return;
            }

            $scope.$watch(function($scope){ return $scope.playlist|| $scope.video }, 
                function(){
                    if($scope.playlist) {
                        vm.playlist_id = $scope.playlist.id;
                        vm.link_id = $scope.playlist.link.id;
                        vm.disabled = false;
                    }
                    else if ($scope.video) {
                        vm.playlist_id = $scope.video.description[0].id;
                        vm.link_id = $scope.video.id;
                        vm.disabled = false;
                    }
            })

            $rootScope.$watch(
                function(){ return $rootScope.saved_videos.length || $rootScope.own },
                function(){
                    if($rootScope.saved_videos) 
                        vm.saved = $rootScope.saved_videos.indexOf(vm.link_id)>=0;
                    if($rootScope.own) {
                        vm.channels = $.merge([$rootScope.share],$rootScope.own);
                    }
                }, true );

        }

        function save(){
            if(!vm.didLogin){
                $("#guestModal").modal();
                return;
            }
            $rootScope.saveVideo(vm.playlist_id, vm.saved);
        }

        function saveToChannel(channel) {
            $rootScope.savePlaylistToOwnChannel(channel.id, vm.playlist_id);
        }
    }
})();
