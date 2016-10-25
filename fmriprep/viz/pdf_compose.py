# -*- coding: utf-8 -*-
"""
Created on Sun Jul 26 16:54:08 2015

@author: craigmoodie
"""


def generate_report(output_file, first_plot, second_plot, third_plot,
                    fourth_plot, fifth_plot, sixth_plot, seventh_plot,
                    eighth_plot, t1_2_mni_plot=None):
    import os.path

    import pylab as plt
    import matplotlib.image as mimage
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.gridspec import GridSpec

    plots = [first_plot, second_plot, third_plot, fourth_plot,
             fifth_plot, sixth_plot, seventh_plot, eighth_plot]

    if t1_2_mni_plot is not None:
        plots.insert(6, t1_2_mni_plot)

    #  error_image = ""
    #  error = mimage.imread(error_image)
    report = PdfPages(output_file)
    fig = plt.figure()
    grid = GridSpec(3, 3)

    plot_iterator = iter(plots)
    for i in range(0, 3):
        for j in range(0, 3):
            try:
                plot = next(plot_iterator)
            except:
                print('{}, {}'.format(i, j))
                continue
            if plot is None:
                #  plot = error
                continue
            img = mimage.imread(plot)
            ax = plt.subplot(grid[j, i])
            ax.imshow(img)
            ax.set_aspect('auto')
            for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                         ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(8)

            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)

    fig.subplots_adjust(wspace=0.02, hspace=.2)

    report.savefig(fig, dpi=300)
    report.close()

    return os.path.abspath(output_file)
