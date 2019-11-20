/**
 * Channel report controller
 * @namespace reports.channel.controllers
 */
(function () {
    'use strict';

    angular
        .module('reports.channel.controllers')
        .controller('ChannelReportController', ChannelReportController);

    ChannelReportController.$inject = ['ChannelReport'];

    function ChannelReportController (ChannelReport) {
        var vm = this;

        vm.user_per_day = [];
        vm.channel_per_day = [];
        vm.sorted_by = "visit";
        vm.sorted_by_name=false;
        vm.reverse = false;
        vm.current_sorted_column = -1;

        // chart
        vm.series = ['Guest', 'User', 'Penta TV', 'Staff','Total'];
        vm.data = [];
        vm.labels = [];

        vm.channelNameSort = channelNameSort;
        vm.channelSort = channelSort;

        activate();

        return vm;

        ////////////////////////////////////

        function activate() {
            ChannelReport.getUserPerDay()
                .success(function(data){
                    var len_1 = data.length - 1;
                    for (var i=len_1, l=0; i>=l; --i) {
                        vm.user_per_day[len_1-i] = data[i];
                    }
                    drawChart();
                });
            ChannelReport.getChannelPerDay()
                .success(function (data) {
                    vm.channel_per_day = data;
                })
        }

        function channelNameSort(){
            if (vm.sorted_by_name) vm.reverse = !vm.reverse;
            vm.current_sorted_column = -1;
            vm.sorted_by_name = true;
            vm.channel_per_day.counter.sort(compare);
            function compare(a, b) {
                if (vm.reverse) {
                    return a['name'].localeCompare(b['name']);
                }
                return b['name'].localeCompare(a['name']);
            }
        }

        function channelSort(column){
            if (vm.current_sorted_column == column) vm.reverse = !vm.reverse;
            vm.current_sorted_column = column;

            console.log(vm.channel_per_day.counter);
            vm.channel_per_day.counter.sort(compare);
            vm.sorted_by_name = false;

            function compare(a, b) {
                if (vm.reverse) {
                    return a['values'][column][vm.sorted_by]['total'] - b['values'][column][vm.sorted_by]['total'];
                }
                return b['values'][column][vm.sorted_by]['total'] - a['values'][column][vm.sorted_by]['total'];
            }
        }

        function drawChart() {
            // vm.series = ['guest', 'user', 'staff', 'penta', 'total'];
            vm.data = [[],[],[],[],[]];
            console.log(vm.user_per_day);

            for (var i=0, l=vm.user_per_day.length, bulk=null; i<l; ++i) {
                bulk = vm.user_per_day[i];
                console.log(bulk);
                vm.labels.push(bulk.date);
                vm.data[0].push(bulk.counter.guest);
                vm.data[1].push(bulk.counter.user);
                vm.data[2].push(bulk.counter.penta);
                vm.data[3].push(bulk.counter.staff);
                vm.data[4].push(bulk.counter.total);
            }

            vm.colours = [
                { // light blue
                    fillColor: 'rgba(151,187,205,0)',
                    strokeColor: '#97BBCD',
                    pointColor: '#97BBCD',
                    pointStrokeColor: '#fff',
                    pointHighlightFill: '#fff',
                    pointHighlightStroke: '#97BBCD'
                },
                { // dark blue
                    fillColor: 'rgba(65, 116, 140,0)',
                    strokeColor: 'rgba(65, 116, 140,1)',
                    pointColor: 'rgba(65, 116, 140,1)',
                    pointStrokeColor: '#fff',
                    pointHighlightFill: '#fff',
                    pointHighlightStroke: 'rgba(65, 116, 140,1)'
                },
                { // blue
                    fillColor: 'rgba(65, 116, 140,0)',
                    strokeColor: 'rgba(50, 90, 160,1)',
                    pointColor: 'rgba(50, 90, 160,1)',
                    pointStrokeColor: '#fff',
                    pointHighlightFill: '#fff',
                    pointHighlightStroke: 'rgba(65, 116, 140,1)'
                },
                { // Yellow
                    fillColor: 'rgba(253, 179, 92,0)',
                    strokeColor: 'rgba(253, 179, 92,1)',
                    pointColor: 'rgba(253, 179, 92,1)',
                    pointStrokeColor: '#fff',
                    pointHighlightFill: '#fff',
                    pointHighlightStroke: 'rgba(253, 179, 92,1)'
                },
                { // light grey
                    fillColor: 'rgba(220, 220, 220,0)',
                    strokeColor: 'rgba(220, 220, 220,1)',
                    pointColor: 'rgba(220, 220, 220,1)',
                    pointStrokeColor: '#fff',
                    pointHighlightFill: '#fff',
                    pointHighlightStroke: 'rgba(220, 220, 220,1)'
                }
            ];
        }
    }
})();