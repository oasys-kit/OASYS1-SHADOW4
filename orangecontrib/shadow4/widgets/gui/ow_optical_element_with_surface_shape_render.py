import numpy
import os
from scipy.optimize import root

from PyQt5.QtWidgets import QDialog, QGridLayout, QWidget, QDialogButtonBox, QFileDialog

from matplotlib import cm
from oasys.widgets.gui import FigureCanvas3D, MessageDialog
from matplotlib.figure import Figure
try:    from mpl_toolkits.mplot3d import Axes3D  # plot 3D
except: pass


from orangewidget import gui

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from oasys.util.oasys_util import write_surface_file

from shadow4.optical_surfaces.s4_toroid import S4Toroid
from shadow4.optical_surfaces.s4_conic import S4Conic
from shadow4.optical_surfaces.s4_mesh import S4Mesh

from shadow4.beamline.optical_elements.mirrors.s4_additional_numerical_mesh_mirror import S4AdditionalNumericalMeshMirror

#todo: add S4Mesh and S4AdditionalMesh

class ShowSurfaceShapeDialog(QDialog):
    def __init__(self, parent=None,
                 is_torus=0,
                 ccc=None, branch=0,
                 torus_major_radius=10.0, torus_minor_radius = 1.0, f_torus=0,
                 x_min=-0.010, x_max=0.010, y_min=-0.010, y_max=0.010,
                 bin_x=100, bin_y=100,
                 read_only=0,
                 ):


        self.parent = parent
        self.ccc = ccc
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

        self.is_torus = is_torus
        self.torus_major_radius = torus_major_radius
        self.torus_minor_radius = torus_minor_radius
        self.f_torus = f_torus

        if ccc is None: ccc = [0.0] * 10
        self.c1 = ccc[0]
        self.c2 = ccc[1]
        self.c3 = ccc[2]
        self.c4 = ccc[3]
        self.c5 = ccc[4]
        self.c6 = ccc[5]
        self.c7 = ccc[6]
        self.c8 = ccc[7]
        self.c9 = ccc[8]
        self.c10 = ccc[9]
        self.branch = branch


        self.read_only = read_only

        self.xx = None
        self.yy = None
        self.zz = None

        self.bin_x = bin_x
        self.bin_y = bin_y

        if self.parent is not None:

            optical_element = self.parent.get_optical_element_instance()

            if isinstance(optical_element, S4AdditionalNumericalMeshMirror):
                optical_element = optical_element.get_ideal()

            optical_surface = optical_element.get_optical_surface_instance()

            if isinstance(optical_surface, S4Conic):
                ccc = optical_surface.get_coefficients()
                self.c1  = round(ccc[0], 10)
                self.c2  = round(ccc[1], 10)
                self.c3  = round(ccc[2], 10)
                self.c4  = round(ccc[3], 10)
                self.c5  = round(ccc[4], 10)
                self.c6  = round(ccc[5], 10)
                self.c7  = round(ccc[6], 10)
                self.c8  = round(ccc[7], 10)
                self.c9  = round(ccc[8], 10)
                self.c10 = round(ccc[9], 10)
                self.is_torus = 0
            elif isinstance(optical_surface, S4Toroid):
                self.torus_major_radius = round(optical_surface.r_maj, 10)
                self.torus_minor_radius = round(optical_surface.r_min, 10)
                self.f_torus = optical_surface.f_torus
                self.is_torus = 1
            else:
                raise Exception("optical surface not implemented", optical_surface)

            if not parent.is_infinite:
                self.x_min = round(-parent.dim_x_minus, 10)
                self.x_max = round(parent.dim_x_plus,   10)
                self.y_min = round(-parent.dim_y_minus, 10)
                self.y_max = round(parent.dim_y_plus,   10)

        #
        # initialize window
        #
        QDialog.__init__(self, parent)
        self.setWindowTitle('O.E. Surface Shape')
        self.setFixedWidth(1000)

        layout = QGridLayout(self)

        figure = Figure(figsize=(100, 100))
        figure.patch.set_facecolor('white')

        self.axis = figure.add_subplot(111, projection='3d')

        self.figure_canvas = FigureCanvas3D(ax=self.axis, fig=figure, show_legend=False, show_buttons=False)
        self.figure_canvas.setFixedWidth(700)
        self.figure_canvas.setFixedHeight(700)

        self.refresh()

        widget    = QWidget(parent=self)
        container = oasysgui.widgetBox(widget, "", addSpace=False, orientation="vertical", width=220)

        if self.is_torus:
            surface_box = oasysgui.widgetBox(container, "Toroid Parameters", addSpace=False, orientation="vertical", width=220, height=375)

            le_torus_major_radius = oasysgui.lineEdit(surface_box, self, "torus_major_radius" , "R [m]" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)
            le_torus_minor_radius = oasysgui.lineEdit(surface_box, self, "torus_minor_radius" , "r [m]" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)

            le_torus_major_radius.setReadOnly(self.read_only)
            le_torus_minor_radius.setReadOnly(self.read_only)

            gui.comboBox(surface_box, self, "f_torus",
                         label="Select solution and \n shift center \n to pole location at:",
                         labelWidth=220,
                         items=["lower/outer (concave/concave)",
                                "lower/inner (concave/convex)",
                                "upper/inner (convex/concave)",
                                "upper/outer (convex/convex)"],
                         sendSelectedValue=False, orientation="vertical", tooltip="f_torus", callback=self.refresh)
        else:
            surface_box = oasysgui.widgetBox(container, "Conic Coefficients", addSpace=False, orientation="vertical", width=220, height=420)

            # label  = "c[1]" + u"\u00B7" + "X" + u"\u00B2" + " + c[2]" + u"\u00B7" + "Y" + u"\u00B2" + " + c[3]" + u"\u00B7" + "Z" + u"\u00B2" + " +\n"
            # label += "c[4]" + u"\u00B7" + "XY" + " + c[5]" + u"\u00B7" + "YZ" + " + c[6]" + u"\u00B7" + "XZ" + " +\n"
            # label += "c[7]" + u"\u00B7" + "X" + " + c[8]" + u"\u00B7" + "Y" + " + c[9]" + u"\u00B7" + "Z" + " + c[10] = 0"

            label  = "c<sub>xx</sub> X<sup>2</sup>  + c<sub>yy</sub> Y<sup>2</sup> + c<sub>zz</sub> Z<sup>2</sup> + <br/>"
            label += "c<sub>xy</sub> X Y + c<sub>yz</sub> Y Z+ c<sub>xz</sub> X Z + <br/>"
            label += "c<sub>x</sub> X + c<sub>y</sub> Y + c<sub>z</sub> Z + c<sub>0</sub>= 0"

            gui.label(surface_box, self, label)

            gui.separator(surface_box, 10)

            label = "c<sub>xx</sub> X<sup>2</sup>  + c<sub>yy</sub> Y<sup>2</sup> + c<sub>zz</sub> Z<sup>2</sup> + <br/>"

            le_0 = oasysgui.lineEdit(surface_box, self, "c1" , "c<sub>xx</sub>" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)
            le_1 = oasysgui.lineEdit(surface_box, self, "c2" , "c<sub>yy</sub>" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)
            le_2 = oasysgui.lineEdit(surface_box, self, "c3" , "c<sub>zz</sub>" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)
            le_3 = oasysgui.lineEdit(surface_box, self, "c4" , "c<sub>xy</sub>" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)
            le_4 = oasysgui.lineEdit(surface_box, self, "c5" , "c<sub>yz</sub>" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)
            le_5 = oasysgui.lineEdit(surface_box, self, "c6" , "c<sub>xz</sub>" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)
            le_6 = oasysgui.lineEdit(surface_box, self, "c7" , "c<sub>x</sub>" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)
            le_7 = oasysgui.lineEdit(surface_box, self, "c8" , "c<sub>y</sub>" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)
            le_8 = oasysgui.lineEdit(surface_box, self, "c9" , "c<sub>z</sub>" , labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)
            le_9 = oasysgui.lineEdit(surface_box, self, "c10", "c<sub>0</sub>", labelWidth=60, valueType=float, orientation="horizontal", callback=self.refresh)

            gui.comboBox(surface_box, self, "branch",
                         label="solution index", addSpace=False,
                         items=['0', '1'],
                         valueType=int, orientation="horizontal", callback=self.refresh)

            le_0.setReadOnly(self.read_only)
            le_1.setReadOnly(self.read_only)
            le_2.setReadOnly(self.read_only)
            le_3.setReadOnly(self.read_only)
            le_4.setReadOnly(self.read_only)
            le_5.setReadOnly(self.read_only)
            le_6.setReadOnly(self.read_only)
            le_7.setReadOnly(self.read_only)
            le_8.setReadOnly(self.read_only)
            le_9.setReadOnly(self.read_only)

        limits_box = oasysgui.widgetBox(container, "Limits", addSpace=False, orientation="vertical", width=220)
        oasysgui.lineEdit(limits_box, self, "x_min", "x<sub>min</sub> [m]", labelWidth=70, valueType=float, orientation="horizontal", callback=self.refresh)
        oasysgui.lineEdit(limits_box, self, "x_max", "x<sub>max</sub> [m]", labelWidth=70, valueType=float, orientation="horizontal", callback=self.refresh)
        oasysgui.lineEdit(limits_box, self, "y_min", "y<sub>min</sub> [m]", labelWidth=70, valueType=float, orientation="horizontal", callback=self.refresh)
        oasysgui.lineEdit(limits_box, self, "y_max", "y<sub>max</sub> [m]", labelWidth=70, valueType=float, orientation="horizontal", callback=self.refresh)



        export_box = oasysgui.widgetBox(container, "Export", addSpace=False, orientation="vertical", width=220)

        bin_box = oasysgui.widgetBox(export_box, "", addSpace=False, orientation="horizontal")
        oasysgui.lineEdit(bin_box, self, "bin_x" , "Bins X" , labelWidth=40, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(bin_box, self, "bin_y" , " x Y" , labelWidth=30, valueType=float, orientation="horizontal")

        gui.button(export_box, self, "Export Surface (.hdf5)", callback=self.save_oasys_surface)

        bbox = QDialogButtonBox(QDialogButtonBox.Ok)
        bbox.accepted.connect(self.accept)
        layout.addWidget(self.figure_canvas, 0, 0)
        layout.addWidget(widget, 0, 1)
        layout.addWidget(bbox, 1, 0, 1, 2)

        self.setLayout(layout)

    def refresh(self):

        self.check_values()

        X, Y, z_values = self.calculate_surface()

        self.axis.clear()

        self.axis.set_xlabel("X [m]")
        self.axis.set_ylabel("Y [m]")
        self.axis.set_zlabel("Z [m]")

        self.axis.plot_surface(X, Y, z_values, rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

        if self.is_torus:
            self.axis.set_title("Toroid equation (centered):\n" +
                           "[X" + u"\u00B2" +
                           " + Y" + u"\u00B2" +
                           " + Z" + u"\u00B2" +
                           " + R" + u"\u00B2" +
                           " - r" + u"\u00B2"
                           + "]" + u"\u00B2" +
                           "= 4R" + u"\u00B2" + "[Y" + u"\u00B2" + " + Z" + u"\u00B2" + "]")
        else:
            title_head = "Surface from generated conic coefficients:\n"
            title = ""
            max_dim = 40

            if self.c1 != 0: title +=       str(self.c1) + u"\u00B7" + "X" + u"\u00B2"
            if len(title) >=  max_dim:
                title_head += title + "\n"
                title = ""
            if self.c2 < 0 or (self.c2 > 0 and title == ""): title +=       str(self.c2) + u"\u00B7" + "Y" + u"\u00B2"
            elif self.c2 > 0                                 : title += "+" + str(self.c2) + u"\u00B7" + "Y" + u"\u00B2"
            if len(title) >=  max_dim:
                title_head += title + "\n"
                title = ""
            if self.c3 < 0 or (self.c3 > 0 and title == ""): title +=       str(self.c3) + u"\u00B7" + "Z" + u"\u00B2"
            elif self.c3 > 0                                 : title += "+" + str(self.c3) + u"\u00B7" + "Z" + u"\u00B2"
            if len(title) >=  max_dim:
                title_head += title + "\n"
                title = ""
            if self.c4 < 0 or (self.c4 > 0 and title == ""): title +=       str(self.c4) + u"\u00B7" + "XY"
            elif self.c4 > 0                                 : title += "+" + str(self.c4) + u"\u00B7" + "XY"
            if len(title) >=  max_dim:
                title_head += title + "\n"
                title = ""
            if self.c5 < 0 or (self.c5 > 0 and title == ""): title +=       str(self.c5) + u"\u00B7" + "YZ"
            elif self.c5 > 0                                 : title += "+" + str(self.c5) + u"\u00B7" + "YZ"
            if len(title) >=  max_dim:
                title_head += title + "\n"
                title = ""
            if self.c6 < 0 or (self.c6 > 0 and title == ""): title +=       str(self.c6) + u"\u00B7" + "XZ"
            elif self.c6 > 0                                 : title += "+" + str(self.c6) + u"\u00B7" + "XZ"
            if len(title) >=  max_dim:
                title_head += title + "\n"
                title = ""
            if self.c7 < 0 or (self.c7 > 0 and title == ""): title +=       str(self.c7) + u"\u00B7" + "X"
            elif self.c7 > 0                                 : title += "+" + str(self.c7) + u"\u00B7" + "X"
            if len(title) >=  max_dim:
                title_head += title + "\n"
                title = ""
            if self.c8 < 0 or (self.c8 > 0 and title == ""): title +=       str(self.c8) + u"\u00B7" + "Y"
            elif self.c8 > 0                                 : title += "+" + str(self.c8) + u"\u00B7" + "Y"
            if len(title) >=  max_dim:
                title_head += title + "\n"
                title = ""
            if self.c9 < 0 or (self.c9 > 0 and title == ""): title +=       str(self.c9) + u"\u00B7" + "Z"
            elif self.c9 > 0                                 : title += "+" + str(self.c9) + u"\u00B7" + "Z"
            if len(title) >=  max_dim:
                title_head += title + "\n"
                title = ""
            if self.c10< 0 or (self.c10> 0 and title == ""): title +=       str(self.c10)
            elif self.c10> 0                                 : title += "+" + str(self.c10)

            self.axis.set_title(title_head + title + " = 0")

        self.figure_canvas.draw()
        self.axis.mouse_init()

    def calculate_surface(self):
        x_min = self.x_min
        x_max = self.x_max
        y_min = self.y_min
        y_max = self.y_max
        bin_x = int(self.bin_x)
        bin_y = int(self.bin_y)

        self.xx = numpy.linspace(x_min, x_max, bin_x + 1)
        self.yy = numpy.linspace(y_min, y_max, bin_y + 1)

        X = numpy.outer(self.xx, numpy.ones_like(self.yy))
        Y = numpy.outer(numpy.ones_like(self.xx), self.yy)


        if self.is_torus:
            T = S4Toroid(r_min=self.torus_minor_radius, r_maj=self.torus_major_radius, f_torus=self.f_torus)
            z_values = T.surface_height(X, Y, method=0, solution_index=-1)
            z_values[numpy.where(numpy.isnan(z_values))] = 0.0
        else:
            T = S4Conic([self.c1, self.c2, self.c3, self.c4, self.c5, self.c6, self.c7, self.c7, self.c9, self.c10])
            z_values = T.surface_height(X, Y, return_solution=self.branch)
            z_values[numpy.where(numpy.isnan(z_values))] = 0.0

        self.zz = z_values

        return X, Y, z_values

    def check_values(self):
        congruence.checkStrictlyPositiveNumber(self.bin_x, "Bins X")
        congruence.checkStrictlyPositiveNumber(self.bin_y, "Bins Y")
        congruence.checkStrictlyPositiveNumber(self.torus_minor_radius, "torus minor radius")
        congruence.checkStrictlyPositiveNumber(self.torus_major_radius, "torus major radius")

    def save_oasys_surface(self):
        try:
            file_path = QFileDialog.getSaveFileName(self, "Save Surface in Oasys (hdf5) Format", ".", "HDF5 format (*.hdf5)")[0]

            if not file_path is None and not file_path.strip() == "":
                self.check_values()

                self.calculate_surface()

                write_surface_file(self.zz.T, self.xx, self.yy, file_path)
        except Exception as exception:
            if self.parent is not None: self.parent.prompt_exception(exception)
            else:
                MessageDialog.message(self, str(exception), "Exception occured in OASYS", "critical")
                if self.IS_DEVELOP: raise exception


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = ShowSurfaceShapeDialog(ccc=[1.0,1.0,1.0,0.0,0.0,0.0,0.0,0.0,-764,0.0], is_torus=0)
    # dialog = ShowSurfaceShapeDialog(is_torus=1, torus_major_radius=7499.954, torus_minor_radius = 0.046, f_torus=0,
    #              x_min=-0.04, x_max=0.04, y_min=-0.3, y_max=0.3,)
    dialog.show()
    app.exec()