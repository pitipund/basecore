/**
* sidebar
* @namespace feed.layout.directives
*/
(function () {
  'use strict';

  angular
    .module('feed.layout.directives')
    .directive('sidebar', sidebar);

  /**
  * @namespace sidebar
  */
  function sidebar() {
    /**
    * @name directive
    * @desc The directive to be returned
    * @memberOf feed.layout.directives.sidebar
    */
    var directive = {
      controller: 'SidebarController',
      controllerAs: 'vm',
      restrict: 'E',
      //scope: {
      //  sidebar: '='
      //},
      templateUrl: '/static/feed/templates/layout/sidebar.html'
    };

    return directive;
  }
})();