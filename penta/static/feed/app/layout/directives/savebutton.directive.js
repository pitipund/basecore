/**
* saveButton
* @namespace feed.layout.directives
*/
(function () {
  'use strict';

  angular
    .module('feed.layout.directives')
    .directive('saveButton', saveButton);

  /**
  * @namespace saveButton
  */
  function saveButton() {
    /**
    * usage
    * for browse page      <save-button video="video"></save-button>
    * for bychannel page   <save-button playlist="playlist"></save-button>
    * @name directive
    * @desc The directive to be returned
    * @memberOf feed.layout.directives.sidebar
    */
    var directive = {
      controller: 'SaveButtonController',
      controllerAs: 'vm',
      restrict: 'E',
      scope: {
        video: '=',
        playlist: '=',
        hidesaved: '='
      },
      templateUrl: '/static/feed/templates/layout/buttons/savebutton.html'
    };

    return directive;
  }
})();