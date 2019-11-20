/**
* tagEditor
* @namespace feed.layout.directives
*/
(function () {
  'use strict';

  angular
      .module('feed.layout.directives')
      .directive('tagEditor', tagEditor);

      /**
      * @namespace tagEditor
      */
      function tagEditor() {
          /**
          * @name directive
          * @desc The directive to be returned
          * @memberOf feed.layout.directives.tagEditor
          */
          var directive = {
              controller: 'TagEditorController',
              controllerAs: 'vm',
              restrict: 'E',
              scope: {
                  tags: '='
              },
              templateUrl: '/static/feed/templates/layout/tageditor.html'
          };

          return directive;
      }
})();