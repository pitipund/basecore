/**
 * application configurations
 * @namespace player.config
 */
(function () {
    'use strict';

    angular
        .module('player.config')
        .config(config);

    config.$inject = ['ngToastProvider'];

    /**
     * @name config
     * @desc Define configurations for the application
     */
    function config(ngToast) {

        ngToast.configure({
            animation: 'fade',
            verticalPosition: 'bottom',
            timeout: 3000
        });
    }
})();