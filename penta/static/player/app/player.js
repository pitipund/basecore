(function() {
	angular
		.module('player', [
					'feed.layout', 
					'feed.account',
					'feed.browse',
                    'ui.bootstrap',
                    'ngToast',
                    'as.sortable',
                    '720kb.tooltips',
                    'player.config',
                    'angularAwesomeSlider',
		]);

	angular
		.module('player.config', []);

	angular
		.module('player')
		.controller('playerController', playerController);



	playerController.$inject = ['$http', '$location', '$scope', '$rootScope', 'PlayerService', 'AccountService', 
                                'BrowseService', 'ngToast', 'PostService',
                                'CreateChannelModal', 'PostboxModal', 'SuggestionBoxModal', 'EditPostModal'];

	function playerController($http, $location, $scope, $rootScope, PlayerService, AccountService, 
                               BrowseService, ngToast, PostService, CreateChannelModal, PostboxModal,
                               SuggestionBoxModal, EditPostModal){
		$http.defaults.xsrfHeaderName = 'X-CSRFToken';
        $http.defaults.xsrfCookieName = 'csrftoken';
        var myThreshold = 5;
        $scope.seekbarValue = "0;0";
        $scope.setSeekbarValue = "0;0";
        $scope.seekbarOptions = {               
            from: 0,
            to: 600,
            floor: true,
            threshold: myThreshold,
            step: 1,
            // dimension: " km",
            vertical: false,
            css: {
                background: {"background-color": "silver"},
                default: {"background-color": "white"},
                pointer: {"background-color": "red"},
                range: {"background-color": "red"}, 
            },
            modelLabels: function(totalSec) {
                var hours = parseInt( totalSec / 3600 ) % 24;
                var minutes = parseInt( totalSec / 60 ) % 60;
                var seconds = totalSec % 60;
                if(hours==0)
                    return (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds  < 10 ? "0" + seconds : seconds);
                return (hours < 10 ? "0" + hours : hours) + ":" + (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds  < 10 ? "0" + seconds : seconds);
            },
            callback: function(value, elt) {
                //console.log(value);
                var oldVal = $scope.setSeekbarValue.split(";");
                var newVal = value.split(";");
                // console.log("old:"+oldVal[1]+" new:"+newVal[1])
                if(oldVal[1]!=newVal[1]) { // check end time did change or not
                    //seekTo(parseInt(newVal[1]));
                } else if(oldVal[0]!=newVal[0]){
                    seekTo(parseInt(newVal[0]));
                }

                $scope.setSeekbarValue = value;

                function seekTo(time_sec){
                    console.log("seek to "+time_sec)
                    if(vm.playlistItem.link.video_type=="Y") {
                        player.seekTo(time_sec);
                    } else if(vm.playlistItem.link.video_type=="D"){
                        player.seek(time_sec);
                    }
                }
            }               
        };

		var vm = $scope;
		vm.playlistId = null;
		vm.playlistItem = null;
        vm.channelId = null;
        vm.channel = null;
        vm.channelPlaylistItems = [];
        vm.isEditing = false;
        vm.openQuestion = false;
        vm.enable_sort_pattern = false;

        vm.channelArrayContains = channelArrayContains;
        //===player control ===//
        vm.shuffleMode = shuffleMode;
        vm.repeatMode = repeatMode;
        vm.isRepeatOn = false;
        vm.isShuffleOn = false;
        vm.repeatModeText = "off";
        vm.shuffleModeText = "off"; 

        //===page===//
        vm.pagingInfo = null;
        vm.currentPage = -1;
        vm.minPage = vm.currentPage; // minimum means newest so loadNext have to decrease minPage
        vm.maxPage = vm.currentPage; // maximum means oldest so loadPrev have to decrease minPage

        vm.selectedPlaylist = [];
        vm.isSelectedAll = false;

		vm.loadPlaylistItem = loadPlaylistItem;
        vm.loadPrevious = loadPrevious;
        vm.loadNext = loadNext;
        vm.editChannel = editChannel;
        vm.deleteChannel = deleteChannel;
        vm.openPostbox = openPostbox;
        vm.openSuggestionBox = openSuggestionBox;
        vm.followChannel = followChannel;
        vm.shareChannel = shareChannel;
        // vm.dragControlListeners = dragControlListeners; //Declare below
        vm.setPlaylistStartEnd = setPlaylistStartEnd; 
        vm.cancelPlaylistStartEnd = cancelPlaylistStartEnd; 
        vm.deletePlaylist = deletePlaylist;
        vm.editPlaylist = editPlaylist;
        vm.deleteSelected = deleteSelected;
        vm.selectPlaylistChange = selectPlaylistChange;
        vm.selectPlaylist = selectPlaylist;
        vm.deselectPlaylist = deselectPlaylist;
        vm.onSelectAllClick = onSelectAllClick;
        vm.deleteAll = deleteAll;
        vm.inversePlaylistOrder = inversePlaylistOrder;
        vm.sortPlaylistByPattern = sortPlaylistByPattern;
        vm.isOwnChannel = isOwnChannel;

        vm.setStartAtCurrentTime = setStartAtCurrentTime;
        vm.setEndAtCurrentTime = setEndAtCurrentTime;

        vm.perm_group = 1;
        vm.setVideoPermission = setVideoPermission;
        vm.setAllVideosPermission = setAllVideosPermission;

        vm.qMessage = '';
        vm.qMessageList = [];
        vm.questionerList = [];
        vm.listQuestionMessage = listQuestionMessage;
        vm.listQuestionMessageFromOwner = listQuestionMessageFromOwner;
        vm.listQuestioner = listQuestioner;
        vm.currentQuestioner = null;
        vm.sendQuestionMessage = sendQuestionMessage;
        vm.toggleOpenForQuestion = toggleOpenForQuestion;
        vm.addSuggestPlaylistById = addSuggestPlaylistById;
        vm.removeSuggestById = removeSuggestById;

		$rootScope.saveVideo = saveVideo;
		$rootScope.savePlaylistToOwnChannel = savePlaylistToOwnChannel;
		$rootScope.saved_videos = [];
    	$rootScope.own = [];
        $rootScope.follow = [];
        $rootScope.didLogin = true;
 
        initPlayer();
		//====== Account Service =======//
		AccountService
            .getAccountChannels()
            .success(onAccountChannelsSuccess)
            .error(onAccountChannelsFail);

        function onAccountChannelsSuccess(data) {
            $rootScope.didLogin = true;
            $rootScope.saved = data.saved;
            $rootScope.share = data.share;
            $rootScope.own = data.own;
            $rootScope.follow = data.follow;
            $rootScope.saved_videos = [];

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
                console.log("saved_videos");
                console.log($rootScope.saved_videos);
            }

            loadPlaylistItem();
        }

        function onAccountChannelsFail(data) {
            $rootScope.didLogin = false;
            $rootScope.isLoading = false;

            loadPlaylistItem();
        }
        //===== Account Service End ======//

        function listQuestioner() {
            function onSuccess(data){
                vm.questionerList = data.questioner;
                vm.qMessageList = data.message;
            }

            function onFail(data) {
                ngToast.create({
                     className: 'warning',   
                     content: data.detail
                });  
            }    
            PlayerService.listQuestioner(vm.playlistId)
                .success(onSuccess)
                .error(onFail);
        }

        function listQuestionMessageFromOwner(q) {
            vm.currentQuestioner = q;
            listQuestionMessage(q.id);
        }

        function listQuestionMessage(questioner_id) {
            vm.qMessageList = [];

            function onSuccess(data){
                vm.qMessageList = data.message;
            }

            function onFail(data) {
                ngToast.create({
                     className: 'warning',   
                     content: data.detail
                });  
            }    
            
            PlayerService.listQuestionMessage(vm.playlistId, questioner_id)
                .success(onSuccess)
                .error(onFail);
        }

        function sendQuestionMessage(questioner_id) {
            if(vm.qMessage.trim() != '') {
                params = {'msg': vm.qMessage.trim()};
                if(questioner_id)
                    params['questioner'] = questioner_id;

                function onSuccess(data){
                    vm.qMessageList = data.message;
                    vm.qMessage = ''
                }

                function onFail(data) {
                    ngToast.create({
                         className: 'warning',   
                         content: data.detail
                    });    
                }

                PlayerService.sendQuestionMessage(vm.playlistId, params)
                    .success(onSuccess)
                    .error(onFail);
            } else {
                ngToast.create({
                     className: 'warning',   
                     content: 'กรุณาระบุข้อความก่อนส่ง'
                });
            }
        }

        function toggleOpenForQuestion() {
            wantToOpen = !vm.openQuestion;
            msg = "คุณต้องการ \""+(wantToOpen?"เปิด":"ปิด")+"\" รับความคิดเห็นใช่หรือไม่";
            if(confirm(msg)) {
                function onSuccess(data){
                    location.reload();
                }
                function onFail(data) {
                    ngToast.create({
                         className: 'warning',   
                         content: data.detail
                    });  
                }    
                params = { 'want_open': wantToOpen };
                PlayerService.setOpenForQuestion(vm.playlistId, params)
                    .success(onSuccess)
                    .error(onFail);
            }
        }

        function addSuggestPlaylistById(thread_id, playlist_id) {
            function onSuccess(data){
                for(var i=0;i<vm.qMessageList.length;i++) {
                    if(vm.qMessageList[i].id == thread_id) {
                        vm.qMessageList[i].suggest = data;
                        break;
                    }
                }
            }
            function onFail(data) {
                ngToast.create({
                     className: 'warning',   
                     content: data.detail
                });  
            } 
            PlayerService.addSuggestPlaylistById(thread_id, {'playlist_id': playlist_id})
                .success(onSuccess)
                .error(onFail);
        }

        function removeSuggestById(suggest, message, index) {
            if(confirm("คุณต้องการยกเลิกการแนะนำวิดีโอ\n        " + suggest.name + " ใช่หรือไม่")) {
                function onSuccess(data){
                    delete message.suggest[index];
                }
                function onFail(data) {
                    ngToast.create({
                         className: 'warning',   
                         content: data.detail
                    });  
                } 
                PlayerService.removeSuggestById(suggest.id, {})
                    .success(onSuccess)
                    .error(onFail);
            }        
        }

		function loadPlaylistItem() {
            if(!vm.playlistId || vm.playlistId=='') {
                ngToast.create({
                         className: 'warning',   
                         content: 'ไม่วิดีโอใช่แชนแนลนี้เลย'
                });
                loadChannel();
                return;
            }

            // load message
            if(vm.openQuestion) {
                if($rootScope.isAdmin) {
                    listQuestioner()
                } else if(didLogin) {
                    listQuestionMessage();    
                }
            }    

			PlayerService.getPlaylist(vm.playlistId)
				.success(onSuccess)
				.error(onFail);

			function onSuccess(data){
                // console.log("on success");
                // console.log(data);
				vm.playlistItem = data;
                vm.channelId = vm.playlistItem.channel;
                loadChannel();
                vm.seekbarOptions.to =  vm.playlistItem.link.duration_s;
                var startAndStop = "";
                if(vm.playlistItem.play_start_at) {
                    startAndStop = ""+vm.playlistItem.play_start_at+";";
                } else {
                    startAndStop = "0;";
                }
                if(vm.playlistItem.play_end_at) {
                    startAndStop += vm.playlistItem.play_end_at;
                } else {
                    startAndStop += vm.playlistItem.link.duration_s;
                }
                vm.seekbarValue = startAndStop;
			}

			function onFail(data) {
				ngToast.create({
                         className: 'danger',   
                         content: 'ไม่สามารถโหลดวิดีโอนี้ได้'
                });
				// console.log(data)
			}
		}

        function loadChannel() {
            PlayerService.getChannel(vm.channelId)
                .success(onSuccess)
                .error(onFail);

            function onSuccess(data){
                vm.channel = data;
                vm.currentPage = Math.ceil((vm.currentIndex)/25);
                if(vm.currentPage==0)
                    vm.currentPage=1;
                vm.minPage = vm.currentPage;// init first load
                vm.maxPage = vm.currentPage;// init first load
                vm.enable_sort_pattern = data.enable_sort_pattern;
                getChannelPlaylist(vm.currentPage); // init side playlist
            }

            function onFail(data) {
                ngToast.create({
                         className: 'danger',   
                         content: 'ไม่สามารถโหลดช่องนี้ได้'
                });
                // console.log(data)
            }
        }

        function getChannelPlaylist(page) {
            PlayerService.getChannelPlaylist(vm.channel.id, page)
                .success(onSuccess)
                .error(onFail);

            function onSuccess(data){
                // console.log("=====data=====");
                // console.log(data)
                // console.log("=====data=====");
                vm.pagingInfo = data;
                vm.channelPlaylistItems = vm.pagingInfo.playlists;
                
                setTimeout( function() {
                    var container = $('#channelPlaylist'), scrollTo = $('.currentplay');
                    if(container.offset() && scrollTo.offset()) {
                        container.scrollTop(
                            scrollTo.offset().top - container.offset().top + container.scrollTop()
                        );
                    }
                }, 50);
            }

            function onFail(data) {
                ngToast.create({
                         className: 'danger',   
                         content: 'เกิดความผิดพลาด'
                });
                // console.log(data)
            }

        }

        function initPlayer() {
            console.log('initPlayer called');
            var mode = $location.search().mode;
            if(mode=="all" || mode=="one"){
                vm.isRepeatOn = true;
                vm.repeatModeText = mode;
            } else if(mode=="random"){
                vm.isShuffleOn = true;
                vm.shuffleModeText = "on";
            }

        }

        function loadPrevious() {
            vm.minPage -=1;
            PlayerService.getChannelPlaylist(vm.channel.id, vm.minPage)
                .success(onSuccess)
                .error(onFail);

            function onSuccess(result) {
                vm.channelPlaylistItems = result.playlists.concat(vm.channelPlaylistItems)
                vm.isSelectedAll = false;
            }

            function onFail(result){
                ngToast.create({
                    className: 'warning',
                    content: 'เกิดความผิดพลาด ไม่สามารถโหลดข้อมูลได้'
                });
            }
        }

    function loadNext() {        
            vm.maxPage +=1;
            PlayerService.getChannelPlaylist(vm.channel.id, vm.maxPage)
                .success(onSuccess)
                .error(onFail);
            
            function onSuccess(result) {
                vm.channelPlaylistItems = vm.channelPlaylistItems.concat(result.playlists);
                vm.isSelectedAll = false;
            }            

            function onFail(result){
                ngToast.create({
                    className: 'warning',
                    content: 'เกิดความผิดพลาด ไม่สามารถโหลดข้อมูลได้'
                });
            }

        }

        //===== Facility function ======//

        function channelArrayContains(channel_id, channel_array) {
            for (var i=0,l=channel_array.length; i<l; i++) {
                if (channel_array[i].id == channel_id) return channel_array[i];
            }
            return false;
        }

        function setMode(){
            if(vm.isRepeatOn) {
                $location.search('mode',vm.repeatModeText);
            } else if(vm.isShuffleOn) {
                $location.search('mode','random');
            } else {
                $location.search('mode',null);
            }
        }

        function repeatMode() {
            if(vm.isRepeatOn) {
                if(vm.repeatModeText=="all") {
                // all -> one 
                    vm.repeatModeText = "one";
                } else {
                    // one -> off
                    vm.repeatModeText = "off";
                    vm.isRepeatOn = false;
                }
            } else {
                // off -> on
                vm.repeatModeText = "all";
                vm.isRepeatOn = true;
            }

            // clear shuffle button
            vm.isShuffleOn = false;
            vm.shuffleModeText = "off";

            setMode();
        }

        function shuffleMode() {
            if(vm.isShuffleOn) {
                // on -> off
                vm.shuffleModeText = "off";
            } else {
                // off -> off 
                vm.shuffleModeText = "on";
            }
            vm.isShuffleOn = !vm.isShuffleOn;

            // clear repeat button
            vm.isRepeatOn = false;
            vm.repeatModeText = "off";

            setMode();
        }

        function followChannel(isfollowing) {
            var channel_id = vm.channelId;
            if (!$rootScope.didLogin) {
                $("#guestModal").modal();
                return;
            }

            if(isfollowing) {
                BrowseService.unfollowChannel(channel_id)
                    .then( function(result) {
                        vm.subscribed = false;
                    }, function(result) {
                        alert("เกิดความผิดพลาดบางประการ กรุณาลองใหม่ภายหลัง"); 
                    });
            } else {
                BrowseService.followChannel(channel_id)
                    .then( function(result) {
                        vm.subscribed = true;
                    }, function(result) {
                        alert("เกิดความผิดพลาดบางประการ กรุณาลองใหม่ภายหลัง"); 
                    });
            }
        }

        function shareChannel() {
            if (!$rootScope.didLogin) {
                $("#guestModal").modal();
                return;
            }

            // var channel_url = "http://www.pentachannel.com/th/channelplay/"+vm.channelId+"/";
            var image_url = "http://www.pentachannel.com"+vm.real_icon;
            fb_publish(vm.channel.name, vm.channel.detail, document.URL, image_url );
        }

        function editChannel() {
            CreateChannelModal.open(vm.channel.id)
                .then(onModalClose);

            function onModalClose(data) {
                // console.log("on edit finish");
                // vm.title = data.name;
                // vm.detail = data.detail;
                // vm.icon = data.real_icon;
                vm.channel = data;
                vm.enable_sort_pattern = data.enable_sort_pattern;
            }
        }

        function deleteChannel(){
            if(confirm("คุณต้องการลบแชนแนลนี้ใช่หรือไม่?")){
                PostService.deleteChannel(vm.channel.id)
                    .success(onSuccess)
                    .error(onFail);
            }

            function onSuccess() {
                console.log("on delete success finish");
                window.location.href = '/th/own/?mode=channels';
            }

            function onFail(data) {
                console.log("delete channel Failed")
                console.log("data")
            }
        }

        function openPostbox() {
            PostboxModal.open(vm.channel.id, [])
                .then(onSuccess);

            function onSuccess(data) {
                console.log("post success");
                // console.log(data);
                // console.log(vm.maxPage);
                // console.log(vm.pagingInfo.num_page);
                if(vm.minPage==1)
                    vm.channelPlaylistItems = $.merge(vm.channelPlaylistItems, [data]);
            }
        }

        function openSuggestionBox() {
            if (!$scope.didLogin) {
                $("#guestModal").modal();
                return;
            }

            SuggestionBoxModal.open(vm.channel.id)
                .then(onSuccess);

            function onSuccess(data) {
                ngToast.create({
                            className: 'success',
                            content: 'แนะนำวีดีโอไปยังแชนแนลแล้ว'
                        });
            }
        }


		function saveVideo(playlist_id, isSaved) {
            if (!$rootScope.didLogin) {
                $("#guestModal").modal();
                return;
            }

			console.log("save called in player");
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

        vm.dragControlListeners = {
            accept: function (sourceItemHandleScope, destSortableScope) {
                return vm.isEditing; //override to determine drag is allowed or not. default is true.
            },
            itemMoved: function (event) {
                console.log("moved");
            },
            orderChanged: function(event) {
                console.log("orderChanged");
                console.log(event);
                var ordered_id = "";
                for(var index in vm.channelPlaylistItems) {
                    if(ordered_id!="")
                        ordered_id += ",";
                    ordered_id += vm.channelPlaylistItems[index].id;
                }
                console.log(ordered_id);

                PostService.reorderPlaylist(vm.channelId, ordered_id).success(function(){
                    console.log("reordered success")
                });
            }
        };

        function deletePlaylist(index) {
            console.log("====will delete====");
            console.log(vm.channelPlaylistItems[index]);
            console.log("====end will delete====");
            var name = vm.channelPlaylistItems[index].name;
            if(confirm("คุณต้องการลบ \""+name+"\" ใช่หรือไม่?")) {
                PostService.deletePost(vm.channelPlaylistItems[index].id)
                    .success( function(result){
                        ngToast.create({
                         content: '\"'+name+"\" ถูกลบแล้ว"
                        });
                        vm.channelPlaylistItems.splice(index,1);
                    })
                    .error( function(result){
                        console.log(result);
                        ngToast.create({
                         className: 'danger',   
                         content: 'เกิดความผิดพลาด ไม่สามารถลบวิดิโอได้'
                        });
                    });
            }
        }

        function editPlaylist() {
            var playlist = vm.playlistItem;
            console.log(playlist);
            EditPostModal.open(playlist.id)
                .then(onClose);

            function onClose(data) {
                if (data != null) {
                    vm.playlistItem.name = data.name;
                }
            }
        }

        function deleteSelected() {
            if(confirm("คุณต้องการลบ วิดีโอที่เลือกไว้ใช่หรือไม่")) {
                PostService.deletePostInChannel(vm.channelId, vm.selectedPlaylist)
                    .success( function(result){
                        var i, j, m, n;
                        // console.log(result);
                        if(!result) {
                            alert("เกิดความผิดพลาด ไม่สามารถลบวิดิโอได้");
                            return;
                        }

                        // console.log(vm.selectedPlaylist);
                        // console.log(vm.channelPlaylistItems);

                        for(i=0,n=vm.selectedPlaylist.length; i<n; i++){
                            for(j=0,m=vm.channelPlaylistItems.length; j<m; j++){
                                if(vm.channelPlaylistItems[j].id === vm.selectedPlaylist[i]){
                                    vm.channelPlaylistItems.splice(j, 1);
                                    break;
                                }
                            }
                        }
                        vm.selectedPlaylist = [];

                        ngToast.create({
                         content: "วิดีโอถูกลบแล้ว"
                        });
                    })
                    .error( function(result){
                        console.error(result);
                        ngToast.create({
                         className: 'danger',
                         content: 'เกิดความผิดพลาด ไม่สามารถลบวิดิโอได้'
                        });
                    });
            }
        }

        function selectPlaylistChange(event, id){
            // console.log(event.currentTarget.checked);
            // console.log(id);
            if(event.currentTarget.checked){
                selectPlaylist(id);
            } else {
                deselectPlaylist(id);
            }
            // console.log(vm.selectedPlaylist);
        }

        function selectPlaylist(id){
            vm.selectedPlaylist.push(id);
            vm.isSelectedAll = checkSelectedAll();
        }

        function deselectPlaylist(id){
            var i = vm.selectedPlaylist.indexOf(id);
            if (i>=0) {
                vm.selectedPlaylist.splice(i, 1);
            }
            vm.isSelectedAll = checkSelectedAll();
        }

        function checkSelectedAll(){
            if (vm.channelPlaylistItems == undefined) return false;
            return vm.channelPlaylistItems.length === vm.selectedPlaylist.length
        }

        function onSelectAllClick() {
            // console.log(vm.channelPlaylistItems.length);
            // console.log(vm.selectedPlaylist.length);
            if (checkSelectedAll()) {
                deselectAll();
                vm.isSelectedAll = false;
            } else {
                selectAll();
                vm.isSelectedAll = true;
            }
        }

        function selectAll() {
            var i, l;
            $('.playlist-checkbox').prop('checked', true);
            vm.selectedPlaylist = [];
            for(i=0,l=vm.channelPlaylistItems.length; i<l; i++){
                vm.selectedPlaylist.push(vm.channelPlaylistItems[i].id);
            }
        }

        function deselectAll() {
            $('.playlist-checkbox').prop('checked', false);
            vm.selectedPlaylist = [];
        }

        function inversePlaylistOrder(isDescending) {
            if(confirm("คุณต้องการเรียงวิดีโอแบบย้อนกลับใช่ หรือไม่")) {
                PostService.inversePlaylistOrder(vm.channelId)
                    .success( function(result){
                        location.reload();
                    })
                    .error( function(result){
                        ngToast.create({
                            className: 'danger',   
                            content: 'เกิดความผิดพลาด ไม่สามารถเรียงวิดิโอได้'
                        });
                    });
            }
        }

        function sortPlaylistByPattern() {
            if(confirm("คุณต้องการเรียงวิดีโอตามที่ตั้งค่าไว้ใช่ หรือไม่")) {
                PostService.sortPlaylistByPattern(vm.channelId)
                    .success( function(result){
                        location.reload();
                    })
                    .error( function(result){
                        ngToast.create({
                            className: 'danger',
                            content: 'เกิดความผิดพลาด ไม่สามารถเรียงวิดิโอได้'
                        });
                    });
            }
        }

        function deleteAll() {
            if(confirm("คุณต้องการลบ ทุกวิดีโอในแชนแนลนี้ใช่หรือไม่")) {
                PostService.deleteAllInChannel(vm.channelId)                    
                    .success( function(result){
                        console.log(result);
                        if(!result) {
                            alert("เกิดความผิดพลาด ไม่สามารถลบวิดิโอได้");
                            return;
                        }

                        ngToast.create({
                         content: "วิดีโอทั้งหมดถูกลบแล้ว"
                        });
                        vm.channelPlaylistItems = []
                    })
                    .error( function(result){
                        console.log(result);
                        ngToast.create({
                         className: 'danger',   
                         content: 'เกิดความผิดพลาด ไม่สามารถลบวิดิโอได้'
                        });
                    });
            }
        }

        function isOwnChannel() {
            if(!$rootScope.saved || !$rootScope.share)
                return false;
            return vm.channelArrayContains(vm.channelId,$rootScope.own) 
                || vm.channelId==$rootScope.saved.id 
                || vm.channelId==$rootScope.share.id;
        }

        function setVideoPermission(level) {
            var params = {'level': level};
            PlayerService.setVideoPermission(vm.playlistId, params)
                .success(function(){
                    ngToast.create({
                        className: 'success',
                        content: 'บันทึกเรียบร้อยแล้ว'
                    });
                    $scope.accessLevel = level;
                })
                .error(function(){
                    ngToast.create({
                        className: 'warning',
                        content: 'เกิดความผิดพลาด ไม่สามารถบันทึกได้'
                    });
                });
        }

        function setAllVideosPermission(level) {
            if(confirm("คุณต้องเปลี่ยนการเข้าถึงของทุกวิดีโอเป็น '"+ $scope.perm_group_text[level] +"' ใช่หรือไม่")) {
                var params = {'level': level};
                PlayerService.setAllVideosPermission(vm.channelId, params)
                    .success(function(){
                        ngToast.create({
                            className: 'success',
                            content: 'บันทึกเรียบร้อยแล้ว'
                        });
                        $scope.accessLevel = level;
                        vm.perm_group = level;
                    })
                    .error(function(){
                        ngToast.create({
                            className: 'warning',
                            content: 'เกิดความผิดพลาด ไม่สามารถบันทึกได้'
                        });
                    });
            }
        }

        function setPlaylistStartEnd() {
            var tmp = vm.setSeekbarValue.split(';');
            var params = {'start': tmp[0], 'end': tmp[1]};
            PlayerService.setStartEndForPlaylist(vm.playlistId, params)
                .success(function(){
                    ngToast.create({
                        className: 'success',
                        content: 'บันทึกเรียบร้อยแล้ว'
                    });
                })
                .error(function(){
                    ngToast.create({
                        className: 'warning',
                        content: 'เกิดความผิดพลาด ไม่สามารถบันทึกได้'
                    });
                });
        }

        // workaround for bug cannot set endpoint when threshold was apply 
        function restoreThreshold() {
            setTimeout(function() {
                vm.seekbarOptions.threshold = myThreshold;
            }, 100);
        }

        function cancelPlaylistStartEnd() {
            vm.seekbarOptions.threshold = 0;
            vm.seekbarValue = "0;"+vm.playlistItem.link.duration_s;
            vm.setSeekbarValue = vm.seekbarValue;
            restoreThreshold();
            var params = {'cancel': true};
            PlayerService.setStartEndForPlaylist(vm.playlistId, params)
                .success(function(){
                    ngToast.create({
                        className: 'success',
                        content: 'ยกเลิกเรียบร้อยแล้ว'
                    });
                })
                .error(function(){
                    ngToast.create({
                        className: 'warning',
                        content: 'เกิดความผิดพลาด ไม่สามารถยกเลิกได้'
                    });
                });
        }


        function getCurrentTime(){
            if(vm.playlistItem.link.video_type =="Y") {
                return player.getCurrentTime();
            } else if(vm.playlistItem.link.video_type =="D") {
                return player.currentTime;
            } else if(["S", "F"].indexOf(vm.playlistItem.link.video_type) >= 0) {
                return player.currentTime;
            }
        }
        function setStartAtCurrentTime(){
            var new_start = Math.floor(getCurrentTime());
            var end_time = parseInt(vm.seekbarValue.split(";")[1]);

            if(Math.abs(new_start-end_time)<5 || new_start>end_time){
                new_start = end_time-5;
            }
            vm.seekbarValue = new_start+";"+end_time;
            vm.setSeekbarValue = vm.seekbarValue;
        }

        function setEndAtCurrentTime(){
            console.log("==")
            vm.seekbarOptions.threshold = 0;
            var new_end = Math.floor(getCurrentTime());
            var start_time = parseInt(vm.seekbarValue.split(";")[0]);
            if(Math.abs(start_time-new_end)<5 || new_end<start_time){
                new_end = start_time+5;
                if(new_end>vm.playlistItem.link.duration_s)
                    new_end = vm.playlistItem.link.duration_s;
            }
            vm.seekbarValue = start_time+";"+new_end;
            vm.setSeekbarValue = vm.seekbarValue;
            restoreThreshold();
        }

        //===== End Facility function ======//
	}
}());