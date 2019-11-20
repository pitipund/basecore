/**
 * FacebookButtonController
 * @namespace feed.layout.controllers
 */
(function () {
    'use strict';

    angular
        .module('feed.layout.controllers')
        .controller('FacebookButtonController', FacebookButtonController);

    FacebookButtonController.$inject = ['$scope', '$rootScope', '$log'];

    /**
     * @namespace FacebookButtonController
     */
    function FacebookButtonController($scope, $rootScope, $log) {
        var vm = this;

        vm.disabled = true;
        vm.didLogin = $rootScope.didLogin;
        vm.shareToFacebook = shareToFacebook;

        activate();

        ////////////////////////////////////////

        function activate(){
            $scope.$watch( 
                function($scope) { return $scope.playlist|| $scope.video }, 
                function() {
                if($scope.playlist) {
                    vm.title = $scope.playlist.name;
                    vm.detail = $scope.playlist.detail;
                    vm.url = "/th/channelplay/" + $scope.playlist.channel + "/" + $scope.playlist.id + "/";
                    vm.imgsrc = $scope.playlist.link.real_thumbnail;
                    vm.disabled = false;
                }
                else if ($scope.video) {
                    vm.title = $scope.video.name;
                    vm.detail = $scope.video.description[0].detail;
                    vm.url = "/th/channelplay/" + $scope.video.description[0].channel_id + "/"
                             + $scope.video.description[0].id + "/";
                    vm.imgsrc = $scope.video.real_thumbnail;
                    vm.disabled = false;
                }    
            }, true);

            
        }

        //vm.shareToFacebook("/th/channelplay/"+video.description[0].channel_id+"/"+video.description[0].id+"/",
        // video.name,
        // video.description[0].detail,
        // video.real_thumbnail)

        function shareToFacebook(){
            var url = window.location.host + vm.url;
            fb_publish(vm.title, vm.detail, url , vm.imgsrc);
        }
    }
})();

