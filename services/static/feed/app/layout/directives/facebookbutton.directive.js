/**
* facebookButton
* @namespace feed.layout.directives
*/
(function () {
  'use strict';

  angular
    .module('feed.layout.directives')
    .directive('facebookButton', facebookButton);

  /**
  * @namespace facebookButton
  */
  function facebookButton() {
    /**
    * usage
    * for browse page      <facebook-button video="video"></facebook-button>
    * for bychannel page   <facebook-button playlist="playlist"></facebook-button>
    * @name directive
    * @desc The directive to be returned
    * @memberOf feed.layout.directives.sidebar
    */
    var directive = {
      controller: 'FacebookButtonController',
      controllerAs: 'vm',
      restrict: 'E',
      scope: {
        video: '=',
        playlist: '='
      },
      templateUrl: '/static/feed/templates/layout/buttons/facebookbutton.html'
    };

    return directive;
  }
})();