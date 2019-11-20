/**
 * CreateChannelModal & CreateChannelController
 * @namespace feed.layout.modals
 */
(function () {
    'use strict';

    angular.module('feed.layout.modals')
        .factory('CreateChannelModal', CreateChannelModal);

    CreateChannelModal.$inject = ['$modal'];

    /**
     * @namespace CreateChannelModal
     * @returns {Factory}
     */
    function CreateChannelModal($modal) {
        /**
         * @name CreateChannelModal
         * @desc The Factory to be returned
         */
        var CreateChannelModal = {
            open: open
        };

        return CreateChannelModal;

        ////////////////////////////////////

        /**
         * @returns promise after get result
         */
        function open(channel_id) {
            var modalInstance;
            if (channel_id == undefined) {
                modalInstance = $modal.open({
                    templateUrl: '/static/feed/templates/layout/modals/createchannelmodal.html',
                    controller: 'CreateChannelController',
                    controllerAs: 'vm',
                    resolve: {
                        channel_id: function () {
                            return null;
                        }
                    }
                });
            } else {
                modalInstance = $modal.open({
                    templateUrl: '/static/feed/templates/layout/modals/createchannelmodal.html',
                    controller: 'CreateChannelController',
                    controllerAs: 'vm',
                    resolve: {
                        channel_id: function () {
                            return channel_id
                        }
                    }
                });
            }

            return modalInstance.result;
        }
    }


    angular
        .module('feed.layout.modals')
        .controller('CreateChannelController', CreateChannelController)
        .directive('datetimepicker', function () {
            return {
                restrict: 'A',
                require : 'ngModel',
                link : function (scope, element, attrs, ngModelCtrl) {
                    element.on('dp.change', function(e) {
                        scope.$apply(function () {
                            ngModelCtrl.$setViewValue(e.date.format('DD/MM/YYYY HH:mm:ss'));
                        });
                    });
                }
            } 
        });

    CreateChannelController.$inject = ['$scope', '$log', '$modalInstance', 'PostService', 'BrowseService', 'channel_id'];

    /**
     * @namespace CreateChannelController
     */
    function CreateChannelController($scope, $log, $modalInstance, PostService, BrowseService, channel_id) {
        var vm = this;

        vm.alerts = [];
        vm.closeAlert = function(index){vm.alerts.splice(index, 1)};
        vm.dismiss = function () {$modalInstance.dismiss('cancel')};

        vm.instant_add = true;
        vm.latest_first = true;
        vm.createClicked = createClicked;
        vm.onChannelIdChange = onChannelIdChange;
        vm.onPlaylistIdChange = onPlaylistIdChange;
        vm.onUserIdChange = onUserIdChange;

        if (channel_id != null){
            vm.env = 'edit';
            vm.mode = 'แก้ไข';
        } else {
            vm.env = 'create';
            vm.mode = 'สร้าง';
        }

        vm.auto_source = "0";
        vm.auto_source_text = { "0": "Youtube Website",
                                "1": "Youtube Channel ID",
                                "2": "Youtube Playlist ID",
                                "3": "Youtube User ID"};

        vm.permission_group = 1;
        vm.permission_group_text = {};

        vm.channelName = null;
        vm.detail = "";
        vm.icon = null;
        vm.icon_url = null;
        vm.first_video = null;
        vm.tags = [];
        vm.isSubmitting = false;

        vm.sorting = {
            enable_sort_pattern: false,
            episode_pattern: '',
            use_date_pattern: false,
            video_part_pattern: '',
            auto_sort: false,
            desc_sort: false
        };

        vm.removeIcon = removeIcon;

        activate();

        ////////////////////////////////////////

        function activate() {
            if (vm.env == 'edit') {
                BrowseService.getChannel(channel_id)
                    .success(onSuccess)
                    .error(onError);
            } else {
                BrowseService.getCreateChannelInitData()
                    .success(function(data) {
                        vm.permission_group_text = data.access_level_choices;
                    })
            }

            function onSuccess(data) {
                $log.debug(data);
                vm.channelName = data.name;
                vm.detail = data.detail;
                vm.icon_url = data.icon_url;
                vm.current_icon = data.icon;
                vm.tags = data.tags;
                vm.enable_auto = data.enable_auto;
                vm.permission_group = data.access_level;
                vm.permission_group_text = data.access_level_choices;
                if(data.rule_include)
                    vm.rule_include = {'text': data.rule_include};
                if(data.rule_exclude)
                    vm.rule_exclude = {'text': data.rule_exclude};
                if(data.publish_after)
                    vm.publish_after = moment.utc(data.publish_after, 'DD/MM/YYYY HH:mm:ss').local().format('DD/MM/YYYY HH:mm:ss');
                if(data.publish_before)
                    vm.publish_before = moment.utc(data.publish_before, 'DD/MM/YYYY HH:mm:ss').local().format('DD/MM/YYYY HH:mm:ss');
                if(data.youtube_channel_id_auto) {
                    vm.youtube_channel_id_auto = {'text': data.youtube_channel_id_auto, valid: true};
                    vm.auto_source = 1;
                }
                if(data.youtube_playlist_id_auto) {
                    vm.youtube_playlist_id_auto = {'text': data.youtube_playlist_id_auto, valid: true};
                    vm.auto_source = 2;
                }
                if(data.youtube_user_id_auto) {
                    vm.youtube_user_id_auto = {'text': data.youtube_user_id_auto, valid: true};
                    vm.auto_source = 3;
                }
                if(data.latest_first) {
                    vm.latest_first = data.latest_first;
                } else if(data.latest_first!=undefined) {
                    vm.latest_first = false;
                }
                if(data.instant_add) {
                    vm.instant_add = data.instant_add;
                } else if(data.instant_add!=undefined) {
                    vm.instant_add = false;
                }
                vm.sorting.enable_sort_pattern = data.enable_sort_pattern;
                vm.sorting.episode_pattern = data.episode_pattern;
                vm.sorting.use_date_pattern = data.use_date_pattern;
                vm.sorting.video_part_pattern = data.video_part_pattern;
                vm.sorting.auto_sort = data.auto_sort;
                vm.sorting.desc_sort = data.desc_sort;
            }

            function onError(data) {
                alert('Cannot retrieve data for channel id ' + channel_id);
            }
        }

        function createClicked() {
            if(vm.enable_auto){
            
                if(vm.auto_source==1&&vm.youtube_channel_id_auto&&!vm.youtube_channel_id_auto.valid){    
                    alert("Youtube Channel id ไม่ถูกต้อง");
                    return;
                }
                if(vm.auto_source==2&&vm.youtube_playlist_id_auto&&!vm.youtube_playlist_id_auto.valid){
                    alert("Youtube Playlist id ไม่ถูกต้อง");
                    return;
                }

                if(vm.auto_source==2&&vm.youtube_user_id_auto&&!vm.youtube_user_id_auto.valid){
                        alert("Youtube User id ไม่ถูกต้อง");
                        return;
                }
            }

            vm.isSubmitting = true;
            var tags=[], i, l;
            for (i=0,l=vm.tags.length; i<l; i++) {
                tags.push(vm.tags[i].id);
            }
            var auto_params = {};

            if(vm.rule_include) {
                auto_params.rule_include = vm.rule_include.text;
            }

            if(vm.rule_exclude) {
                auto_params.rule_exclude = vm.rule_exclude.text;
            }

            if(vm.publish_after) {
                try {
                    auto_params.publish_after = moment(vm.publish_after, 'DD/MM/YYYY HH:mm:ss').utc().format('DD/MM/YYYY HH:mm:ss');
                } catch(e) {
                    console.log(e);
                    alert("เวลา 'เปิดเผยหลังจาก' ไม่ถูกต้อง");
                    return;
                }
            }

            if(vm.publish_before) {
                try {
                    auto_params.publish_before = moment(vm.publish_before, 'DD/MM/YYYY HH:mm:ss').utc().format('DD/MM/YYYY HH:mm:ss');
                } catch(e) {
                    console.log(e);
                    alert("เวลา 'เปิดเผยก่อน' ไม่ถูกต้อง");
                    return;
                }
            }

            if(vm.auto_source==1 && vm.youtube_channel_id_auto) {
                auto_params.youtube_channel_id_auto = vm.youtube_channel_id_auto.text;
            }

            if(vm.auto_source==2 && vm.youtube_playlist_id_auto) {
                auto_params.youtube_playlist_id_auto = vm.youtube_playlist_id_auto.text;
            }

            if(vm.auto_source==3 && vm.youtube_user_id_auto) {
                auto_params.youtube_user_id_auto = vm.youtube_user_id_auto.text;
            }

            auto_params.latest_first = !!vm.latest_first;

            if(vm.instant_add) {
                auto_params.instant_add = vm.instant_add;
            } else {
                auto_params.instant_add = false;
            }

            if(vm.permission_group) {
                auto_params.permission_group = vm.permission_group;
            } else {
                auto_params.permission_group = 1;
            }

            auto_params.enable_sort_pattern = vm.sorting.enable_sort_pattern;
            auto_params.episode_pattern = vm.sorting.episode_pattern;
            auto_params.use_date_pattern = vm.sorting.use_date_pattern;
            auto_params.video_part_pattern = vm.sorting.video_part_pattern;
            auto_params.auto_sort = vm.sorting.auto_sort;
            auto_params.desc_sort = vm.sorting.desc_sort;

            if (vm.env == 'edit') {
                PostService.editChannel(channel_id, vm.channelName, vm.detail, 
                                        vm.icon, vm.icon_url, tags, vm.current_icon == null,
                                        vm.enable_auto, auto_params)
                    .success(onSuccess)
                    .error(onError);
            } else {
                if(vm.first_video) {
                    auto_params.first_video = vm.first_video;
                }
                PostService.createChannel(vm.channelName, vm.detail, vm.icon, vm.icon_url, tags, 
                                        vm.enable_auto, auto_params)
                    .success(onSuccess)
                    .error(onError);
            }

            function onSuccess(data) {
                vm.isSubmitting = false;
                $modalInstance.close(data)
            }

            function onError(data) {
                vm.isSubmitting = false;
                if ('detail' in data)
                    vm.alerts.push({ type: 'danger', msg: data.detail });
                else {
                    for(var prop in data){
                        vm.alerts.push({ type: 'danger', msg: prop + ' ' + data[prop] });
                    }
                }
            }
        }

        function removeIcon() {
            vm.current_icon = null;
        }

        function onChannelIdChange(){
            console.log(vm.youtube_channel_id_auto.text);
            PostService.validateYoutubeChannelId(vm.youtube_channel_id_auto.text)
                .success( function(result) {
                    setValid(result.items.length>0);

                })
                .error( function(result) {
                    setValid(false);
                });

            function setValid(valid) {
                vm.youtube_channel_id_auto.valid = valid;
            }
        }

        function onPlaylistIdChange(){
            console.log(vm.youtube_playlist_id_auto.text);
            PostService.validateYoutubePlaylistId(vm.youtube_playlist_id_auto.text)
                .success( function(result) {
                    setValid(result.items.length>0);

                })
                .error( function(result) {
                    setValid(false);
                });

            function setValid(valid) {
                vm.youtube_playlist_id_auto.valid = valid;
            }
        }

        function onUserIdChange(){
            console.log(vm.youtube_user_id_auto.text);
            PostService.validateYoutubeUserId(vm.youtube_user_id_auto.text)
                .success( function(result) {
                    setValid(result.items.length>0);

                })
                .error( function(result) {
                    setValid(false);
                });

            function setValid(valid) {
                vm.youtube_user_id_auto.valid = valid;
            }
        }
    }
})();
