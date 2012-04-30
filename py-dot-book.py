#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Based on pyslice by Manish Singh

#Copyright (c) Manish Singh
#javascript animation support by Joao S. O. Bueno Calligaris (2004)

#   Gimp-Python - allows the writing of Gimp plugins in Python.
#   Copyright (C) 2003, 2005  Manish Singh <yosh@gimp.org>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# (c) 2003 Manish Singh.
#"Guillotine implemented ala python, with html output
# (based on perlotine by Seth Burgess)",
# Modified by João S. O. Bueno Calligaris to allow  dhtml animations (2005)

import os

from gimpfu import *
import os.path

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def pydotbook(image, drawable, save_path, html_filename,
            image_basename, separate, image_path):

    vert, horz = get_guides(image)

    if len(vert) != 1 and len(horz) != 1:
        return

    gimp.progress_init(_("Dot Book"))
    progress_increment = 1 / ( 4 * len(image.layers) )
    progress = 0.0

    def check_path(path):
        path = os.path.abspath(path)

        if not os.path.exists(path):
            os.mkdir(path)

        return path

    save_path = check_path(save_path)

    if not os.path.isdir(save_path):
        save_path = os.path.dirname(save_path)

    if separate:
        image_relative_path = image_path
        if not image_relative_path.endswith("/"):
            image_relative_path += "/"
        image_path = check_path(os.path.join(save_path, image_path))
    else:
        image_relative_path = ''
        image_path = save_path

    html = HTMLWriter(os.path.join(save_path, html_filename))

    for x in range(0, len(image.layers)):
	temp_layer = image.layers[x]

	left = 0

	for j in range(0, len(vert) + 1):
            if j == len(vert):
            	right = image.width
            else:
                right = image.get_guide_position(vert[j])

            top = 0

            for i in range(0, len(horz) + 1):
	    	if i == len(horz):
                    bottom = image.height
            	else:
                    bottom = image.get_guide_position(horz[i])


                src = (image_relative_path +
                       save_quadrant (image, temp_layer, image_path, image_basename,
                              left, right, top, bottom, x, i, j))

            	html.addimage(src)

	        top = bottom

	        progress += progress_increment
	        gimp.progress_update(progress)

            left = right

    html.close()

def save_quadrant(image, drawable, image_path, image_basename,
          	  left, right, top, bottom, x, i, j):
    src = "%s_%d_%d_%d.jpg" % (image_basename, x, i, j)
    filename = os.path.join(image_path, src)

    temp_image = pdb.gimp_image_new (drawable.width, drawable.height, image.base_type)
    temp_drawable = pdb.gimp_layer_new_from_drawable (drawable, temp_image)
    temp_image.add_layer (temp_drawable, -1)

    temp_image.disable_undo()
    temp_image.crop(right - left, bottom - top, left, top)
    # should resize to 520x740 for kindle touch
    
    if image.base_type == INDEXED:
        pdb.gimp_image_convert_rgb (temp_image)

    pdb.gimp_file_save(temp_image, temp_drawable, filename, filename)

    gimp.delete(temp_image)
    return src

class GuideIter:
    def __init__(self, image):
        self.image = image
        self.guide = 0

    def __iter__(self):
        return iter(self.next_guide, 0)

    def next_guide(self):
        self.guide = self.image.find_next_guide(self.guide)
        return self.guide

def get_guides(image):
    vguides = []
    hguides = []

    for guide in GuideIter(image):
        orientation = image.get_guide_orientation(guide)

        guide_position = image.get_guide_position(guide)

        if guide_position > 0:
            if orientation == ORIENTATION_VERTICAL:
                if guide_position < image.width:
                    vguides.append((guide_position, guide))
            elif orientation == ORIENTATION_HORIZONTAL:
                if guide_position < image.height:
                    hguides.append((guide_position, guide))

    def position_sort(x, y):
        return cmp(x[0], y[0])

    vguides.sort(position_sort)
    hguides.sort(position_sort)

    vguides = [g[1] for g in vguides]
    hguides = [g[1] for g in hguides]

    return vguides, hguides

class HTMLWriter:
    def __init__(self, filename):

        self.filename = filename

        self.image_prefix = os.path.basename (filename)
        self.image_prefix = self.image_prefix.split(".")[0]
        self.image_prefix = self.image_prefix.replace ("-", "_")
        self.image_prefix = self.image_prefix.replace (" ", "_")

        self.html = open(filename, 'wt')
        self.open()

    def write(self, s, vals=None):
        if vals:
            s = s % vals

        self.html.write(s + '\n')

    def open(self):
        self.write('<html>\n<body>\n')

    def close(self):
        self.write('</body>\n</html>\n')
        prefix = self.image_prefix

    def addimage(self, src):
        if isinstance (src, list):
            prefix = "images_%s" % self.image_prefix
            self.images.append ({"index" : (row, col), "plain" : src[0]})
            out = ('    <img src="%s" />\n') % (src[0])

        else:
	    out = ('    <img src="%s" />\n') %  (src)

        self.write(out)

register(
    "python-fu-dot-book",
    # table snippet means a small piece of HTML code here
    N_("Cuts an image along its guides, rotates 90 deg, creates an HTML page suitable for an e-reader"),
    """Import a drill-chart PDF as layers.  Add guides to an image. 
    Then run this. It will cut along the guides, rotate the images 90 degrees,
    order them as such upper-left, lower-left, upper-right, lower-right.  Images
    will be sized optimal to a regular sized Kindle and save in a single HTML page. """,
    "Justin Foell",
    "Justin Foell",
    "2012",
    _("_Dot Book..."),
    "*",
    [
        (PF_IMAGE, "image", "Input image", None),
        (PF_DRAWABLE, "drawable", "Input drawable", None),
        (PF_DIRNAME, "save-path",     _("Path for HTML export"), os.getcwd()),
        (PF_STRING, "html-filename",  _("Filename for export"),  "dot-book.html"),
        (PF_STRING, "image-basename", _("Image name prefix"),    "dot-book"),
        (PF_TOGGLE, "separate-image-dir",  _("Separate image folder"), False),
        (PF_STRING, "relative-image-path", _("Folder for image export"), "images")
    ],
    [],
    pydotbook,
    menu="<Image>/Filters/Web",
    domain=("gimp20-python", gimp.locale_directory)
    )

main()
