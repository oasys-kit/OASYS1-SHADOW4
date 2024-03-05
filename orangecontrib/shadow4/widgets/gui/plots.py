import numpy
from oasys.widgets import gui as oasysgui
from silx.gui.plot.StackView import StackViewMainWindow
from silx.gui.plot import Plot2D

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

def plot_data2D(data2D, dataX, dataY, title="", xtitle="", ytitle=""):

    origin = (dataX[0],dataY[0])
    scale = (dataX[1]-dataX[0],dataY[1]-dataY[0])

    data_to_plot = data2D.T

    colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

    plot_widget_id = Plot2D()
    plot_widget_id.resetZoom()
    plot_widget_id.setXAxisAutoScale(True)
    plot_widget_id.setYAxisAutoScale(True)
    plot_widget_id.setGraphGrid(False)
    plot_widget_id.setKeepDataAspectRatio(True)
    plot_widget_id.yAxisInvertedAction.setVisible(False)
    plot_widget_id.setXAxisLogarithmic(False)
    plot_widget_id.setYAxisLogarithmic(False)
    plot_widget_id.getMaskAction().setVisible(False)
    plot_widget_id.getRoiAction().setVisible(False)
    plot_widget_id.getColormapAction().setVisible(False)
    plot_widget_id.setKeepDataAspectRatio(False)
    plot_widget_id.addImage(numpy.array(data_to_plot),
                                                 legend="",
                                                 scale=scale,
                                                 origin=origin,
                                                 colormap=colormap,
                                                 replace=True)

    plot_widget_id.setActiveImage("")
    plot_widget_id.setGraphXLabel(xtitle)
    plot_widget_id.setGraphYLabel(ytitle)
    plot_widget_id.setGraphTitle(title)

    return plot_widget_id

def plot_data3D(data3D, dataE, dataX, dataY,
                title="", xtitle="", ytitle="",
                callback_for_title=(lambda idx: "")):

    xmin = numpy.min(dataX)
    xmax = numpy.max(dataX)
    ymin = numpy.min(dataY)
    ymax = numpy.max(dataY)


    stepX = dataX[1]-dataX[0]
    stepY = dataY[1]-dataY[0]
    if isinstance(dataE, list):
        if len(dataE) > 1: stepE = dataE[1] - dataE[0]
        else: stepE = 1.0
    else:
        if dataE.size > 1: stepE = dataE[1] - dataE[0]
        else: stepE = 1.0

    if stepE == 0.0: stepE = 1.0
    if stepX == 0.0: stepX = 1.0
    if stepY == 0.0: stepY = 1.0

    dim0_calib = (dataE[0],stepE)
    dim1_calib = (ymin, stepY)
    dim2_calib = (xmin, stepX)


    data_to_plot = numpy.swapaxes(data3D,1,2)

    colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

    plot_widget_id = StackViewMainWindow()
    plot_widget_id.setGraphTitle(title)
    plot_widget_id.setLabels(["Photon Energy [eV]",ytitle,xtitle])
    plot_widget_id.setColormap(colormap=colormap)
    plot_widget_id.setStack(numpy.array(data_to_plot), calibrations=[dim0_calib, dim1_calib, dim2_calib] )
    plot_widget_id.setTitleCallback( callback_for_title )

    return plot_widget_id


def plot_multi_data1D(x, y_list,
                      title="", xtitle="",
                      ytitle="",
                      ytitles=[""],
                      colors=None, #['green'],
                      replace=True,
                      control=False,
                      xrange=None,
                      yrange=None,
                      symbol=[''],
                      flag_common_abscissas=1,
                    ):
    if isinstance(y_list, list):
        ntimes = len(y_list)
    else:
        ntimes = y_list.shape[0]

    if ntimes != len(ytitles):
        ytitles = ytitles * ntimes

    if colors is None:
        colors = [None] * ntimes
    else:
        if ntimes != len(colors):
            colors = colors * ntimes

    if ntimes != len(symbol):
        symbol = symbol * ntimes

    # if tabs_canvas_index is None: tabs_canvas_index = 0  # back compatibility?

    # self.tab[tabs_canvas_index].layout().removeItem(self.tab[tabs_canvas_index].layout().itemAt(0))

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

    # self.tab[tabs_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])


    if flag_common_abscissas:
        for i in range(ntimes):
            plot_widget_id.addCurve(x, y_list[i],
                                                         ytitles[i],
                                                         xlabel=xtitle,
                                                         ylabel=ytitle,
                                                         symbol='',
                                                         color=colors[i])
    else:
        for i in range(ntimes):
            plot_widget_id.addCurve(x[i], y_list[i],
                                                         ytitles[i],
                                                         xlabel=xtitle,
                                                         ylabel=ytitle,
                                                         symbol='',
                                                         color=colors[i])

    #
    plot_widget_id.getLegendsDockWidget().setFixedHeight(150)
    plot_widget_id.getLegendsDockWidget().setVisible(True)
    plot_widget_id.setActiveCurve(ytitles[0])
    plot_widget_id.replot()

    if xrange is not None:
        plot_widget_id.setGraphXLimits(xrange[0], xrange[1])
    if yrange is not None:
        plot_widget_id.setGraphYLimits(yrange[0], yrange[1])

    return plot_widget_id
