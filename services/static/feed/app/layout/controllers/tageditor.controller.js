/**
 * TagEditorController
 * @namespace feed.layout.controllers
 */
(function () {
    'use strict';

    angular
        .module('feed.layout.controllers')
        .controller('TagEditorController', TagEditorController);

    TagEditorController.$inject = ['$scope', '$log', 'TagService'];

    /**
     * @namespace TagEditorController
     */
    function TagEditorController($scope, $log, TagService) {
        var vm = this;

        vm.searchWord = "";
        vm.tagSelector = [];

        vm.addTag = addTag;
        vm.removeTag = removeTag;
        vm.createTag = createTag;

        vm.isTagSelected = isTagSelected;

        activate();

        ////////////////////////////////////////

        function activate() {
            TagService.getTags()
                .success(onGetTagSuccess)
                .error(onGetTagError);

            $scope.$watch('vm.searchWord', updateSelector);

            function onGetTagSuccess(data) {
                vm.tagSelector = data;
            }
            function onGetTagError(data) {
                $log.error(data.detail);
            }

            function updateSelector(word, old_word) {
                if (word == old_word) return;
                TagService.getTags(word)
                    .success(onGetTagSuccess)
                    .error(onGetTagError);
            }
        }

        function addTag(tag) {
            $scope.tags.push(tag);
        }

        function removeTag (index) {
            $scope.tags.splice(index, 1);
        }

        function createTag() {
            TagService.createTag(vm.searchWord)
                .success(onSuccess)
                .error(onError);

            function onSuccess(data) {
                addTag(data);
                vm.searchWord = "";
            }
            function onError(data) {
                $log.error(data);
            }
        }

        function isTagSelected(tag) {
            for(var i= 0,l=$scope.tags.length; i<l; i++){
                if(tag.id == $scope.tags[i].id) return true;
            }
            return false;
        }
    }
})();
