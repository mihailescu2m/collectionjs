
/*
# Copyright (C) 2013 Marian Mihailescu
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; only version 2 of the License is applicable.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Authors:
#   Marian Mihailescu <mihailescu2m at gmail.com>
*/

jQuery(document).ready(function ($) {
	// set some defaults
	CollectionJS = {};
	CollectionJS.theme = {
		global: { useUTC: false },
		credits: { enabled: false },
		navigation: { buttonOptions: { theme: { fill: 'whitesmoke', borderRadius: 0, states: { hover: { stroke: 'grey', fill: 'gainsboro', r: 0 }, select: { stroke: 'grey', fill: 'gainsboro', r: 0 } } } } },
		title: { style: { color: 'black', font: 'bold 14px "Trebuchet MS", Verdana, sans-serif' } },
		yAxis: { title: { style: { color: '#333', font: '12px "Trebuchet MS", Verdana, sans-serif' } }, lineWidth: 1, lineColor: 'grey', tickPixelInterval: 36, minorTickPixelInterval: 36, minorTickInterval: 'auto', gridLineColor: '#ffb2b2', gridLineDashStyle: 'ShortDot' },
		xAxis: { lineWidth: 1, lineColor: 'grey', minPadding: 0, type: 'datetime', minorTickInterval: 'auto', gridLineWidth: 1, gridLineColor: '#ffb2b2', gridLineDashStyle: 'ShortDot' },
		legend: { /*layout: 'vertical', align: 'middle', borderWidth: 0, x: 10, */ backgroundColor: 'white', borderRadius: 0, borderColor: 'grey', itemStyle: { color: '#333', font: '12px "Trebuchet MS", Verdana, sans-serif' } },
		chart: { zoomType: 'x', alignTicks: false, backgroundColor: 'whitesmoke', plotBackgroundColor: 'white', borderRadius: 0, borderWidth: 1, borderColor: 'gainsboro', spacingLeft: 0, spacingBottom: 10, spacingRight: 15 },
		plotOptions: { line: { marker: { enabled: false, states: { hover: { enabled: false } } }, shadow: false, step: true, lineWidth: 1, states: { hover: { lineWidth: 2 } } }, area: { marker: { enabled: false, states: { hover: { enabled: false } } }, shadow: false, step: true, lineWidth: 1, states: { hover: { lineWidth: 1 } } } },
		tooltip: { crosshairs: { color: 'grey', dashStyle: 'solid' }, shadow: false, valueDecimals: 2 }
	};
	Highcharts.setOptions(CollectionJS.theme);

	// render all charts defined in divs
	renderCharts();

	
}); // end main function


									
// function to update chart data
function updateChart(container, start) {
	var url = container.data("url") + ';begin=' + start;
	var chart = container.highcharts();
	chart.showLoading();
	$.ajax({
		type: "GET",
		url: url,
		dataType: 'json',
		success: function (data) {
			for (var i = 0; i < data.series.length; i++) {
				chart.series[i].update(data.series[i], false); // update series, but don't redraw yet
			}
			chart.hideLoading();
			chart.redraw(); // redraw chart
		}
	}); // end ajax call
}

// function to load the charts
function renderCharts() {
	$('.highchart').each(function () {
		// start the spinner
		var spinner = new Spinner({ lines: 11, length: 10, width: 7, radius: 15, corners: 1, rotate: 0, direction: 1, color: '#000', speed: 1, trail: 50, shadow: false, hwaccel: true, className: 'spinner', zIndex: 2e9, top: 'auto', left: 'auto' }).spin(this);
		// spinner will be replaced by the chart when loaded...
		var	container = $(this);
		var url = container.data("url") + ';begin=' + container.data("start");
		// fetch data and display chart
		$.ajax({
			type: "GET",
			url: url,
			dataType: 'json',
			success: function (data) {
				// add buttons for time intervals
				data.exporting = {
					buttons: {
						hourly: { text: '1h', align: 'left', x: 10, onclick: function () { updateChart($(this.container).closest('.highchart'), -3600); } },
						halfdaily: { text: '6h', align: 'left', x: 40, onclick: function () { updateChart($(this.container).closest('.highchart'), -21600); } },
						daily: { text: '1d', align: 'left', x: 70, onclick: function () { updateChart($(this.container).closest('.highchart'), -86400); } },
						weekly: { text: '1w', align: 'left', x: 100, onclick: function () { updateChart($(this.container).closest('.highchart'), -604800); } },
						monthly: { text: '1m', align: 'left', x: 130, onclick: function () { updateChart($(this.container).closest('.highchart'), -2678400); } },
						yearly: { text: '1y', align: 'left', x: 160, onclick: function () { updateChart($(this.container).closest('.highchart'), -31622400); }}
					}
				}
				// create the charts options from the data received, button intervals, and custom options from 'data-options' settings
				var options = $.extend({}, data, container.data("options"));
				container.highcharts(options);
			}
		}); // end ajax call
	}); // end each
}; // end document ready function

