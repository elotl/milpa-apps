// Dear future person.  I have no idea how to do frontend stuff. If
// you can make this better, please do so.
function refreshChart() {
    var resolutionText = $('#resolutionGroup > .active')[0].innerText;
    var chartTypeText = $('#chartTypeGroup').find('.active')[0].innerText;
    var groupByText = $('#groupByGroup').find('.active')[0].innerText;
    var selectorText = $('#selectorInput')[0].value;
    var dates = getDates();
    var startDateStr = dates['startDateStr'];
    var endDateStr = dates['endDateStr'];
    var params = {
	resolution: resolutionText.trim().toLowerCase(),
	chartType: chartTypeText.trim().toLowerCase(),
	groupBy: groupByText.trim().toLowerCase(),
	startDate: startDateStr,
	endDate: endDateStr,
	selector: selectorText,
    }

    var query = $.param(params);
    window.location.href = "/details?" + query;
}

function getDates() {
    var startDateStr = $('#startDate')[0].value;
    var endDateStr = $('#endDate')[0].value;
    return {
	startDateStr: startDateStr,
	endDateStr: endDateStr,
    }
}

$(function() {
    // get start and end date from hidden div
    var dates = getDates()
    var off = (new Date()).getTimezoneOffset();
    // note: moment is a date library that is required by the
    // datepicker we use that because the JS date.parse method moves
    // us to UCT and then building a date out of that, moves us back 8
    // hours from there.
    var startDateVal = new Date(moment(dates.startDateStr))
    var endDateVal = new Date(moment(dates.endDateStr))
    $('#dateRange').daterangepicker({
	"startDate": startDateVal,
	"endDate": endDateVal,
	"opens": "left"
    })

    $("#applySelector").click(function(e){
	refreshChart();
    });

    $("#resolutionGroup > button.btn").on("click", function(){
	$('#resolutionGroup > .btn').removeClass('active')
	this.classList.add("active");
	refreshChart()
    });

    $(".groupByClass").click(function(e){
	$('.groupByClass').removeClass('active')
	this.classList.add("active");
	refreshChart()
    });

    $(".chartTypeClass").click(function(e){
	$('.chartTypeClass').removeClass('active')
	this.classList.add("active");
	refreshChart()
    });

    $('#dateRange').on('apply.daterangepicker', function(ev, picker) {
	$('#startDate')[0].value = picker.startDate.format('YYYY-MM-DD')
	$('#endDate')[0].value = picker.endDate.format('YYYY-MM-DD')
	refreshChart()
    });
});
