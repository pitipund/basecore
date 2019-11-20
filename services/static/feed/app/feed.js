/**
 * application modules declaration
 * @namespace feed
 */
(function () {
    'use strict';

    angular
        .module('feed', [
            'angulartics',
            'angulartics.google.analytics',
            'ui.bootstrap',
            'ngToast',
            '720kb.tooltips',
            'feed.config',
            'feed.routes',
            'feed.account',
            'feed.layout',
            'feed.browse',
            'angular-jqcloud'
        ]);

    angular
        .module('feed.config', []);

    angular
        .module('feed.routes', ['ngRoute']);

    angular
        .module('feed')
        .run(run);

    run.$inject = ['$http', '$rootScope', '$location', 'AccountService', 'BrowseService', 'ngToast', 'SidebarService'];

    /**
     * @name run
     * @desc Action performed when application instantiated
     */
    function run($http, $rootScope, $location, AccountService, BrowseService, ngToast, SidebarService) {
        $http.defaults.xsrfHeaderName = 'X-CSRFToken';
        $http.defaults.xsrfCookieName = 'csrftoken';

        $rootScope.goTo = goTo;
        $rootScope.saveVideo = saveVideo;
        $rootScope.followChannel = followChannel;
        $rootScope.channelArrayContains = channelArrayContains;
        $rootScope.shareToFacebook = shareToFacebook;
        $rootScope.savePlaylistToOwnChannel = savePlaylistToOwnChannel;
        $rootScope.own = [];
        $rootScope.follow = [];
        $rootScope.didLogin = true;
        $rootScope.isLoading = true;

        $rootScope.updateSuggestionCount = updateSuggestionCount;


        AccountService
            .getAccountChannels()
            .success(onAccountChannelsSuccess)
            .error(onAccountChannelsFail);

        //////////////////////////////////////////////////

        function onAccountChannelsSuccess(data) {
            // console.log("onAccountChannelsSuccess");
            $rootScope.didLogin = true;
            // console.log(data);
            $rootScope.saved = data.saved;
            $rootScope.share = data.share;
            $rootScope.own = data.own;
            $rootScope.follow = data.follow;
            // $rootScope.subscribe = [];
            $rootScope.saved_videos = [];

            // console.log("saved channel");
            // console.log($rootScope.saved);
            // console.log("share channel");
            // console.log($rootScope.share);
            // console.log("own channels");
            // console.log($rootScope.own);
            //count suggestion in all own channels
            updateSuggestionCount();
            // console.log("follow channels");
            // console.log($rootScope.follow);

            

            $rootScope.isLoading = false;

            if (data.admin != undefined) {
                $rootScope.isAdmin = true;
            }

            BrowseService
                .getVideoFromChannel($rootScope.saved.id, 1, 100)
                .success(onGetSaveVideoSuccess);

            function onGetSaveVideoSuccess(data) {
                var playlists = data.playlists,
                    i,len;

                $rootScope.saved_videos = [];
                for (i=0,len=playlists.length; i<len; i++){
                    $rootScope.saved_videos.push(playlists[i].link.id);
                }
                // console.log("saved_videos");
                // console.log($rootScope.saved_videos);
            }
        }

        function updateSuggestionCount(){
            var all_unread_count = 0
            for(var index in $rootScope.own) {
                if($rootScope.own[index].unread_count){
                    all_unread_count += $rootScope.own[index].unread_count;
                }
            }
            SidebarService.setSuggestionCount(all_unread_count);
        }

        function onAccountChannelsFail(data) {
            $rootScope.didLogin = false;
            $rootScope.isLoading = false;
        }

        function goTo(url, query_dict){
            if (query_dict == undefined)
                $location.path(url);
            else
                $location.path(url).search(query_dict);

            if(window.ga) {
                window.ga('send', 'pageview', {
                    'dimension1': lstatus
                });   
            }    
        }

        function channelArrayContains(channel_id, channel_array) {
            for (var i=0,l=channel_array.length; i<l; i++) {
                if (channel_array[i].id == channel_id) return channel_array[i];
            }
            return false;
        }

        function saveVideo(playlist_id, isSaved) {
            if(isSaved) { //to unsave
                BrowseService.unsaveVideo(playlist_id)
                    .success( function(playlist){
                        ngToast.create({
                            className: 'warning',
                            content: 'เลิกเก็บ \"'+playlist.name+'\"'
                        });
                        for(var index in $rootScope.saved_videos) {
                            if($rootScope.saved_videos[index] == playlist.link.id){
                                $rootScope.saved_videos.splice(index,1);
                                break;
                            }
                        }
                    })
                    .error( function(result){
                        ngToast.create({
                         className: 'danger',   
                         content: 'เกิดความผิดพลาด ไม่สามารถแชร์วิดิโอได้'
                        });
                    });
            } else { // to save
                BrowseService.saveVideo(playlist_id)
                    .success( function(playlist) {
                        ngToast.create({
                            content: '\"'+playlist.name+'\" ถูกเก็บเรียบร้อย'
                        });
                        $rootScope.saved_videos.push(playlist.link.id);
                    })
                    .error( function(result) {
                        ngToast.create({
                         className: 'danger',   
                         content: 'เกิดความผิดพลาด ไม่สามารถเก็บวิดิโอได้'
                        });
                    });
            }
        }

        function followChannel(channel_id, isfollowing) {
            if(!$rootScope.didLogin){
                $("#guestModal").modal();
                return;
            }
            if(isfollowing) {
                BrowseService.unfollowChannel(channel_id)
                    .then(function(result){},
                          function(result){ // Failed
                            alert("เกิดความผิดพลาด กรุณาทดลองใหม่ภายหลัง")
                          });
            } else {
                BrowseService.followChannel(channel_id)
                    .then(function(result){},
                          function(result){ // Failed
                            alert("เกิดความผิดพลาด กรุณาทดลองใหม่ภายหลัง")
                          });
            }
        }

        function shareToFacebook(url, title, detail, imgsrc){
            url = window.location.host+url;
            fb_publish(title, detail, url , imgsrc)
        }

        function savePlaylistToOwnChannel(channel_id, playlist_id){
            BrowseService.shareVideoToChannel(channel_id, playlist_id)
                .success( function(playlist){
                    ngToast.create({
                     content: '\"'+playlist.name+'\" ถูกแชร์ไปยัง \"'+playlist.channel_name+'\"แล้ว'
                    });
                })
                .error(function(result){
                    ngToast.create({
                     className: 'danger',   
                     content: 'เกิดความผิดพลาด ไม่สามารถแชร์วิดิโอได้'
                    });
                });
        }

    }
})();