module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    // Task configuration.
    // pack html
    ngtemplates: {
      feed: {
        src: 'static/feed/templates/**/*.html',
        dest: 'static/dist/feed-template.js',
        options: {
          prefix: '/',
          htmlmin:  { collapseWhitespace: true, collapseBooleanAttributes: true }
        }
      },
      player: {
        src: ['static/feed/templates/layout/buttons/*.html', 'static/feed/templates/layout/modals/*.html'],
        dest: 'static/dist/player-template.js',
        options: {
          prefix: '/',
          htmlmin:  { collapseWhitespace: true, collapseBooleanAttributes: true }
        }
      }
    },
    ngAnnotate: {
        options: {
            singleQuotes: true,
        },
        feed: {
            files: {
                'static/dist/js/app.annotated.js': [
                  'static/feed/js/jquery-2.1.4.min.js',
                  'static/feed/js/bootstrap.min.js',
                  'static/feed/js/angular.min.js',
                  'static/feed/js/angular-route.min.js',
                  'static/feed/js/angular-animate.min.js',
                  'static/feed/js/angulartics.min.js',
                  'static/feed/js/angulartics-ga.min.js',
                  'static/feed/js/Chart.min.js',
                  'static/feed/js/angular-chart.min.js',
                  'static/feed/js/prefixfree.min.js',
                  'static/feed/js/jquery.form.min.js',
                  'static/feed/js/angular-cookies.min.js',
                  'static/feed/js/angular-inview.js',
                  'static/feed/js/angular-sanitize.min.js',
                  'static/feed/js/angular-tooltips.min.js',
                  'static/feed/js/ui-bootstrap-tpls-0.13.0.min.js',
                  'static/feed/js/ng-file-upload-shim.min.js',
                  'static/feed/js/ng-file-upload.min.js',
                  'static/feed/js/ngToast.min.js',
                  'static/feed/js/jqcloud.min.js',
                  'static/feed/js/moment.min.js',
                  'static/feed/js/bootstrap-datetimepicker.min.js',
                  'static/feed/app/feed.js',
                  'static/feed/app/feed.routes.js',
                  'static/feed/app/feed.config.js',
                  'static/feed/app/account/account.module.js',
                  'static/feed/app/account/services/account.service.js',
                  'static/feed/app/layout/layout.module.js',
                  'static/feed/app/layout/controllers/sidebar.controller.js',
                  'static/feed/app/layout/controllers/tageditor.controller.js',
                  'static/feed/app/layout/controllers/facebookbutton.controller.js',
                  'static/feed/app/layout/controllers/savebutton.controller.js',
                  'static/feed/app/layout/directives/lazysrc.directive.js',
                  'static/feed/app/layout/directives/sidebar.directive.js',
                  'static/feed/app/layout/directives/tageditor.directive.js',
                  'static/feed/app/layout/directives/facebookbutton.directive.js',
                  'static/feed/app/layout/directives/savebutton.directive.js',
                  'static/feed/app/layout/services/sidebar.service.js',
                  'static/feed/app/layout/services/post.service.js',
                  'static/feed/app/layout/services/tag.service.js',
                  'static/feed/app/layout/services/usersuggestion.service.js',
                  'static/feed/app/layout/modals/postbox.modal.js',
                  'static/feed/app/layout/modals/suggestionbox.modal.js',
                  'static/feed/app/layout/modals/createchannel.modal.js',
                  'static/feed/app/layout/modals/editpost.modal.js',
                  'static/feed/app/browse/browse.module.js',
                  'static/feed/app/browse/controllers/browse.controller.js',
                  'static/feed/app/browse/controllers/ownchannel.controller.js',
                  'static/feed/app/browse/controllers/followchannel.controller.js',
                  'static/feed/app/browse/controllers/highlight.controller.js',
                  'static/feed/app/browse/controllers/channelview.controller.js',
                  'static/feed/app/browse/controllers/searchview.controller.js',
                  'static/feed/app/browse/controllers/updatechannel.controller.js',
                  'static/feed/app/browse/services/browse.service.js',
                  'static/feed/js/angular-jqcloud.js',
                  'static/player/app/player.js',
                  'static/player/app/player.service.js',
                  'static/player/app/player.config.js',
                  'static/player/app/directives/ng-sortable.min.js',
                  'static/player/app/directives/angular-awesome-slider.min.js',
                  'media/scripts/feed/fb_script.js',
                  'media/scripts/libs/bootstrap3-typeahead-mod.js',
                  'static/feed/js/search_typeahead.js',
                  'static/feed/js/sign_in_register_modal.js',
                  'media/scripts/feed/tag_editor.js',
                  'static/dist/feed-template.js',
                  'static/dist/player-template.js',
                ]
            }
        }
    },
    // pack js
    uglify: {
      feed: {
         files: {
             'static/dist/js/app.min.js': ['static/dist/js/app.annotated.js']
         }
       }
    },
    // pack css
    cssmin: {
      options: {
        keepSpecialComments: false,
      },
      compress: {
        files: {          
          'static/dist/css/app.min.css': 'static/feed/css/*.css',
          'static/dist/css/player.min.css': 'static/player/css/*.css',
        }
      }
    },
    copy: {
      feed: {
        files: [
          // slider
          {expand: true, flatten: true, src: ['static/feed/fonts/*'], dest: 'static/dist/fonts/'},          
        ]
      }
    },
  });

  grunt.loadNpmTasks('grunt-angular-templates');
  // grunt.loadNpmTasks('grunt-angular-builder');
  grunt.loadNpmTasks('grunt-ng-annotate');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-copy');

  // Default task.
  grunt.registerTask('default', ['ngtemplates', 'ngAnnotate', 'uglify', 'cssmin', 'copy']);

};
