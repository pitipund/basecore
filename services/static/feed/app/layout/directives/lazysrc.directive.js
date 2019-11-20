/**
 * lazySrc
 * Attribute for <img> tag, using for lazy loading an image.
 * Can be customized transition and placeholder background at the end of this file.
 * original code from https://github.com/Treri/me-lazyload
 * more info http://angularscript.com/minimal-image-lazy-load-directive-angularjs/
 * @namespace feed.layout.directives
 */
(function() {
    'use strict';

    angular.module('feed.layout.directives', [])
        .directive('lazySrc', lazySrc);

    lazySrc.$inject = ['$window', '$document'];

    function lazySrc ($window, $document) {
        var doc = $document[0],
            body = doc.body,
            win = $window,
            $win = angular.element(win),
            wrapper = $("#wrapper"),// sorry for this ugly work around.
            uid = 0,
            elements = {},
            directive;

        activate();

        directive = {
            restrict: 'A',
            scope: {
                lazySrc: '@'
            },
            link: link
        };

        return directive;

        //////////////////////////////////////////////////

        function activate() {
            wrapper.bind('scroll', checkImage);
            $win.bind('resize', checkImage);
        }

        function link ($scope, iElement, attrs) {

            iElement.bind('load', onLoad);

            $scope.$watch('lazySrc', function () {
                if (isVisible(iElement)) {
                    if (iElement.prop("tagName") == 'IMG') {
                        iElement.attr('src', $scope.lazySrc);
                    } else {
                        iElement.css({'background': 'url("' + $scope.lazySrc + '") no-repeat center center',
                                      'background-size':'cover'});
                    }
                } else {
                    var uid = getUid(iElement);
                    iElement.css({
                        'background-color': 'transparent',
                        'opacity': 0,
                        '-webkit-transition': 'opacity 0.5s',
                        'transition': 'opacity 0.5s'
                    });
                    elements[uid] = {
                        iElement: iElement,
                        $scope: $scope
                    };
                }
            });

            $scope.$on('$destroy', function () {
                iElement.unbind('load');
            });
        }

        function getUid(el) {
            return el.__uid || (el.__uid = '' + (++uid));
        }

        function getWindowOffset() {
            var //t,
                //pageXOffset = (typeof win.pageXOffset == 'number') ? win.pageXOffset : (((t = doc.documentElement) || (t = body.parentNode)) && typeof t.ScrollLeft == 'number' ? t : body).ScrollLeft,
                //pageYOffset = (typeof win.pageYOffset == 'number') ? win.pageYOffset : (((t = doc.documentElement) || (t = body.parentNode)) && typeof t.ScrollTop == 'number' ? t : body).ScrollTop;
                pageYOffset = wrapper.scrollTop(),
                pageXOffset = wrapper.scrollLeft();
            return {
                offsetX: pageXOffset,
                offsetY: pageYOffset
            };
        }

        function isVisible(iElement) {
            var elem = iElement[0],
                elemRect = elem.getBoundingClientRect(),
                windowOffset = getWindowOffset(),
                winOffsetX = windowOffset.offsetX,
                winOffsetY = windowOffset.offsetY,
                elemWidth = elemRect.width,
                elemHeight = elemRect.height,
                elemOffsetX = elemRect.left + winOffsetX,
                elemOffsetY = elemRect.top + winOffsetY,
                viewWidth = win.innerWidth,
                viewHeight = win.innerHeight,
                xVisible = false,
                yVisible = false;

            if (elemOffsetY <= winOffsetY) {
                if (elemOffsetY + elemHeight >= winOffsetY) {
                    yVisible = true;
                }
            } else if (elemOffsetY >= winOffsetY) {
                if (elemOffsetY <= winOffsetY + viewHeight) {
                    yVisible = true;
                }
            }

            if (elemOffsetX <= winOffsetX) {
                if (elemOffsetX + elemWidth >= winOffsetX) {
                    xVisible = true;
                }
            } else if (elemOffsetX >= winOffsetX) {
                if (elemOffsetX <= winOffsetX + viewWidth) {
                    xVisible = true;
                }
            }

            return xVisible && yVisible;
        }

        function checkImage() {
            getWindowOffset();
            Object.keys(elements).forEach(function (key) {

                var obj = elements[key],
                    iElement = obj.iElement,
                    $scope = obj.$scope;
                if (isVisible(iElement)) {
                    if (iElement.prop("tagName") == 'IMG') {
                        iElement.attr('src', $scope.lazySrc);
                    } else {
                        iElement.css({'background': 'url("' + $scope.lazySrc + '") no-repeat center center',
                                      'background-size':'cover',
                                      'opacity': 1.0 });
                    }
                }
            });
        }

        function onLoad() {
            var $el = angular.element(this),
                uid = getUid($el);

            $el.css('opacity', 1);

            if (elements.hasOwnProperty(uid)) {
                delete elements[uid];
            }
        }

    }
})();