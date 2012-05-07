#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

#Based on pyslice by Manish Singh
# (c) 2003 Manish Singh.
#"Guillotine implemented ala python, with html output
# (based on perlotine by Seth Burgess)",

from __future__ import division
import os
from gimpfu import *
import os.path

gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

class DotBook:
    def __init__(self, image, drawable, save_path, html_filename, image_basename, 
		separate, image_path, landscape, max_w, max_h, vert, horz):

        self.image = image
	self.image_basename = image_basename
	self.image_path = image_path
	gimp.progress_init(_("Dot Book"))
        self.progress_increment = 1 / ( 4 * len(self.image.layers) )
    	self.progress = 0.0
	self.landscape = landscape
	self.max_w = max_w
	self.max_h = max_h
	self.vert = vert
	self.horz = horz

	save_path = self.check_path(save_path)

	if not os.path.isdir(save_path):
            save_path = os.path.dirname(save_path)

    	if separate:
            self.image_relative_path = self.image_path
            if not self.image_relative_path.endswith("/"):
		self.image_relative_path += "/"
            self.image_path = self.check_path(os.path.join(save_path, self.image_path))
    	else:
            self.image_relative_path = ''
            self.image_path = save_path

	self.html = HTMLWriter(os.path.join(save_path, html_filename))


    @staticmethod
    def main(image, drawable, save_path, html_filename,
             image_basename, separate, image_path, landscape, max_w, max_h):
	
        vert, horz = get_guides(image)

	# make sure this image is split into 4 quadrants
	if len(vert) != 1 and len(horz) != 1:
            return

	dotbook = DotBook(image, drawable, save_path, html_filename, image_basename,
			separate, image_path, landscape, max_w, max_h, vert, horz)
	dotbook.process_image()


    def check_path(self, path):
        path = os.path.abspath(path)

        if not os.path.exists(path):
            os.mkdir(path)

        return path


    def process_image(self):
    	for x in range(0, len(self.image.layers)):
            temp_layer = self.image.layers[x]	

	    if self.landscape:
		self.process_landscape(temp_layer, x)
	    else:
		self.process_portrait(temp_layer, x)

	self.html.close()
		

    def process_landscape(self, temp_layer, x):
        left = 0

        for j in range(0, len(self.vert) + 1):
            if j == len(self.vert):
                right = self.image.width
            else:
                right = self.image.get_guide_position(self.vert[j])

            top = 0

            for i in range(0, len(self.horz) + 1):
            	if i == len(self.horz):
                    bottom = self.image.height
            	else:
                    bottom = self.image.get_guide_position(self.horz[i])

            	self.process_quadrant(temp_layer, left, right, top, bottom, x, i, j)
	
            	top = bottom

            left = right


    def process_portrait(self, temp_layer, x):
	for i in range(len(self.horz), -1, -1):
            if i == 0:
            	bottom = self.image.height
            top = self.image.get_guide_position(self.horz[0])
    	else:
            bottom = self.image.get_guide_position(self.horz[0])
            top = 0;

            for j in range(len(self.vert), -1, -1):
		if j == 0:
                    right = self.image.get_guide_position(self.vert[0])
                    left = 0
            	else:
                    right = self.image.width
                    left = self.image.get_guide_position(self.vert[0])

		self.process_quadrant(temp_layer, left, right, top, bottom, x, i, j)


    def process_quadrant(self, temp_layer, left, right, top, bottom, x, i, j):
	src = (self.image_relative_path +
                       self.save_quadrant (temp_layer, left, right, top, bottom, x, i, j))

        self.html.addimage(src)
        self.progress += self.progress_increment
        gimp.progress_update(self.progress)
	

    def save_quadrant(self, drawable, left, right, top, bottom, x, i, j):
	src = "%s_%d_%d_%d.jpg" % (self.image_basename, x, i, j)
    	filename = os.path.join(self.image_path, src)

    	temp_image = pdb.gimp_image_new (drawable.width, drawable.height, self.image.base_type)
    	temp_drawable = pdb.gimp_layer_new_from_drawable (drawable, temp_image)
    	temp_image.add_layer (temp_drawable, -1)

    	temp_image.disable_undo()
    	temp_image.crop(right - left, bottom - top, left, top)

    	temp_width = right - left;
    	temp_height = bottom - top;

    	width_factor = self.max_w / temp_width
    	height_factor = self.max_h / temp_height
    	scale_factor = height_factor if width_factor > height_factor else width_factor
    	final_w = int(temp_width * scale_factor)
    	final_h = int(temp_height * scale_factor)

    	temp_image.scale(final_w, final_h)
    
    	if self.image.base_type == INDEXED:
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
            out = ('    <h2><img src="%s" /></h2>\n') % (src[0])

        else:
	    out = ('    <h2><img src="%s" /></h2>\n') %  (src)

        self.write(out)


register(
    "python-fu-dot-book",
    # table snippet means a small piece of HTML code here
    N_("Cuts a Pyware 'Personal Drill Book' along its guides, creates an HTML page suitable for an e-reader"),
    """Import a Pyware 'Personal Drill Book' PDF as layers.  Rotate it
    90 degrees clockwise if your reader doesn't have a landscape mode.
    Add guides to split the image into four (4) quadrants.  Then run
    the Dot Book filter. It will cut along the guides, order them as
    such: upper-left, lower-left, upper-right, lower-right.  Images
    will be saved in a single HTML page suitable to convert with
    calibre.""",
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
        (PF_STRING, "relative-image-path", _("Folder for image export"), "images"),
        (PF_TOGGLE, "landscape-mode",  _("Landscape Mode"), True),
	(PF_INT, "max-width", _("Width Constraint"), 740),
	(PF_INT, "max-height", _("Height Constraint"), 520)	
    ],
    [],
    DotBook.main,
    menu="<Image>/Filters/Web",
    domain=("gimp20-python", gimp.locale_directory)
    )

main()
