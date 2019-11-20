/**
 * @version: 1.3.21
 * @author: Dan Grossman http://www.dangrossman.info/
 * @copyright: Copyright (c) 2012-2015 Dan Grossman. All rights reserved.
 * @license: Licensed under the MIT license. See http://www.opensource.org/licenses/mit-license.php
 * @website: https://www.improvely.com/
 */

(function (root, factory) {

    if(typeof define === 'function' && define.amd) {
        define(['moment', 'jquery', 'exports'], function (momentjs, $, exports) {
            root.daterangepicker = factory(root, exports, momentjs, $);
        });

    } else if(typeof exports !== 'undefined') {
        var momentjs = require('moment');
        var jQuery;
        try {
            jQuery = require('jquery');
        } catch(err) {
            jQuery = window.jQuery;
            if(!jQuery) throw new Error('jQuery dependency not found');
        }

        factory(root, exports, momentjs, jQuery);

        // Finally, as a browser global.
    } else {
        root.daterangepicker = factory(root, {}, root.moment, (root.jQuery || root.Zepto ||
            root.ender || root.$));
    }

}(this, function (root, daterangepicker, moment, $) {

    var DateRangePicker = function (element, options, cb, valid, inValid) {

        // by default, the daterangepicker element is placed at the bottom of HTML body
        this.parentEl = 'body';

        //element that triggered the date range picker
        this.element = $(element);

        //tracks visible state
        this.isShowing = false;

        //create the picker HTML object
        var DRPTemplate = '<div class="daterangepicker dropdown-menu">' +
            '<div class="ranges">' +
            '<div class="range_inputs">' +
            '<div class="daterangepicker_start_input">' +
            '<label for="daterangepicker_start"></label>' +
            '<input class="input-mini" type="text" name="daterangepicker_start" value="" />' +
            '</div>' +
            '<div class="daterangepicker_end_input">' +
            '<label for="daterangepicker_end"></label>' +
            '<input class="input-mini" type="text" name="daterangepicker_end" value="" />' +
            '</div>' +
            '<button class="applyBtn" disabled="disabled"></button>&nbsp;' +
            '<button class="cancelBtn"></button>' +
            '</div>' +
            '</div>' +
            '<div class="calendar first left"></div>' +   //VC move this line here to show the range section upper itself
            '<div class="calendar second right"></div>' + //VC move this line here to show the range section upper itself
            '</div>';

        //custom options
        if(typeof options !== 'object' || options === null)
            options = {};

        this.parentEl = (typeof options === 'object' && options.parentEl &&
            $(options.parentEl).length) ? $(options.parentEl) : $(this.parentEl);
        this.container = $(DRPTemplate).appendTo(this.parentEl);

        this.setOptions(options, cb, valid, inValid);

        //event listeners
        this.container.find('.calendar')
            .on('click.daterangepicker', '.prev', $.proxy(this.clickPrev,
                this))
            .on('click.daterangepicker', '.next', $.proxy(this.clickNext,
                this))
            .on('click.daterangepicker', 'td.available', $.proxy(this.clickDate,
                this))
            .on('mouseenter.daterangepicker', 'td.available', $.proxy(this.hoverDate,
                this))
            .on('mouseleave.daterangepicker', 'td.available', $.proxy(this.updateFormInputs,
                this))
            .on('change.daterangepicker', 'select.yearselect', $.proxy(this.updateMonthYear,
                this))
            .on('change.daterangepicker', 'select.monthselect', $.proxy(this
                .updateMonthYear, this))
            .on('change.daterangepicker',
                'select.hourselect,select.minuteselect,select.secondselect,select.ampmselect',
                $.proxy(this.updateTime, this));

        this.container.find('.ranges')
            .on('click.daterangepicker', 'button.applyBtn', $.proxy(this.clickApply,
                this))
            .on('click.daterangepicker', 'button.cancelBtn', $.proxy(this.clickCancel,
                this))
            .on('click.daterangepicker',
                '.daterangepicker_start_input,.daterangepicker_end_input', $
                .proxy(this.showCalendars, this))
            .on('change.daterangepicker',
                '.daterangepicker_start_input,.daterangepicker_end_input', $
                .proxy(this.inputsChanged, this))
            .on('keydown.daterangepicker',
                '.daterangepicker_start_input,.daterangepicker_end_input', $
                .proxy(this.inputsKeydown, this))
            .on('click.daterangepicker', 'li', $.proxy(this.clickRange, this))
            .on('mouseenter.daterangepicker', 'li', $.proxy(this.enterRange,
                this))
            .on('mouseleave.daterangepicker', 'li', $.proxy(this.updateFormInputs,
                this));

        if(this.element.is('input')) {
            this.element.on({
                'click.daterangepicker': $.proxy(this.show, this),
                'focus.daterangepicker': $.proxy(this.show, this),
                'keyup.daterangepicker': $.proxy(this.updateFromControl,
                    this),
                'keydown.daterangepicker': $.proxy(this.keydown,
                    this)
            });
        } else {
            this.element.on('click.daterangepicker', $.proxy(this.toggle,
                this));
        }

    };

    DateRangePicker.prototype = {

        constructor: DateRangePicker,

        setOptions: function (options, callback, valid, inValid) {

            this.startDate = moment().startOf('day');
            this.endDate = moment().endOf('day');
            this.timeZone = moment().utcOffset();
            this.minDate = false;
            this.maxDate = false;
            this.dateLimit = false;

            this.showDropdowns = false;
            this.showWeekNumbers = false;
            this.timePicker = false;
            this.timePickerSeconds = false;
            this.timePickerIncrement = 30;
            this.timePicker12Hour = true;
            this.singleDatePicker = false;
            this.ranges = {};
            this.thai = false;
            this.singleModeRange = false

            this.opens = 'right';
            if(this.element.hasClass('pull-right'))
                this.opens = 'left';

            this.drops = 'down';
            if(this.element.hasClass('dropup'))
                this.drops = 'up';

            this.buttonClasses = ['ui', 'compact', 'small', 'button'];
            this.applyClass = 'primary';
            this.cancelClass = 'secondary';

            this.format = 'DD/MM/YYYY';
            this.separator = ' - ';

            this.locale = {
                applyLabel: 'Apply',
                cancelLabel: 'Cancel',
                fromLabel: 'From',
                toLabel: 'To',
                weekLabel: 'W',
                customRangeLabel: 'Custom Range',
                daysOfWeek: moment.weekdaysMin(),
                monthNames: moment.monthsShort(),
                firstDay: moment.localeData()._week.dow
            };

            this.cb = function () {};

            //VC
            //set valid, invalid callback
            this.valid = valid;
            this.inValid = inValid;

            //VC 
            //thai option for showing thai style calendar
            if(typeof options.thai === 'boolean')
                this.thai = options.thai;
            
            //VC 
            //if singleModeRange is set to true, it will show range panel in single mode
            if(typeof options.singleModeRange === 'boolean')
                this.singleModeRange = options.singleModeRange;

            if(typeof options.format === 'string')
                this.format = options.format;
            
            if(typeof options.separator === 'string')
                this.separator = options.separator;

            if(typeof options.startDate === 'string'){
                //VC
                //if thai style minus startDate by 543
                this.startDate = moment(options.startDate, this.format);
                var _year  = Math.max(moment(options.startDate, this.format).year() - 543, 0);
                var _month = moment(options.startDate, this.format).month();
                var _day   = moment(options.startDate, this.format).date();
                var newStartDate = _day + "/" + _month + "/" + _year;
                if(this.thai) this.startDate = moment(newStartDate, this.format);
            }

            if(typeof options.endDate === 'string'){
                //VC
                //if thai style minus endDate by 543
                this.endDate = moment(options.endDate, this.format);
                var _year  = Math.max(moment(options.endDate, this.format).year() - 543, 0);
                var _month = moment(options.endDate, this.format).month();
                var _day   = moment(options.endDate, this.format).date();
                var newEndDate = _day + "/" + _month + "/" + _year;
                if(this.thai) this.endDate = moment(newEndDate, this.format);
            }

            if(typeof options.minDate === 'string'){
                //VC
                //if thai style minus minDate by 543
                this.minDate = moment(options.minDate, this.format);
                var _year  = Math.max(moment(options.minDate, this.format).year() - 543, 0);
                var _month = moment(options.minDate, this.format).month();
                var _day   = moment(options.minDate, this.format).date();
                var newMinDate = _day + "/" + _month + "/" + _year;
                if(this.thai) this.minDate = moment(newMinDate, this.format);
            }

            if(typeof options.maxDate === 'string'){
                this.maxDate = moment(options.maxDate, this.format);
                //VC
                //if thai style minus maxDate by 543
                var _year  = Math.max(moment(options.maxDate, this.format).year() - 543, 0);
                var _month = moment(options.maxDate, this.format).month();
                var _day   = moment(options.maxDate, this.format).date();
                var newMaxDate = _day + "/" + _month + "/" + _year;
                if(this.thai) this.maxDate = moment(newMaxDate, this.format);
            }

            if(typeof options.startDate === 'object'){
                this.startDate = moment(options.startDate);
                //VC
                //if thai style minus startDate by 543
                var _year  = Math.max(moment(options.startDate).year() - 543, 0);
                var _month = moment(options.startDate).month();
                var _day   = moment(options.startDate).date();
                var newStartDate = _day + "/" + _month + "/" + _year;
                if(this.thai) this.startDate = moment(newStartDate, this.format);
            }

            if(typeof options.endDate === 'object'){
                this.endDate = moment(options.endDate);
                //VC
                //if thai style minus endDate by 543
                var _year  = Math.max(moment(options.endDate).year() - 543, 0);
                var _month = moment(options.endDate).month();
                var _day   = moment(options.endDate).date();
                var newEndDate = _day + "/" + _month + "/" + _year;
                if(this.thai) this.endDate = moment(newEndDate, this.format);
            }

            if(typeof options.minDate === 'object'){
                this.minDate = moment(options.minDate);
                //VC
                //if thai style minus minDate by 543
                var _year  = Math.max(moment(options.minDate).year() - 543, 0);
                var _month = moment(options.minDate).month();
                var _day   = moment(options.minDate).date();
                var newMinDate = _day + "/" + _month + "/" + _year;
                if(options.thai) this.minDate = moment(newMinDate, this.format);
            }

            if(typeof options.maxDate === 'object'){
                this.maxDate = moment(options.maxDate);
                //VC
                //if thai style minus maxDate by 543
                var _year  = Math.max(moment(options.maxDate).year() - 543, 0);
                var _month = moment(options.maxDate).month();
                var _day   = moment(options.maxDate).date();
                var newMaxDate = _day + "/" + _month + "/" + _year;
                if(this.thai) this.maxDate = moment(newMaxDate, this.format);
            }

            if(typeof options.applyClass === 'string')
                this.applyClass = options.applyClass;

            if(typeof options.cancelClass === 'string')
                this.cancelClass = options.cancelClass;

            if(typeof options.dateLimit === 'object')
                this.dateLimit = options.dateLimit;
            
           

            if(typeof options.locale === 'object') {

                if(typeof options.locale.daysOfWeek === 'object') {
                    // Create a copy of daysOfWeek to avoid modification of original
                    // options object for reusability in multiple daterangepicker instances
                    this.locale.daysOfWeek = options.locale.daysOfWeek.slice();
                }

                if(typeof options.locale.monthNames === 'object') {
                    this.locale.monthNames = options.locale.monthNames.slice();
                }

                if(typeof options.locale.firstDay === 'number') {
                    this.locale.firstDay = options.locale.firstDay;
                }

                if(typeof options.locale.applyLabel === 'string') {
                    this.locale.applyLabel = options.locale.applyLabel;
                }

                if(typeof options.locale.cancelLabel === 'string') {
                    this.locale.cancelLabel = options.locale.cancelLabel;
                }

                if(typeof options.locale.fromLabel === 'string') {
                    this.locale.fromLabel = options.locale.fromLabel;
                }

                if(typeof options.locale.toLabel === 'string') {
                    this.locale.toLabel = options.locale.toLabel;
                }

                if(typeof options.locale.weekLabel === 'string') {
                    this.locale.weekLabel = options.locale.weekLabel;
                }

                if(typeof options.locale.customRangeLabel === 'string') {
                    this.locale.customRangeLabel = options.locale.customRangeLabel;
                }
            }

            if(typeof options.opens === 'string')
                this.opens = options.opens;

            if(typeof options.drops === 'string')
                this.drops = options.drops;

            if(typeof options.showWeekNumbers === 'boolean') {
                this.showWeekNumbers = options.showWeekNumbers;
            }

            if(typeof options.buttonClasses === 'string') {
                this.buttonClasses = [options.buttonClasses];
            }

            if(typeof options.buttonClasses === 'object') {
                this.buttonClasses = options.buttonClasses;
            }

            if(typeof options.showDropdowns === 'boolean') {
                this.showDropdowns = options.showDropdowns;
            }

            if(typeof options.singleDatePicker === 'boolean') {
                this.singleDatePicker = options.singleDatePicker;
                if(this.singleDatePicker) {
                    this.endDate = this.startDate.clone();
                }
            }

            if(typeof options.timePicker === 'boolean') {
                this.timePicker = options.timePicker;
            }

            if(typeof options.timePickerSeconds === 'boolean') {
                this.timePickerSeconds = options.timePickerSeconds;
            }

            if(typeof options.timePickerIncrement === 'number') {
                this.timePickerIncrement = options.timePickerIncrement;
            }

            if(typeof options.timePicker12Hour === 'boolean') {
                this.timePicker12Hour = options.timePicker12Hour;
            }

            // update day names order to firstDay
            if(this.locale.firstDay !== 0) {
                var iterator = this.locale.firstDay;
                while(iterator > 0) {
                    this.locale.daysOfWeek.push(this.locale.daysOfWeek.shift());
                    iterator--;
                }
            }

            var start, end, range;

            //if no start/end dates set, check if an input element contains initial values
            if(typeof options.startDate === 'undefined' && typeof options
                .endDate === 'undefined') {
                if($(this.element).is('input[type=text]')) {
                    var val = $(this.element).val(),
                        split = val.split(this.separator);
                    
                    start = end = null;

                    if(split.length == 2) {
                        start = moment(split[0], this.format);
                        end = moment(split[1], this.format);
                    } else if(this.singleDatePicker && val !== "") {
                        start = moment(val, this.format);
                        end = moment(val, this.format);
                    }
                    if(start !== null && end !== null) {
                        this.startDate = start.isValid() ? start : this.startDate;
                        this.endDate = end.isValid() ? end : this.endDate;
                    }

                    //VC
                    //if thai style, year - 543
                    //TODO fix problem about format
                    //this code can only use format like DD/MM/YYYY
                    if(this.thai && split.length == 2){
                        var _startDate = split[0].split("/");
                        var _sdate = Number(_startDate[0]);
                        var _smonth = Number(_startDate[1]);
                        var _syear = Number(_startDate[2]);

                        if( Number.isInteger(_sdate)   && 
                            Number.isInteger(_smonth) && 
                            Number.isInteger(_syear)  ){

                            _syear = Math.max(_syear - 543, 0);
                            _startDate = _sdate + "/" + _smonth + "/" + _syear;
                            _startDate = moment(_startDate, this.format);
                            this.startDate = _startDate.isValid() ? _startDate : this.startDate; 
                        } 

                        var _endDate = split[1].split("/");
                        var _eday = Number(_endDate[0]);
                        var _emonth = Number(_endDate[1]);
                        var _eyear = Number(_endDate[2]);

                        if( Number.isInteger(_eday)   && 
                            Number.isInteger(_emonth) && 
                            Number.isInteger(_eyear)  ){

                            _eyear = Math.max(_eyear - 543, 0);
                            _endDate = _eday + "/" + _emonth + "/" + _eyear;
                            _endDate = moment(_endDate, this.format);
                            this.endDate = _endDate.isValid() ? _endDate : this.endDate;
                        }
                    }
                    else if(this.thai && split.length == 1){
                        var value = split[0].split("/");
                        var _day = Number(value[0]);
                        var _month = Number(value[1]);
                        var _year = Number(value[2]);
                        var _date;

                        if( Number.isInteger(_day)   && 
                            Number.isInteger(_month) && 
                            Number.isInteger(_year)  ){

                            _year = Math.max(_year - 543, 0);
                            value = _day + "/" + _month + "/" + _year;
                            _date = moment(value, this.format);
                            this.startDate = _date.isValid() ? _date : this.startDate; 
                            this.endDate   = _date.isValid() ? _date : this.endDate;
                        } 
                    }
                }
            }

            // bind the time zone used to build the calendar to either the
            // timeZone passed in through the options or the zone of the
            // startDate (which will be the local time zone by default)
            if(typeof options.timeZone === 'string' || typeof options.timeZone ===
                'number') {
                if(typeof options.timeZone === 'string' && typeof moment
                    .tz !== 'undefined') {
                    this.timeZone = moment.tz.zone(options.timeZone).parse(
                        new Date()) * -1; // Offset is positive if the timezone is behind UTC and negative if it is ahead.
                } else {
                    this.timeZone = options.timeZone;
                }
                this.startDate.utcOffset(this.timeZone);
                this.endDate.utcOffset(this.timeZone);
            } else {
                this.timeZone = moment(this.startDate).utcOffset();
            }

            if(typeof options.ranges === 'object') {
                for(range in options.ranges) {

                    if(typeof options.ranges[range][0] === 'string')
                        start = moment(options.ranges[range][0], this.format);
                    else
                        start = moment(options.ranges[range][0]);

                    if(typeof options.ranges[range][1] === 'string')
                        end = moment(options.ranges[range][1], this.format);
                    else
                        end = moment(options.ranges[range][1]);
                    
                    //VC
                    //if thai style, year - 543
                    //TODO fix problem about format
                    //this code can only use format like DD/MM/YYYY
                    if(this.thai){
                        var _start = options.ranges[range][0].split("/");
                        var _end   = options.ranges[range][1].split("/");

                        var _sday   = parseInt(_start[0]),
                            _smonth = parseInt(_start[1]),
                            _syear  = Math.max(parseInt(_start[2]) - 543, 0),
                            _eday   = parseInt(_end[0]),
                            _emonth = parseInt(_end[1]),
                            _eyear  = Math.max(parseInt(_end[2]) - 543, 0),
                            _start  = _sday + "/" + _smonth + "/" + _syear,
                            _end    = _eday + "/" + _emonth + "/" + _eyear;

                        start = moment(_start, this.format);
                        end   = moment(_end, this.format);
                    }

                    // If we have a min/max date set, bound this range
                    // to it, but only if it would otherwise fall
                    // outside of the min/max.
                    if(this.minDate && start.isBefore(this.minDate))
                        start = moment(this.minDate);

                    if(this.maxDate && end.isAfter(this.maxDate))
                        end = moment(this.maxDate);

                    // If the end of the range is before the minimum (if min is set) OR
                    // the start of the range is after the max (also if set) don't display this
                    // range option.
                    if((this.minDate && end.isBefore(this.minDate)) || (
                            this.maxDate && start.isAfter(this.maxDate))) {
                        continue;
                    }

                    this.ranges[range] = [start, end];
                }

                var list = '<ul>';
                for(range in this.ranges) {
                    list += '<li>' + range + '</li>';
                }
                //VC
                //if singleModeRange it will not show custom label
                if(!this.singleModeRange){
                    list += '<li>' + this.locale.customRangeLabel + '</li>';
                }
                list += '</ul>';
                this.container.find('.ranges ul').remove();
                this.container.find('.ranges').prepend(list);
            }

            if(typeof callback === 'function') {
                this.cb = callback;
            }

            if(!this.timePicker) {
                this.startDate = this.startDate.startOf('day');
                this.endDate = this.endDate.endOf('day');
            }

            if(this.singleDatePicker) {
                this.opens = 'right';
                this.container.addClass('single');
                this.container.find('.calendar.right').show();
                this.container.find('.calendar.left').hide();
                if(!this.timePicker) {
                    //VC
                    //show ranges button on top of calendar in case single calendar
                    if(!this.singleModeRange){
                        this.container.find('.ranges').hide();
                    }else{
                        this.container.find('.ranges').show();
                        this.container.find('.calendar.right, .ranges .range_inputs').hide();
                    }
                } else {
                    this.container.find(
                        '.ranges .daterangepicker_start_input, .ranges .daterangepicker_end_input'
                    ).hide();
                }
                if(!this.container.find('.calendar.right').hasClass(
                        'single'))
                    this.container.find('.calendar.right').addClass(
                        'single');
            } else {
                this.container.removeClass('single');
                this.container.find('.calendar.right').removeClass(
                    'single');
                this.container.find('.ranges').show();
            }

            this.oldStartDate = this.startDate.clone();
            this.oldEndDate = this.endDate.clone();
            this.oldChosenLabel = this.chosenLabel;

            this.leftCalendar = {
                month: moment([this.startDate.year(), this.startDate
                    .month(), 1, this.startDate.hour(), this
                    .startDate.minute(), this.startDate.second()
                ]),
                calendar: []
            };

            this.rightCalendar = {
                month: moment([this.endDate.year(), this.endDate.month(),
                    1, this.endDate.hour(), this.endDate.minute(),
                    this.endDate.second()
                ]),
                calendar: []
            };

            if(this.opens == 'right' || this.opens == 'center') {
                //swap calendar positions
                var first = this.container.find('.calendar.first');
                var second = this.container.find('.calendar.second');

                if(second.hasClass('single')) {
                    second.removeClass('single');
                    first.addClass('single');
                }

                first.removeClass('left').addClass('right');
                second.removeClass('right').addClass('left');

                if(this.singleDatePicker) {
                    first.show();
                    second.hide();
                }
            }

            if(typeof options.ranges === 'undefined' && !this.singleDatePicker) {
                this.container.addClass('show-calendar');
            }

            this.container.removeClass('opensleft opensright').addClass(
                'opens' + this.opens);

            this.updateView();
            this.updateCalendars();

            //apply CSS classes and labels to buttons
            var c = this.container;
            $.each(this.buttonClasses, function (idx, val) {
                c.find('button').addClass(val);
            });
            this.container.find('.daterangepicker_start_input label').html(
                this.locale.fromLabel);
            this.container.find('.daterangepicker_end_input label').html(
                this.locale.toLabel);
            if(this.applyClass.length)
                this.container.find('.applyBtn').addClass(this.applyClass);
            if(this.cancelClass.length)
                this.container.find('.cancelBtn').addClass(this.cancelClass);
            this.container.find('.applyBtn').html(this.locale.applyLabel);
            this.container.find('.cancelBtn').html(this.locale.cancelLabel);
        },

        setStartDate: function (startDate) {
            if(typeof startDate === 'string')
                this.startDate = moment(startDate, this.format).utcOffset(
                    this.timeZone);

            if(typeof startDate === 'object')
                this.startDate = moment(startDate);

            if(!this.timePicker)
                this.startDate = this.startDate.startOf('day');

            this.oldStartDate = this.startDate.clone();

            this.updateView();
            this.updateCalendars();
            this.updateInputText();
        },

        setEndDate: function (endDate) {
            if(typeof endDate === 'string')
                this.endDate = moment(endDate, this.format).utcOffset(
                    this.timeZone);

            if(typeof endDate === 'object')
                this.endDate = moment(endDate);

            if(!this.timePicker)
                this.endDate = this.endDate.endOf('day');

            this.oldEndDate = this.endDate.clone();

            this.updateView();
            this.updateCalendars();
            this.updateInputText();
        },

        updateView: function () {
            this.leftCalendar.month.month(this.startDate.month()).year(
                this.startDate.year()).hour(this.startDate.hour()).minute(
                this.startDate.minute());
            this.rightCalendar.month.month(this.endDate.month()).year(
                this.endDate.year()).hour(this.endDate.hour()).minute(
                this.endDate.minute());
            this.updateFormInputs();
        },

        updateFormInputs: function () {
            this.container.find('input[name=daterangepicker_start]').val(
                this.startDate.format(this.format));
            this.container.find('input[name=daterangepicker_end]').val(
                this.endDate.format(this.format));

            //VC
            //if thai style, year in 2 textboxs = year + 543
            if(this.thai){
                var _sYear  = this.startDate.year()  + 543,
                    _sMonth = this.startDate.month() + 1,
                    _sDay   = this.startDate.date(),
                    _eYear  = this.endDate.year()  + 543,
                    _eMonth = this.endDate.month() + 1,
                    _eDay   = this.endDate.date(),
                    _sDate  = _sDay + "/" + _sMonth + "/" + _sYear,
                    _eDate  = _eDay + "/" + _eMonth + "/" + _eYear;

                //VC
                //TODO fix this problem [can't use this.format]
                this.container.find('input[name=daterangepicker_start]').val(_sDate);
                this.container.find('input[name=daterangepicker_end]').val(_eDate);
            }

            if(this.startDate.isSame(this.endDate) || this.startDate.isBefore(
                    this.endDate)) {
                this.container.find('button.applyBtn').removeAttr(
                    'disabled');
            } else {
                this.container.find('button.applyBtn').attr('disabled',
                    'disabled');
            }
        },

        updateFromControl: function () {
            var isValid = true;
            if(!this.element.is('input')) isValid = false;
            if(!this.element.val().length) isValid = false;

            if(!isValid){
                this.inValid();
                return;
            }

            var dateString = this.element.val().split(this.separator),
                start = null,
                end = null;
            
            //VC
            //if thai style, year - 543
            //TODO fix problem about format
            //this code can only use format like DD/MM/YYYY
            if(this.thai){
                if(dateString.length === 2){
                    var _start = dateString[0].split("/");
                    var _sdate  = parseInt(_start[0]);
                    var _smonth = parseInt(_start[1]);
                    var _syear  = parseInt(_start[2]);

                    _syear = Math.max(_syear - 543, 0);
                    _start = _sdate + "/" + _smonth + "/" + _syear;
                    start = moment(_start, this.format).utcOffset(this.timeZone);

                    var _end = dateString[1].split("/");
                    var _edate  = parseInt(_end[0]);
                    var _emonth = parseInt(_end[1]);
                    var _eyear  = parseInt(_end[2]);

                    _eyear = Math.max(_eyear - 543, 0);
                    _end = _edate + "/" + _emonth + "/" + _eyear;
                    end = moment(_end, this.format).utcOffset(this.timeZone);
                }
                else if(this.singleDatePicker || start === null || end === null){
                    var value  = this.element.val().split("/");
                    var _day = Number(value[0]);
                    var _month = Number(value[1]);
                    var _year = Number(value[2]);

                    //validate input
                    if(Number.isInteger(_day) && Number.isInteger(_month) && Number.isInteger(_year)){
                        if(("" + _day).length > 2) isValid = false;
                        if(("" + _month).length > 2) isValid = false;
                        if(("" + _year).length > 4) isValid = false;
                        if(_year < 543) isValid = false;
                    }
                    else{
                        isValid = false;
                    }

                    _year = Math.max(_year - 543, 0);
                    value = _day + "/" + _month + "/" + _year;
                    start = moment(value, this.format).utcOffset(this.timeZone);
                    end = start;

                    if(!start.isValid())
                        isValid = false;
                }
            }
            else{
                if(dateString.length === 2) {
                    start = moment(dateString[0], this.format).utcOffset(
                        this.timeZone);
                    end = moment(dateString[1], this.format).utcOffset(this.timeZone);
                }

                if(this.singleDatePicker || start === null || end === null) {
                    start = moment(this.element.val(), this.format).utcOffset(
                        this.timeZone);
                    end = start;
                }

                if(!start.isValid() || !end.isValid()) isValid = false;
            }

            //VC
            if(!isValid || end.isBefore(start)){
                this.inValid();
                return;
            }

            this.valid();
            
            this.oldStartDate = this.startDate.clone();
            this.oldEndDate = this.endDate.clone();

            this.startDate = start;
            this.endDate = end;

            if(!this.startDate.isSame(this.oldStartDate) || !this.endDate
                .isSame(this.oldEndDate))
                this.notify();

            this.updateCalendars();
        },

        keydown: function (e) {
            //hide on tab or enter
            if((e.keyCode === 9) || (e.keyCode === 13)) {
                this.hide();
            }
        },

        notify: function () {
            this.updateView();
            this.cb(this.startDate, this.endDate, this.chosenLabel);
        },

        move: function () {
            var parentOffset = {
                    top: 0,
                    left: 0
                },
                containerTop;
            var parentRightEdge = $(window).width();
            if(!this.parentEl.is('body')) {
                parentOffset = {
                    top: this.parentEl.offset().top - this.parentEl.scrollTop(),
                    left: this.parentEl.offset().left - this.parentEl
                        .scrollLeft()
                };
                parentRightEdge = this.parentEl[0].clientWidth + this.parentEl
                    .offset().left;
            }

            if(this.drops == 'up')
                containerTop = this.element.offset().top - this.container
                .outerHeight() - parentOffset.top;
            else
                containerTop = this.element.offset().top + this.element.outerHeight() -
                parentOffset.top;
            this.container[this.drops == 'up' ? 'addClass' :
                'removeClass']('dropup');

            if(this.opens == 'left') {
                this.container.css({
                    top: containerTop,
                    right: parentRightEdge - this.element.offset()
                        .left - this.element.outerWidth(),
                    left: 'auto'
                });
                if(this.container.offset().left < 0) {
                    this.container.css({
                        right: 'auto',
                        left: 9
                    });
                }
            } else if(this.opens == 'center') {
                this.container.css({
                    top: containerTop,
                    left: this.element.offset().left -
                        parentOffset.left + this.element.outerWidth() /
                        2 - this.container.outerWidth() / 2,
                    right: 'auto'
                });
                if(this.container.offset().left < 0) {
                    this.container.css({
                        right: 'auto',
                        left: 9
                    });
                }
            } else {
                this.container.css({
                    top: containerTop,
                    left: this.element.offset().left -
                        parentOffset.left,
                    right: 'auto'
                });
                if(this.container.offset().left + this.container.outerWidth() >
                    $(window).width()) {
                    this.container.css({
                        left: 'auto',
                        right: 0
                    });
                }
            }
        },

        toggle: function (e) {
            if(this.element.hasClass('active')) {
                this.hide();
            } else {
                this.show();
            }
        },

        show: function (e) {
            if(this.isShowing) return;

            this.element.addClass('active');
            this.container.show();
            this.move();

            // Create a click proxy that is private to this instance of datepicker, for unbinding
            this._outsideClickProxy = $.proxy(function (e) {
                this.outsideClick(e);
            }, this);
            // Bind global datepicker mousedown for hiding and
            $(document)
                .on('mousedown.daterangepicker', this._outsideClickProxy)
                // also support mobile devices
                .on('touchend.daterangepicker', this._outsideClickProxy)
                // also explicitly play nice with Bootstrap dropdowns, which stopPropagation when clicking them
                .on('click.daterangepicker', '[data-toggle=dropdown]',
                    this._outsideClickProxy)
                // and also close when focus changes to outside the picker (eg. tabbing between controls)
                .on('focusin.daterangepicker', this._outsideClickProxy);

            this.isShowing = true;
            this.element.trigger('show.daterangepicker', this);
        },

        outsideClick: function (e) {
            var target = $(e.target);
            // if the page is clicked anywhere except within the daterangerpicker/button
            // itself then call this.hide()
            if(
                // ie modal dialog fix
                e.type == "focusin" ||
                target.closest(this.element).length ||
                target.closest(this.container).length ||
                target.closest('.calendar-date').length
            ) return;
            this.hide();
        },

        hide: function (e) {
            if(!this.isShowing) return;

            $(document)
                .off('.daterangepicker');

            this.element.removeClass('active');
            this.container.hide();

            if(!this.startDate.isSame(this.oldStartDate) || !this.endDate
                .isSame(this.oldEndDate))
                this.notify();

            this.oldStartDate = this.startDate.clone();
            this.oldEndDate = this.endDate.clone();

            this.isShowing = false;
            this.element.trigger('hide.daterangepicker', this);
        },

        enterRange: function (e) {
            // mouse pointer has entered a range label
            var label = e.target.innerHTML;
            if(label == this.locale.customRangeLabel) {
                this.updateView();
            } else {
                var dates = this.ranges[label],
                    startDate = dates[0].format(this.format),
                    endDate   = dates[1].format(this.format);
                //VC
                //year + 543
                if(this.thai){
                    var _startDate = dates[0].format(this.format).split("/"),
                        _endDate   = dates[0].format(this.format).split("/"),
                        _sdate  = parseInt(_startDate[0]),
                        _edate  = parseInt(_endDate[0]),
                        _smonth = parseInt(_startDate[1]),
                        _emonth = parseInt(_endDate[1]),
                        _syear  = parseInt(_startDate[2]) + 543,
                        _eyear  = parseInt(_endDate[2]) + 543,
                        _startDate = _sdate + "/" + _smonth + "/" + _syear,
                        _endDate   = _sdate + "/" + _smonth + "/" + _syear;
                    
                    startDate = _startDate
                    endDate = _endDate

                }
                this.container.find('input[name=daterangepicker_start]').val(startDate);
                this.container.find('input[name=daterangepicker_end]').val(endDate);
            }
        },

        showCalendars: function () {
            this.container.addClass('show-calendar');
            this.move();
            this.element.trigger('showCalendar.daterangepicker', this);
        },

        hideCalendars: function () {
            this.container.removeClass('show-calendar');
            this.element.trigger('hideCalendar.daterangepicker', this);
        },

        // when a date is typed into the start to end date textboxes
        inputsChanged: function (e) {
            var el = $(e.target);
            var value = el.val();
            //VC
            //if thai style, year - 543
            //TODO fix problem about format
            //this code can only use format like DD/MM/YYYY
            if(this.thai){
                var splitedDate = value.split("/");
                if(splitedDate.length !== 3) return;
                var _day = Number(splitedDate[0]);
                var _month = Number(splitedDate[1]);
                var _year = Number(splitedDate[2]);

                if( ! (
                    Number.isInteger(_day)   && 
                    Number.isInteger(_month) && 
                    Number.isInteger(_year) 
                    )) return;
                
                _year = Math.max(_year - 543, 0);
                value = _day + "/" + _month + "/" + _year;
            }

            var date = moment(value, this.format);
            if(!date.isValid()) return;

            var startDate, endDate;
            if(el.attr('name') === 'daterangepicker_start') {
                startDate = (false !== this.minDate && date.isBefore(
                    this.minDate)) ? this.minDate : date;
                endDate = this.endDate;
            } else {
                startDate = this.startDate;
                endDate = (false !== this.maxDate && date.isAfter(this.maxDate)) ?
                    this.maxDate : date;
            }
            this.setCustomDates(startDate, endDate);
        },

        inputsKeydown: function (e) {
            if(e.keyCode === 13) {
                this.inputsChanged(e);
                this.notify();
            }
        },

        updateInputText: function () {
            var _startDate = this.startDate.format(this.format);
            var _endDate   = this.endDate.format(this.format);
            var _fullDate  = _startDate + this.separator + _endDate;
            
            //VC
            //if thai style, year in main textbox  = year + 543 
            if(this.thai){
                var _sYear  = this.startDate.year()  + 543,
                    _sMonth = this.startDate.month() + 1,
                    _sDay   = this.startDate.date(),
                    _eYear  = this.endDate.year()  + 543,
                    _eMonth = this.endDate.month() + 1,
                    _eDay   = this.endDate.date(),
                    _sDate  = this.pad(_sDay, 2) + "/" + this.pad(_sMonth, 2) + "/" + _sYear,
                    _eDate  = this.pad(_eDay, 2) + "/" + this.pad(_eMonth, 2) + "/" + _eYear;

                    _startDate = _sDate;
                    _endDate   = _eDate;
                    _fullDate  = _sDate + this.separator + _endDate
            }

            if(this.element.is('input') && !this.singleDatePicker) {
                this.element.val(_fullDate);
                this.element.trigger('change');
                this.element.trigger('dateChange', _fullDate);
            } else if(this.element.is('input')) {
                this.element.val(_endDate);
                this.element.trigger('change');
                this.element.trigger('dateChange', _endDate);
            }
        },

        pad: function(n, width, z) {
            z = z || '0';
            n = n + '';
            return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
        },

        clickRange: function (e) {
            var label = e.target.innerHTML;
            this.chosenLabel = label;
            if(label == this.locale.customRangeLabel) {
                this.showCalendars();
            } else {
                var dates = this.ranges[label];

                this.startDate = dates[0];
                this.endDate = dates[1];

                if(!this.timePicker) {
                    this.startDate.startOf('day');
                    this.endDate.endOf('day');
                }

                this.leftCalendar.month.month(this.startDate.month()).year(
                        this.startDate.year()).hour(this.startDate.hour())
                    .minute(this.startDate.minute());
                this.rightCalendar.month.month(this.endDate.month()).year(
                    this.endDate.year()).hour(this.endDate.hour()).minute(
                    this.endDate.minute());
                this.updateCalendars();

                this.updateInputText();

                this.hideCalendars();
                this.hide();
                this.element.trigger('apply.daterangepicker', this);
                //VC
                this.valid();
            }
        },

        clickPrev: function (e) {
            var cal = $(e.target).parents('.calendar');
            if(cal.hasClass('left')) {
                this.leftCalendar.month.subtract(1, 'month');
            } else {
                this.rightCalendar.month.subtract(1, 'month');
            }
            this.updateCalendars();
        },

        clickNext: function (e) {
            var cal = $(e.target).parents('.calendar');
            if(cal.hasClass('left')) {
                this.leftCalendar.month.add(1, 'month');
            } else {
                this.rightCalendar.month.add(1, 'month');
            }
            this.updateCalendars();
        },

        hoverDate: function (e) {
            var title = $(e.target).attr('data-title');
            var row = title.substr(1, 1);
            var col = title.substr(3, 1);
            var cal = $(e.target).parents('.calendar');

            var leftDate  = this.leftCalendar.calendar[row][col].format(this.format);
            var rightDate = this.rightCalendar.calendar[row][col].format(this.format);

            //VC
            //if thai style, year in 2 textboxs = year + 543
            if(this.thai){
                var _lYear  = this.leftCalendar.calendar[row][col].year()  + 543,
                    _lMonth = this.leftCalendar.calendar[row][col].month() + 1,
                    _lDay   = this.leftCalendar.calendar[row][col].date(),
                    _rYear  = this.rightCalendar.calendar[row][col].year()  + 543,
                    _rMonth = this.rightCalendar.calendar[row][col].month() + 1,
                    _rDay   = this.rightCalendar.calendar[row][col].date(),
                    _lDate  = _lDay + "/" + _lMonth + "/" + _lYear,
                    _rDate  = _rDay + "/" + _rMonth + "/" + _rYear;
                
                //VC
                //TODO fix this problem [can't use format]
                //ignore this.format 
                leftDate  = _lDate;
                rightDate = _rDate;
            }

            if(cal.hasClass('left')) {
                this.container.find('input[name=daterangepicker_start]').val(leftDate);
            } else {
                this.container.find('input[name=daterangepicker_end]').val(rightDate);
            }
        },

        setCustomDates: function (startDate, endDate) {
            this.chosenLabel = this.locale.customRangeLabel;
            if(startDate.isAfter(endDate)) {
                var difference = this.endDate.diff(this.startDate);
                endDate = moment(startDate).add(difference, 'ms');
                if(this.maxDate && endDate.isAfter(this.maxDate)) {
                    endDate = this.maxDate.clone();
                }
            }
            this.startDate = startDate;
            this.endDate = endDate;

            this.updateView();
            this.updateCalendars();
        },

        clickDate: function (e) {
            var title = $(e.target).attr('data-title');
            var row = title.substr(1, 1);
            var col = title.substr(3, 1);
            var cal = $(e.target).parents('.calendar');

            var startDate, endDate;
            if(cal.hasClass('left')) {
                startDate = this.leftCalendar.calendar[row][col];
                endDate = this.endDate;
                if(typeof this.dateLimit === 'object') {
                    var maxDate = moment(startDate).add(this.dateLimit).startOf(
                        'day');
                    if(endDate.isAfter(maxDate)) {
                        endDate = maxDate;
                    }
                }
            } else {
                startDate = this.startDate;
                endDate = this.rightCalendar.calendar[row][col];
                if(typeof this.dateLimit === 'object') {
                    var minDate = moment(endDate).subtract(this.dateLimit)
                        .startOf('day');
                    if(startDate.isBefore(minDate)) {
                        startDate = minDate;
                    }
                }
            }

            if(this.singleDatePicker && cal.hasClass('left')) {
                endDate = startDate.clone();
            } else if(this.singleDatePicker && cal.hasClass('right')) {
                startDate = endDate.clone();
            }

            cal.find('td').removeClass('active');

            $(e.target).addClass('active');

            this.setCustomDates(startDate, endDate);

            if(!this.timePicker)
                endDate.endOf('day');

            if(this.singleDatePicker && !this.timePicker)
                this.clickApply();
        },

        clickApply: function (e) {
            this.updateInputText();
            this.hide();
            this.element.trigger('apply.daterangepicker', this);
            //VC
            this.valid();
        },

        clickCancel: function (e) {
            this.startDate = this.oldStartDate;
            this.endDate = this.oldEndDate;
            this.chosenLabel = this.oldChosenLabel;
            this.updateView();
            this.updateCalendars();
            this.hide();
            this.element.trigger('cancel.daterangepicker', this);
        },

        updateMonthYear: function (e) {
            var isLeft = $(e.target).closest('.calendar').hasClass(
                    'left'),
                leftOrRight = isLeft ? 'left' : 'right',
                cal = this.container.find('.calendar.' + leftOrRight);

            // Month must be Number for new moment versions
            var month = parseInt(cal.find('.monthselect').val(), 10);
            var year = cal.find('.yearselect').val();

            if(!isLeft && !this.singleDatePicker) {
                if(year < this.startDate.year() || (year == this.startDate
                        .year() && month < this.startDate.month())) {
                    month = this.startDate.month();
                    year = this.startDate.year();
                }
            }

            if(this.minDate) {
                if(year < this.minDate.year() || (year == this.minDate.year() &&
                        month < this.minDate.month())) {
                    month = this.minDate.month();
                    year = this.minDate.year();
                }
            }

            if(this.maxDate) {
                if(year > this.maxDate.year() || (year == this.maxDate.year() &&
                        month > this.maxDate.month())) {
                    month = this.maxDate.month();
                    year = this.maxDate.year();
                }
            }

            this[leftOrRight + 'Calendar'].month.month(month).year(year);
            this.updateCalendars();
        },

        updateTime: function (e) {

            var cal = $(e.target).closest('.calendar'),
                isLeft = cal.hasClass('left');

            var hour = parseInt(cal.find('.hourselect').val(), 10);
            var minute = parseInt(cal.find('.minuteselect').val(), 10);
            var second = 0;

            if(this.timePickerSeconds) {
                second = parseInt(cal.find('.secondselect').val(), 10);
            }

            if(this.timePicker12Hour) {
                var ampm = cal.find('.ampmselect').val();
                if(ampm === 'PM' && hour < 12)
                    hour += 12;
                if(ampm === 'AM' && hour === 12)
                    hour = 0;
            }

            if(isLeft) {
                var start = this.startDate.clone();
                start.hour(hour);
                start.minute(minute);
                start.second(second);
                this.startDate = start;
                this.leftCalendar.month.hour(hour).minute(minute).second(
                    second);
                if(this.singleDatePicker)
                    this.endDate = start.clone();
            } else {
                var end = this.endDate.clone();
                end.hour(hour);
                end.minute(minute);
                end.second(second);
                this.endDate = end;
                if(this.singleDatePicker)
                    this.startDate = end.clone();
                this.rightCalendar.month.hour(hour).minute(minute).second(
                    second);
            }

            this.updateView();
            this.updateCalendars();
        },

        updateCalendars: function () {
            this.leftCalendar.calendar = this.buildCalendar(this.leftCalendar
                .month.month(), this.leftCalendar.month.year(), this
                .leftCalendar.month.hour(), this.leftCalendar.month.minute(),
                this.leftCalendar.month.second(), 'left');
            this.rightCalendar.calendar = this.buildCalendar(this.rightCalendar
                .month.month(), this.rightCalendar.month.year(),
                this.rightCalendar.month.hour(), this.rightCalendar.month
                .minute(), this.rightCalendar.month.second(),
                'right');
            this.container.find('.calendar.left').empty().html(this.renderCalendar(
                this.leftCalendar.calendar, this.startDate, this
                .minDate, this.maxDate, 'left'));
            this.container.find('.calendar.right').empty().html(this.renderCalendar(
                this.rightCalendar.calendar, this.endDate, this.singleDatePicker ?
                this.minDate : this.startDate, this.maxDate,
                'right'));

            this.container.find('.ranges li').removeClass('active');
            var customRange = true;
            var i = 0;
            for(var range in this.ranges) {
                if(this.timePicker) {
                    if(this.startDate.isSame(this.ranges[range][0]) &&
                        this.endDate.isSame(this.ranges[range][1])) {
                        customRange = false;
                        this.chosenLabel = this.container.find(
                                '.ranges li:eq(' + i + ')')
                            .addClass('active').html();
                    }
                } else {
                    //ignore times when comparing dates if time picker is not enabled
                    if(this.startDate.format('YYYY-MM-DD') == this.ranges[
                            range][0].format('YYYY-MM-DD') && this.endDate
                        .format('YYYY-MM-DD') == this.ranges[range][1].format(
                            'YYYY-MM-DD')) {
                        customRange = false;
                        this.chosenLabel = this.container.find(
                                '.ranges li:eq(' + i + ')')
                            .addClass('active').html();
                    }
                }
                i++;
            }
            if(customRange) {
                this.chosenLabel = this.container.find('.ranges li:last')
                    .addClass('active').html();
                this.showCalendars();
            }
        },

        buildCalendar: function (month, year, hour, minute, second, side) {
            var daysInMonth = moment([year, month]).daysInMonth();
            var firstDay = moment([year, month, 1]);
            var lastDay = moment([year, month, daysInMonth]);
            var lastMonth = moment(firstDay).subtract(1, 'month').month();
            var lastYear = moment(firstDay).subtract(1, 'month').year();

            var daysInLastMonth = moment([lastYear, lastMonth]).daysInMonth();

            var dayOfWeek = firstDay.day();

            var i;

            //initialize a 6 rows x 7 columns array for the calendar
            var calendar = [];
            calendar.firstDay = firstDay;
            calendar.lastDay = lastDay;

            for(i = 0; i < 6; i++) {
                calendar[i] = [];
            }

            //populate the calendar with date objects
            var startDay = daysInLastMonth - dayOfWeek + this.locale.firstDay +
                1;
            if(startDay > daysInLastMonth)
                startDay -= 7;

            if(dayOfWeek == this.locale.firstDay)
                startDay = daysInLastMonth - 6;

            var curDate = moment([lastYear, lastMonth, startDay, 12,
                minute, second
            ]).utcOffset(this.timeZone);

            var col, row;
            for(i = 0, col = 0, row = 0; i < 42; i++, col++, curDate =
                moment(curDate).add(24, 'hour')) {
                if(i > 0 && col % 7 === 0) {
                    col = 0;
                    row++;
                }
                calendar[row][col] = curDate.clone().hour(hour);
                curDate.hour(12);

                if(this.minDate && calendar[row][col].format(
                        'YYYY-MM-DD') == this.minDate.format(
                        'YYYY-MM-DD') && calendar[row][col].isBefore(
                        this.minDate) && side == 'left') {
                    calendar[row][col] = this.minDate.clone();
                }

                if(this.maxDate && calendar[row][col].format(
                        'YYYY-MM-DD') == this.maxDate.format(
                        'YYYY-MM-DD') && calendar[row][col].isAfter(this
                        .maxDate) && side == 'right') {
                    calendar[row][col] = this.maxDate.clone();
                }

            }

            return calendar;
        },

        renderDropdowns: function (selected, minDate, maxDate) {
            var currentMonth = selected.month();
            var currentYear = selected.year();
            //VC
            //render prev 50 years and render next 5 year in combobox
            var maxYear = (maxDate && maxDate.year()) || (currentYear +
                5);
            var minYear = (minDate && minDate.year()) || (currentYear -
                100);

            var monthHtml = '<select class="ui compact selection dropdown monthselect">';
            var inMinYear = currentYear == minYear;
            var inMaxYear = currentYear == maxYear;

            for(var m = 0; m < 12; m++) {
                if((!inMinYear || m >= minDate.month()) && (!inMaxYear ||
                        m <= maxDate.month())) {
                    monthHtml += "<option value='" + m + "'" +
                        (m === currentMonth ? " selected='selected'" :
                            "") +
                        ">" + this.locale.monthNames[m] + "</option>";
                }
            }
            monthHtml += "</select>";

            var yearHtml = '<select class="ui compact selection dropdown yearselect">';

            for(var y = minYear; y <= maxYear; y++) {
                yearHtml += '<option value="' + y + '"' +
                (y === currentYear ? ' selected="selected"' : '');
                
                //VC
                //if thai style year + 543
                if(this.thai){
                    yearHtml += '>' + (y + 543) + '</option>';
                }
                else{
                    yearHtml += '>' + y + '</option>';
                }
            }

            yearHtml += '</select>';

            return monthHtml + yearHtml;
        },

        renderCalendar: function (calendar, selected, minDate, maxDate, side) {

            var html = '<div class="calendar-date">';
            html += '<table class="table-condensed">';
            html += '<thead>';
            html += '<tr>';

            // add empty cell for week number
            if(this.showWeekNumbers)
                html += '<th></th>';

            if(!minDate || minDate.isBefore(calendar.firstDay)) {
                html +=
                    '<th class="prev available"><i class="left arrow icon"></i></th>';
            } else {
                html += '<th></th>';
            }

            //VC
            //date Html is a header section which shows month and year
            //ex. พฤศจิกายน 2016 (in case no dropdown option)
            var dateHtml = this.locale.monthNames[calendar[1][1].month()] +
                calendar[1][1].format(" YYYY");
            
            if(this.showDropdowns) {
                dateHtml = this.renderDropdowns(calendar[1][1], minDate,
                    maxDate);
            }

            html += '<th colspan="5" class="month">' + dateHtml +
                '</th>';
            if(!maxDate || maxDate.isAfter(calendar.lastDay)) {
                html +=
                    '<th class="next available"><i class="right arrow icon"></i></th>';
            } else {
                html += '<th></th>';
            }

            html += '</tr>';
            html += '<tr>';

            // add week number label
            if(this.showWeekNumbers)
                html += '<th class="week">' + this.locale.weekLabel +
                '</th>';

            $.each(this.locale.daysOfWeek, function (index, dayOfWeek) {
                html += '<th>' + dayOfWeek + '</th>';
            });

            html += '</tr>';
            html += '</thead>';
            html += '<tbody>';

            for(var row = 0; row < 6; row++) {
                html += '<tr>';

                // add week number
                if(this.showWeekNumbers)
                    html += '<td class="week">' + calendar[row][0].week() +
                    '</td>';

                for(var col = 0; col < 7; col++) {
                    var cname = 'available ';
                    cname += (calendar[row][col].month() == calendar[1][
                        1
                    ].month()) ? '' : 'off';

                    if((minDate && calendar[row][col].isBefore(minDate,
                            'day')) || (maxDate && calendar[row][col].isAfter(
                            maxDate, 'day'))) {
                        cname = ' off disabled ';
                    } else if(calendar[row][col].format('YYYY-MM-DD') ==
                        selected.format('YYYY-MM-DD')) {
                        cname += ' active ';
                        if(calendar[row][col].format('YYYY-MM-DD') ==
                            this.startDate.format('YYYY-MM-DD')) {
                            cname += ' start-date ';
                        }
                        if(calendar[row][col].format('YYYY-MM-DD') ==
                            this.endDate.format('YYYY-MM-DD')) {
                            cname += ' end-date ';
                        }
                    } else if(calendar[row][col] >= this.startDate &&
                        calendar[row][col] <= this.endDate) {
                        cname += ' in-range ';
                        if(calendar[row][col].isSame(this.startDate)) {
                            cname += ' start-date ';
                        }
                        if(calendar[row][col].isSame(this.endDate)) {
                            cname += ' end-date ';
                        }
                    }

                    var title = 'r' + row + 'c' + col;
                    html += '<td class="' + cname.replace(/\s+/g, ' ').replace(
                            /^\s?(.*?)\s?$/, '$1') + '" data-title="' +
                        title + '">' + calendar[row][col].date() +
                        '</td>';
                }
                html += '</tr>';
            }

            html += '</tbody>';
            html += '</table>';
            html += '</div>';

            var i;
            if(this.timePicker) {

                html += '<div class="calendar-time">';
                html += '<select class="ui compact upward selection dropdown hourselect">';

                // Disallow selections before the minDate or after the maxDate
                var min_hour = 0;
                var max_hour = 23;

                if(minDate && (side == 'left' || this.singleDatePicker) &&
                    selected.format('YYYY-MM-DD') == minDate.format(
                        'YYYY-MM-DD')) {
                    min_hour = minDate.hour();
                    if(selected.hour() < min_hour)
                        selected.hour(min_hour);
                    if(this.timePicker12Hour && min_hour >= 12 &&
                        selected.hour() >= 12)
                        min_hour -= 12;
                    if(this.timePicker12Hour && min_hour == 12)
                        min_hour = 1;
                }

                if(maxDate && (side == 'right' || this.singleDatePicker) &&
                    selected.format('YYYY-MM-DD') == maxDate.format(
                        'YYYY-MM-DD')) {
                    max_hour = maxDate.hour();
                    if(selected.hour() > max_hour)
                        selected.hour(max_hour);
                    if(this.timePicker12Hour && max_hour >= 12 &&
                        selected.hour() >= 12)
                        max_hour -= 12;
                }

                var start = 0;
                var end = 23;
                var selected_hour = selected.hour();
                if(this.timePicker12Hour) {
                    start = 1;
                    end = 12;
                    if(selected_hour >= 12)
                        selected_hour -= 12;
                    if(selected_hour === 0)
                        selected_hour = 12;
                }

                for(i = start; i <= end; i++) {

                    if(i == selected_hour) {
                        html += '<option value="' + i +
                            '" selected="selected">' + i + '</option>';
                    } else if(i < min_hour || i > max_hour) {
                        html += '<option value="' + i +
                            '" disabled="disabled" class="disabled">' +
                            i + '</option>';
                    } else {
                        html += '<option value="' + i + '">' + i +
                            '</option>';
                    }
                }

                html += '</select> : ';

                html += '<select class="ui compact upward selection dropdown minuteselect">';

                // Disallow selections before the minDate or after the maxDate
                var min_minute = 0;
                var max_minute = 59;

                if(minDate && (side == 'left' || this.singleDatePicker) &&
                    selected.format('YYYY-MM-DD h A') == minDate.format(
                        'YYYY-MM-DD h A')) {
                    min_minute = minDate.minute();
                    if(selected.minute() < min_minute)
                        selected.minute(min_minute);
                }

                if(maxDate && (side == 'right' || this.singleDatePicker) &&
                    selected.format('YYYY-MM-DD h A') == maxDate.format(
                        'YYYY-MM-DD h A')) {
                    max_minute = maxDate.minute();
                    if(selected.minute() > max_minute)
                        selected.minute(max_minute);
                }

                for(i = 0; i < 60; i += this.timePickerIncrement) {
                    var num = i;
                    if(num < 10)
                        num = '0' + num;
                    if(i == selected.minute()) {
                        html += '<option value="' + i +
                            '" selected="selected">' + num + '</option>';
                    } else if(i < min_minute || i > max_minute) {
                        html += '<option value="' + i +
                            '" disabled="disabled" class="disabled">' +
                            num + '</option>';
                    } else {
                        html += '<option value="' + i + '">' + num +
                            '</option>';
                    }
                }

                html += '</select> ';

                if(this.timePickerSeconds) {
                    html += ': <select class="ui compact upward selection dropdown secondselect">';

                    for(i = 0; i < 60; i += this.timePickerIncrement) {
                        var numbr = i;
                        if(numbr < 10)
                            numbr = '0' + numbr;
                        if(i == selected.second()) {
                            html += '<option value="' + i +
                                '" selected="selected">' + numbr +
                                '</option>';
                        } else {
                            html += '<option value="' + i + '">' + numbr +
                                '</option>';
                        }
                    }

                    html += '</select>';
                }

                if(this.timePicker12Hour) {
                    html += '<select class="ui compact upward selection dropdown ampmselect">';

                    // Disallow selection before the minDate or after the maxDate
                    var am_html = '';
                    var pm_html = '';

                    if(minDate && (side == 'left' || this.singleDatePicker) &&
                        selected.format('YYYY-MM-DD') == minDate.format(
                            'YYYY-MM-DD') && minDate.hour() >= 12) {
                        am_html =
                            ' disabled="disabled" class="disabled"';
                    }

                    if(maxDate && (side == 'right' || this.singleDatePicker) &&
                        selected.format('YYYY-MM-DD') == maxDate.format(
                            'YYYY-MM-DD') && maxDate.hour() < 12) {
                        pm_html =
                            ' disabled="disabled" class="disabled"';
                    }

                    if(selected.hour() >= 12) {
                        html += '<option value="AM"' + am_html +
                            '>AM</option><option value="PM" selected="selected"' +
                            pm_html + '>PM</option>';
                    } else {
                        html += '<option value="AM" selected="selected"' +
                            am_html + '>AM</option><option value="PM"' +
                            pm_html + '>PM</option>';
                    }
                    html += '</select>';
                }

                html += '</div>';

            }

            return html;

        },

        remove: function () {

            this.container.remove();
            this.element.off('.daterangepicker');
            this.element.removeData('daterangepicker');

        },

        updateDateText: function(){
            this.updateFromControl();
        }

    };

    $.fn.daterangepicker = function (options, cb, valid, inValid) {
        this.each(function () {
            var el = $(this);
            if(el.data('daterangepicker'))
                el.data('daterangepicker').remove();
            el.data('daterangepicker', new DateRangePicker(el,
                options, cb, valid, inValid));
        });
        return this;
    };

}));
