from itertools import cycle

colors = [
    'rgba(54, 162, 235, 1)',
    'rgba(255,99,132,1)',
    'rgba(255, 206, 86, 1)',
    'rgba(75, 192, 192, 1)',
    'rgba(153, 102, 255, 1)',
    'rgba(255, 159, 64, 1)',
    'rgba(65, 191, 65, 1)',
    'rgba(140, 86, 75, 1)'
    'rgba(227, 119, 194, 1)',
    'rgba(127, 127, 127, 1)',
    'rgba(188, 189, 34, 1)',
]


def make_standard_chart(xvals, yval_sets, yval_names, charttype):
    datasets = []
    fill = True
    if charttype == 'line':
        fill = False
    stacked = False
    if charttype == 'stacked':
        charttype = 'bar'
        stacked = True

    for yvals, yval_name, color in zip(yval_sets, yval_names, cycle(colors)):
        item = {
            # 'lineTension': 4,
            'data': yvals,
            'label': yval_name,
            'backgroundColor': color,
            'borderColor': color,
            'fill': fill,
        }
        datasets.append(item)
    return make_chartspec(charttype, xvals, datasets, stacked)


def make_donut_chart(xvals, yval_sets, yval_names):
    xvals = []
    yvals = []
    datasets = []
    for yval_set, yval_name in zip(yval_sets, yval_names):
        xvals.append(yval_name)
        yvals.append(yval_set[0])
    datasets = [{
            'data': yvals,
            'backgroundColor': colors,
            'borderColor': colors,
            'fill': True,
        }]
    return make_chartspec('doughnut', xvals, datasets, axes=False)


def make_chartspec(charttype, xvals, datasets, stacked=False, axes=True):
    chartspec = {
        'type': charttype,
        'data': {
            'labels': xvals,
            'datasets': datasets,
        },
        'options': {
            'legend': {
                'display': True
            }
        }
    }
    if axes:
        chartspec['options']['scales'] = {
            'xAxes': [{
                'stacked': stacked,
                'ticks': {
                    'beginAtZero': True
                }
            }],
            'yAxes': [{
                'stacked': stacked,
                'ticks': {
                    'beginAtZero': True,
                }
            }]
        }
    return chartspec
