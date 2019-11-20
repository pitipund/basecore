'use strict'

var app = angular.module('plunker', [
                  'feed.layout', 
                  'feed.account',
                  'feed.browse',
                  'ui.bootstrap',
                  'ngToast',
                  'as.sortable',
                  '720kb.tooltips',
              ]);

angular
    .module('plunker')
    .controller('MainCtrl', mainController)

mainController.$inject = ['$http', '$location', '$scope', '$rootScope', 'AccountService', 
                                'BrowseService', 'ngToast', 'PostService',
                                'CreateChannelModal', 'PostboxModal', 'SuggestionBoxModal'];

function mainController($http, $location, $scope, $rootScope, AccountService, 
                               BrowseService, ngToast, PostService, CreateChannelModal, PostboxModal, SuggestionBoxModal){
  $http.defaults.xsrfHeaderName = 'X-CSRFToken';
  $http.defaults.xsrfCookieName = 'csrftoken';

  var vm = $scope;
  $scope.onlyShow = false;
  $scope.curTagId = -1;
  $scope.curTagName = '';
  $scope.allTags = [];
  $scope.channels = [];
  $scope.sortableOptions = {
    containment: '#sortable-container'
  };

  $http.get('/api/v2/tag/manage/')
    .success(function (data) {
      $scope.allTags = data;
    });

  // ---------------------------------------------------------
  $scope.filterChannel = function(item) {
    return item.show || !$scope.onlyShow;
  };

  $scope.openChannelWindow = function(item) {
      window.open("/th/channelplay/"+item.id+"/", "_blank");
  };

  $scope.selectTag = function(id, name) {
    $scope.channels = []
    $scope.curTagId = id;
    $scope.curTagName = name;
    $http.get('/api/v2/tag/manage/?tag_id='+id)
      .success(function(data) {
        $scope.channels = data;
    });
  };

  $scope.updateTag = function() {
    var params = {'tags': $scope.allTags};
    $http.post('/api/v2/tag/manage/', params)
      .success(function(data) {
        location.reload();
      })
      .error(function(data) {
        alert("something wrong, please contact admin");
      });
  };

  $scope.toggleShow = function(item) {
    item.show = !item.show;
    var params = {'channel_show': [item]};
    $http.post('/api/v2/tag/manage/', params)
      .success(function(data) {
        ;
      })
      .error(function(data) {
        alert("something wrong, please contact admin");
      });
  }

  $scope.editChannel = function(item) {
    CreateChannelModal.open(item.id)
        .then(onModalClose);
    function onModalClose(data) {
        if(item.tid && data.tags.indexOf(item.tid)==-1) {
          var index = $scope.channels.indexOf(item);
          if(index >= 0)
            delete $scope.channels[index];
          return;
        }
        item.name = data.name;
    }
  }

};