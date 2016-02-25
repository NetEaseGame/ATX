// common functions
$(function() {
    if (!String.prototype.format) {
        String.prototype.format = function() {
            var args = arguments;
            return this.replace(/{(\d+)}/g, function(match, number) {
                return typeof args[number] != 'undefined' ? args[number] : match;
            });
        };
    }
});

$(function() {
    // Create the chart
    var setting = {
        rangeSelector: {
            selected: 1,
            enabled: false,
        },
        title: {
            text: 'CPU'
        },
        xAxis: {
            lineColor: '#000',
            gridLineWidth: 1,
            labels: {
                formatter: function() {
                    var minute = parseInt(this.value / 60, 10);
                    var hour = parseInt(this.value / 3600, 10);
                    return (hour === 0 ? "" : hour + "h") + (minute === 0 ? "" : minute + "m") + (this.value % 60 + "s");
                }
            },
        },
        yAxis: {
            minorTickInterval: 'auto',
            lineColor: '#000',
            lineWidth: 1,
            tickWidth: 1,
            tickColor: '#000',
            labels: {
                formatter: function() {
                    return this.value + '%';
                }
            },
            max: 100,
            min: 0,
        },
        chart: {
            type: 'spline',
        },
        navigator: {
            enabled: false,
        },
        scrollbar: {
            enabled: false,
        },
        series: []
    };
    var updateGraph = function(role) {
        var selector = "div.highstock[role={0}]".format(role);
        var $stock = $(selector);
        var max = $stock.attr("max");
        var unit = $stock.attr("unit") || "";
        var yAxis = {
            minorTickInterval: 'auto',
            lineColor: '#000',
            lineWidth: 1,
            tickWidth: 1,
            tickColor: '#000',
            labels: {
                formatter: function() {
                    return this.value + unit;
                }
            },
            min: 0
        };
        if (max) {
            yAxis["max"] = parseInt(max, 10);
        }
        $.getJSON('highstock-data-{0}.json'.format(role), function(result) {
            $stock.highcharts('StockChart', $.extend(setting, {
                title: {
                    text: role
                },
                series: [{
                    name: '',
                    data: result.data,
                }],
                yAxis: yAxis
            }));
        });
    };

    $("div.highstock").each(function() {
        var role = $(this).attr("role");
        //var role = "cpu";
        updateGraph(role);
    });
});