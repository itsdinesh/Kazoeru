let chart;

function requestData()
{
    // Ajax call to get the Data from Flask
    let requests = $.get('/data');
    requests.done(function (result)
    {
        let series = chart.series[0],
            shift = series.data.length > 20;

        // add the point
        chart.series[0].addPoint(result, true, shift);

        // call it again after three second
        setTimeout(requestData, 3000);
    });
}

// Define Highcharts Chart
$(document).ready(function() {
    chart = new Highcharts.Chart({
        chart: {
            renderTo: 'data-container',
            defaultSeriesType: 'spline',
            events: {
                load: requestData
            }
        },
        title: {
            text: 'Live Crowd Count'
        },
        xAxis: {
            title: {
                text: 'Current Time'
            },
            type: 'datetime',
            tickPixelInterval: 150,
            maxZoom: 20 * 1000,
        },
        yAxis: {
            title: {
                text: 'Number of People'
            }
        },
        series: [{
            name: 'People',
            data: []
        }]
    });
});
