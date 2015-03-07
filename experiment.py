__author__ = "EXPERIMENTER_NAME"

import klibs
from klibs import Params
from klibs.KLNumpySurface import *
from klibs.KLUtilities import *
from math import floor
import random
Params.screen_x = 1440
Params.screen_y = 900
# Params.default_fill_color = (125, 125, 125, 255)

Params.debug_level = 11
Params.collect_demographics = True
Params.practicing = True
Params.eye_tracking = True
Params.eye_tracker_available = False
Params.instructions = False

Params.blocks_per_experiment = 1
Params.trials_per_block = 96
Params.practice_blocks = None
Params.trials_per_practice_block = None

BG_CIRCLE = 0
BG_SQUARE = 1
FIG_SQUARE = "FIG_S"
FIG_CIRCLE = "FIG_C"
FIG_D = "FIG_D"
FIG_TRIANGLE = "FIG_T"
OR_UP = "ORI_U"
OR_DOWN = "ORI_D"
OR_LEFT = "ORI_D"
OR_RIGHT = "ORI_D"
FULL = "MASK_F"
CENTRAL = "MASK_C"
PERIPHERAL = "MASK_P"
FIX_TOP = (Params.screen_x // 2, Params.screen_y // 4)
FIX_CENTRAL = Params.screen_c
FiX_BOTTOM = (Params.screen_x // 2, 3 * Params.screen_y // 4)
Params.exp_meta_factors = {"stim_size": [10, 8, 4], # degrees of visual angle
						   "fixation": [FIX_TOP, FIX_CENTRAL, FiX_BOTTOM]}
Params.exp_factors = [("mask", [FULL, CENTRAL, PERIPHERAL]),
					  ("figure", [FIG_SQUARE, FIG_CIRCLE, FIG_D, FIG_TRIANGLE ]),
					  ("background", [BG_CIRCLE, BG_SQUARE]),
					  ("orientation", [OR_UP, OR_DOWN, OR_LEFT, OR_RIGHT]),
					]
#
# class Gradient(object):
# 	stops = []
#
# 	def __init__(self):
# 		pass
#
# 	def add_color(self, color, location, opacity ):
# 		self.stops.append( (color, location, opacity) )
#
# 	def render(self):


class FGSearch(klibs.Experiment):
	stim_size = None
	bg_element_size = 0.2  # degrees of visual angle
	bg_element_padding = 0.2  # degrees of visual angle

	neutral_color = (127, 127, 127)
	mask_opaque_region = 0.5

	# trial vars
	timed_out = False

	def __init__(self, *args, **kwargs):
		klibs.Experiment.__init__(self, *args, **kwargs)


	def setup(self):
		pr("@PExperiment.setup() reached")
		Params.key_maps['FGSearch_response'] = klibs.KeyMap('FGSearch_response', [], [], [])
		Params.exp_meta_factors['fixation'] = [Params.screen_c,
											   (Params.screen_c[0], Params.screen_y / 4),
											   (Params.screen_c[0], 3 * Params.screen_y / 4)]
		dc_box_size = 50
		# left drift correct box
		dc_top_tl = (0.5 * Params.screen_x - 0.5 * dc_box_size, Params.screen_y / 4 - 0.5 * dc_box_size )
		dc_top_br = (0.5 * Params.screen_x + 0.5 * dc_box_size, Params.screen_y / 4 + 0.5 * dc_box_size)
		self.eyelink.add_gaze_boundary('dc_top_box', [dc_top_tl, dc_top_br])
		# right drift correct box
		dc_bottom_tl = ( 0.5 * Params.screen_y - 0.5 * dc_box_size, 3 * Params.screen_y / 4 - 0.5 * dc_box_size )
		dc_bottom_br = ( 0.5 * Params.screen_y - 0.5 * dc_box_size, 3 * Params.screen_y / 4 + 0.5 * dc_box_size )
		self.eyelink.add_gaze_boundary('dc_bottom_box', [dc_bottom_tl, dc_bottom_br])
		# middle drift correct box
		dc_middle_tl = (Params.screen_x / 2 - 0.5 * dc_box_size, 0.5 * Params.screen_y - 0.5 * dc_box_size)
		dc_middle_br = (Params.screen_x / 2 + 0.5 * dc_box_size, 0.5 * Params.screen_y + 0.5 * dc_box_size)
		self.eyelink.add_gaze_boundary('dc_middle_box', [dc_middle_tl, dc_middle_br])
		pr("@BExperiment.setup() exiting")


	def block(self, block_num):
		pr("@PExperiment.block() reached")
		# dv = degrees of vis. angle,
		self.stim_size = int(str(Params.exp_meta_factors['stim_size'][Params.block_number % 3]).replace("vd", " "))
		pr("@BExperiment.block() exiting")

	def trial_prep(self, *args, **kwargs):
		pr("@PExperiment.trial_prep() reached")
		self.database.init_entry('trials')
		self.message("Press any key to advance...", color=(255, 255, 255, 255), location="center", font_size=48,
					 flip=False)
		self.listen()
		self.drift_correct(tuple(random.choice(Params.exp_meta_factors['fixation'])))
		pr("@BExperiment.trial_prep() exiting")

	def trial(self, trial_factors, trial_num):
		"""
		trial_factors: 1 = mask, 2 = figure, 3 = background, 4 = orientation]
		"""
		pr("@PExperiment.trial() reached")
		pr("@T\ttrial_factors: {0}".format(trial_factors[1]))
		self.eyelink.start(trial_num)
		texture = self.texture(trial_factors[3])
		if trial_factors[2] != FIG_SQUARE:  # texture already is square, nothing to mask
			texture_mask = self.figure(trial_factors[2])
			pr("@T TextureMask: {0},  texture: {1}".format(texture_mask, texture))
			texture.mask(texture_mask, (0, 0))
		start = now()
		print trial_factors
		if trial_factors[1] == CENTRAL:
			mask = self.central_mask(5, self.neutral_color)
		if trial_factors[1] == PERIPHERAL:
			mask = self.central_mask(5, (255, 0, 0))

		while now() - start < 2:
			pump()
			self.fill()
			self.blit(texture, 5, 'center')
			if trial_factors[1] == PERIPHERAL:
				mask = self.peripheral_mask(mask)
				print mask
				self.blit(mask, 7, (0, 0))
			if trial_factors[1] == CENTRAL:
				self.blit(mask, 5, mouse_pos())
			self.flip()
		exit()
		try:
			resp = self.listen(3)
		except:
			self.timed_out = True
		# stim_parts = trial_factors[2].split("_") # this is the name of the bg  ie. "circle_of_squares"

		if self.timed_out:
			data = {"practicing": -1,
					"response": -1,
					"rt": float(-1),
					"metacondition": ",".join(self.METACOND),
					"mask": trial_factors[3],
					"mask_diam": self.stim_size,
					"form": bg[0],
					"material": bg[1],
					"trial_num": trial_num,
					"block_num": Params.block_number,
					"initial_fixation": 'not_tracking'}
		else:
			data = {"practicing": trial_factors[0],
					"response": resp[0],
					"rt": float(resp[1]),
					"metacondition": ",".join(self.METACOND),
					"mask": trial_factors[3],
					"mask_diam": self.stim_size,
					"form": bg[0],
					"material": bg[1],
					"trial_num": trial_num,
					"block_num": Params.block_number,
					"initial_fixation": trial_factors[1]}
			return data
		return {}

	def refreshScreen(self, bg, mask):
		gaze = self.eyelink.gaze()
		if gaze:
			self.fill()
			self.blit(bg, 5, Params.screen_c)
			self.blit(mask, 5, gaze)
			self.flip()

	def trial_clean_up(self, *args, **kwargs):
		pass

	def clean_up(self):
		pass

	def texture(self, texture_figure):
		pr("@P Experiment.texture(texture_figure) reached\n\t@Ttexture_figure = {0}".format(texture_figure))
		grid_size = deg_to_px(1.1 * self.stim_size)
		dc = aggdraw.Draw("RGBA", (grid_size, grid_size), (0, 0, 0, 0))
		pen = aggdraw.Pen((255, 255, 255), 1.5, 255)
		grid_cell_size = deg_to_px(self.bg_element_size + self.bg_element_padding)
		grid_cell_count = grid_size // grid_cell_size
		pr("\t@TGridSize: {0}, GridCellSize:{1}, GridCellCount: {2}".format(grid_size, grid_cell_size, grid_cell_count))

	 	# Visual Representation of the Texture Rendering Logic
		# <-------G-------->
		#  _______________   ^
		# |       O       |  |    O = element_offset, ie. 1/2 bg_element_padding
		# |     _____     |  |    E = element (ie. circle, square, triangle, etc.)
		# |    |     |    |  |    G = one grid length
		# | O  |  E  |  O |  G
		# |    |_____|    |  |
		# |               |  |
		# |_______O_______|  |
		#                    v

		element_offset = self.bg_element_padding // 2  # so as to apply padding equally on all sides of bg elements
		element = None
		for col in range(0, grid_cell_count):
			for row in range(0, grid_cell_count):
				top = int(row * grid_cell_size + element_offset)
				left = int(col * grid_cell_size + element_offset)
				bottom = int(top + deg_to_px(self.bg_element_size))
				right = int(left + deg_to_px(self.bg_element_size))
				# pr("\t@Ttop: {0}, left: {1}, bottom:{2}, right:{3}".format(top, left, bottom, right))
				if texture_figure == BG_CIRCLE: dc.ellipse([left, top, right, bottom], pen)
				if texture_figure == BG_SQUARE: dc.rectangle([left, top, right, bottom], pen)
		return from_aggdraw_context(dc)

	def figure(self, figure_shape):
		size = deg_to_px(self.stim_size)
		dc_size = deg_to_px(1.1 * self.stim_size)
		pad = 0.1 * size
		dc = aggdraw.Draw('RGBA', (dc_size, dc_size), (0, 0, 0, 0))
		brush = aggdraw.Brush((255, 255, 255), 255)

		if figure_shape == FIG_CIRCLE:
			dc.ellipse((pad, pad, size, size), brush)
		if figure_shape == FIG_TRIANGLE:
			dc.polygon((size // 2, 0, size, size, 0, size, size // 2, 0), brush)
		if figure_shape == FIG_D:
			dc.ellipse((pad, pad, size, size), brush)
			dc.rectangle((pad, pad, size // 2, size), brush)
		cookie_cutter = from_aggdraw_context(dc)
		dough = aggdraw.Draw('RGBA', (dc_size, dc_size), (0, 0, 0, 0))
		dough.rectangle((0, 0, dc_size, dc_size), brush)
		dough = from_aggdraw_context(dough)
		dough.mask(cookie_cutter, (0, 0))
		return dough


	def central_mask(self, diameter, color):
		diameter = deg_to_px(diameter)
		pr("@P mask(diameter): {0}".format(diameter))

		mask = aggdraw.Draw('RGBA', (diameter, diameter), (0, 0, 0, 0))
		opaque_region = int(diameter * self.mask_opaque_region)
		graded_region = diameter - opaque_region
		graded_range = range(opaque_region, diameter)
		cumulative_opacity = None
		cumulative_diffs = []
		for n in range(1, diameter):
			d = float(diameter - n)
			if d in graded_range:
				opacity_factor = float(diameter - d) / graded_region * 1.0
				intended_opacity = int(floor(255 * opacity_factor))
				if cumulative_opacity is None: cumulative_opacity = intended_opacity
				if intended_opacity > cumulative_opacity:
					opacity_diff = intended_opacity - cumulative_opacity
					cumulative_diffs.append(opacity_diff/255.0)
					cumulative_opacity += opacity_diff
					opacity = cumulative_opacity * sum(cumulative_diffs)
				else:
					opacity = cumulative_opacity
				tl = n//2
				br = diameter - tl
				pr("\t@T opacity: {0},cumulative:{3}  opacity_factor: {1},  d: {2}".format(opacity,  opacity_factor, d, cumulative_opacity), 10)
			else:
				opacity = 255
			brush = aggdraw.Brush(color, int(opacity))
			mask.ellipse((tl, tl, br, br), brush)

		return from_aggdraw_context(mask)

	def peripheral_mask(self, mask):
		dc = aggdraw.Draw('RGBA', (Params.screen_x, Params.screen_y), (0, 0, 0, 0))
		brush = aggdraw.Brush(self.neutral_color, 255)
		dc.rectangle( (0, 0, Params.screen_x, Params.screen_y), brush )
		p_mask = from_aggdraw_context(dc)
		p_mask.mask(mask, mouse_pos())
		return p_mask
		box_width = int(1.1 * diameter)
		pr("@T\tBoxWidth: {0}".format(box_width))


		'''
		  DRAW THE MASK BOX -- this is for testing; creates the bounding box for where the mask *should* go
	  	'''
	  	# half_bw = box_width // 2
		# box_tl = (mp[0] - half_bw, mp[1] - half_bw)
		# box_br = (mp[0] + half_bw, mp[1] + half_bw)
		# dc.rectangle((box_tl[0], box_tl[1], box_br[0], box_br[1]), aggdraw.Brush((0, 0, 0), ))
		#
		# if box_tl[0] >= 0:
		# 	if box_tl[1] >=  0:
		# 		#  TOP STRIP
		# 		dc.rectangle((0, 0, Params.screen_x, box_tl[1]), brush)
		# 		#  LEFT PANEL
		# 		dc.rectangle((0, box_tl[1],  box_tl[0], box_tl[1] + box_width), brush)
		# 		# RIGHT PANEL
		# 		dc.rectangle((box_tl[0] + box_width, box_tl[1], Params.screen_x, box_tl[1] + box_width), brush)
		# 		# BOTTOM PANEL
		# 		dc.rectangle( (0, box_tl[1] + box_width, Params.screen_x, Params.screen_y), brush)
		# curtain = from_aggdraw_context(dc)

		padded_radius = int(math.ceil(1.1 * box_width))
	 	cookie_cutter = canvas(padded_radius, padded_radius)
		for n in range(padded_radius):
			n = float(n)
			r = float(padded_radius - n)
			opacity = int(( 0.25 * n / padded_radius) * 100)
			brush = ad_fill((255, 255, 255), int(opacity))
			tl = (padded_radius - r) // 2
			br = (padded_radius - r) // 2 + r
			cookie_cutter.ellipse((tl, tl, br, br), ad_fill([0, 0, 0]))
			# pr("@T\ti:{0}, r:{3}, i/r: {1},  Opacity: {2}, tl: {4}, br: {5}".format(n, float(n) / radius, opacity, radius,tl, br ))
		cookie_cutter = from_aggdraw_context(cookie_cutter)
		dough = canvas(Params.screen_x, Params.screen_y)
		dough.rectangle((0, 0, Params.screen_x,  Params.screen_y), ad_fill([255,0,0]))
		dough = from_aggdraw_context(dough)
		dough.mask(cookie_cutter, Params.screen_c)
		self.blit(dough, 5, 'center')


app = FGSearch("FGSearch").run()
