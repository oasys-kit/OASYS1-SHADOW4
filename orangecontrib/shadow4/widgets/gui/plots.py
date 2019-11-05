
from oasys.widgets import gui as oasysgui


def plot_data1D(x, y,
                title="", xtitle="", ytitle="",
                log_x=False, log_y=False, color='blue', replace=True, control=False,
                xrange=None, yrange=None, symbol=''):



    plot_widget_id = oasysgui.plotWindow(parent=None,
                                         backend=None,
                                         resetzoom=True,
                                         autoScale=False,
                                         logScale=True,
                                         grid=True,
                                         curveStyle=True,
                                         colormap=False,
                                         aspectRatio=False,
                                         yInverted=False,
                                         copy=True,
                                         save=True,
                                         print_=True,
                                         control=control,
                                         position=True,
                                         roi=False,
                                         mask=False,
                                         fit=False)


    plot_widget_id.setDefaultPlotLines(True)
    plot_widget_id.setActiveCurveColor(color='blue')
    plot_widget_id.setGraphXLabel(xtitle)
    plot_widget_id.setGraphYLabel(ytitle)


    plot_widget_id.addCurve(x, y, title, symbol=symbol, color=color, xlabel=xtitle, ylabel=ytitle, replace=replace)  # '+', '^', ','

    if not xtitle is None: plot_widget_id.setGraphXLabel(xtitle)
    if not ytitle is None: plot_widget_id.setGraphYLabel(ytitle)
    if not title is None:  plot_widget_id.setGraphTitle(title)

    plot_widget_id.resetZoom()
    plot_widget_id.replot()
    plot_widget_id.setActiveCurve(title)


    plot_widget_id.setXAxisLogarithmic(log_x)
    plot_widget_id.setYAxisLogarithmic(log_y)


    if xrange is not None:
        plot_widget_id.setGraphXLimits(xrange[0] ,xrange[1])
    if yrange is not None:
        plot_widget_id.setGraphYLimits(yrange[0] ,yrange[1])

    if min(y) < 0:
        if log_y:
            plot_widget_id.setGraphYLimits(min(y ) *1.2, max(y ) *1.2)
        else:
            plot_widget_id.setGraphYLimits(min(y ) *1.01, max(y ) *1.01)
    else:
        if log_y:
            plot_widget_id.setGraphYLimits(min(y), max(y ) *1.2)
        else:
            plot_widget_id.setGraphYLimits(min(y ) *0.99, max(y ) *1.01)

    return plot_widget_id

