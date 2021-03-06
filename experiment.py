__author__ = "Jon Mulle & Austin Hurst"

import klibs
from klibs.KLConstants import TIMEOUT, TK_S
from klibs import P
from klibs.KLUtilities import deg_to_px
from klibs.KLUserInterface import any_key, ui_request
from klibs.KLGraphics import aggdraw_to_numpy_surface, fill, flip, blit, clear
from klibs.KLCommunication import message
from klibs.KLKeyMap import KeyMap
from klibs.KLTime import CountDown
from klibs.KLResponseCollectors import KeyPressResponse

from PIL import Image, ImageDraw, ImageFilter
import random
import sdl2


"""
DEFINITIONS & SHORTHAND THAT CLEAN UP THE READABILITY OF THE CODE BELOW
"""
#  Fixation positions calculated in FigureGroundSearch.__init__() based on current screen dimensions

CIRCLE = "circle"
SQUARE = "square"
LOCAL  = "local"
GLOBAL = "global"

CENTRAL    = "central"
PERIPHERAL = "peripheral"

BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
NEUTRAL_COLOR = P.default_fill_color
TRANSPARENT = 0
OPAQUE = 255
RGBA = "RGBA"


"""
This code defines a  class that 'extends' the basic KLExperiment class.
The experiment itself is actually *run* at the end of this document, after it's been defined.
"""

class FigureGroundSearch(klibs.Experiment):
    stim_size = 12  # degrees of visual angle
    stim_pad = 0.8 # degrees of visual angle
    mask_blur_width = 4  # pixels
    maximum_mask_size = 0  # automatically set at run time, do not change
    search_time = 30  # seconds
    fixation = None  # chosen randomly each trial
    bg_element_size = 0.8  # degrees of visual angle
    bg_element_pad = 0.6  # degrees of visual angle
    orientations = [0, 90, 180, 270]

    neutral_color = P.default_fill_color
    trial_start_msg = None

    #  trial vars
    timed_out = False

    textures = {}
    figures = {}
    stimuli = {}
    masks = {}

    # dynamic trial vars
    mask = None
    mask_label = None
    figure = None
    orientation = None


    def setup(self):
        
        # Stimulus sizes
        
        self.stim_pad = deg_to_px(self.stim_pad)
        self.txtm.add_style('q_and_a', 48, WHITE)
    
        
        # Generate masks, stimuli, and fixations for the experiment
        
        self.__generate_masks()
        self.__generate_stimuli()
        self.__generate_fixations()

        self.trial_start_msg = message("Press any key to advance...", 'default', blit_txt=False)


    def __generate_masks(self):
        smaller_than_screen = True
        while smaller_than_screen:
            self.maximum_mask_size += 1
            new_max_mask_px = deg_to_px(self.maximum_mask_size) + self.mask_blur_width * 4 + 2
            if new_max_mask_px > P.screen_y:
                smaller_than_screen = False
                self.maximum_mask_size -= 1
        for size in self.trial_factory.exp_factors['mask_size']:
            if size > self.maximum_mask_size:
                e_str = "The maximum mask size this monitor can support is {0} degrees.".format(self.maximum_mask_size)
                raise ValueError(e_str)

        clear()
        msg = message("Rendering masks...", "q_and_a", blit_txt=False)
        blit(msg, 5, P.screen_c)
        flip()

        self.masks = {}
        for size in self.trial_factory.exp_factors['mask_size']:
            ui_request()
            self.masks["{0}_{1}".format(CENTRAL, size)] = self.render_mask(size, CENTRAL).render()
            self.masks["{0}_{1}".format(PERIPHERAL, size)] = self.render_mask(size, PERIPHERAL).render()


    def __generate_stimuli(self):
        clear()
        msg = message("Generating stimuli...", "q_and_a", blit_txt=False)
        blit(msg, 5, P.screen_c)
        flip()

        stimuli_labels = [[(False, 0), (CIRCLE, 0)], [(False, 90), (CIRCLE, 0)], [(False, 180), (CIRCLE, 0)],
                          [(False, 270), (CIRCLE, 0)],
                          [(False, 0), (SQUARE, 0)], [(False, 90), (SQUARE, 0)], [(False, 180), (SQUARE, 0)],
                          [(False, 270), (SQUARE, 0)],
                          [(CIRCLE, 0), (False, 0)], [(CIRCLE, 0), (False, 90)], [(CIRCLE, 0), (False, 180)],
                          [(CIRCLE, 0), (False, 270)],
                          [(SQUARE, 0), (False, 0)], [(SQUARE, 0), (False, 90)], [(SQUARE, 0), (False, 180)],
                          [(SQUARE, 0), (False, 270)]]

        for sl in stimuli_labels:
            stim = self.render_texture(sl[1][0], sl[1][1])
            figure = self.render_figure(sl[0][0], sl[0][1])
            stim.putalpha(figure)
            stim = aggdraw_to_numpy_surface(stim)
            fig_text = sl[0][0] if sl[0][0] in (CIRCLE, SQUARE) else "D_%s" % sl[0][1]
            texture_text = sl[1][0] if sl[1][0] in (CIRCLE, SQUARE) else "D_%s" % sl[1][1]
            self.stimuli["{0}_{1}".format(fig_text, texture_text)] = stim.render()


    def __generate_fixations(self):
        
        # Locations
        self.fixation_top     = (P.screen_x / 2,  1 * P.screen_y / 4)
        self.fixation_central = (P.screen_x / 2,  2 * P.screen_y / 4)
        self.fixation_bottom  = (P.screen_x / 2,  3 * P.screen_y / 4)
        self.exp_meta_factors = {"fixation": [self.fixation_top, self.fixation_central, self.fixation_bottom]}
        

    def block(self):
        pass
    

    def setup_response_collector(self):
        self.rc.display_callback = self.screen_refresh
        self.rc.terminate_after = [self.search_time, TK_S]
        self.rc.uses([KeyPressResponse])
        self.rc.keypress_listener.interrupts = True
        self.rc.keypress_listener.key_map = {'z': "circle", '/': "square"}
        self.rc.flip = False # Disable flipping on each rc loop, since callback already flips
    

    def trial_prep(self):
        clear()
        # choose randomly varying parts of trial
        self.orientation = random.choice(self.orientations)
        self.fixation = tuple(random.choice(self.exp_meta_factors['fixation']))

        # infer which mask & stim to use and retrieve them
        self.figure = self.target_shape if self.target_level == LOCAL else False

        if self.figure:
            stim_label = "{0}_D_{1}".format(self.target_shape, self.orientation)
        else:
            stim_label = "D_{0}_{1}".format(self.orientation, self.target_shape)
        self.figure = self.stimuli[stim_label]
        self.mask_label = "{0}_{1}".format(self.mask_type, self.mask_size)
        try:
            self.mask = self.masks[self.mask_label]
        except KeyError:
            self.mask = None  # for the no mask condition, easier than creating empty keys in self.masks
        blit(self.trial_start_msg, 5, P.screen_c)
        flip()
        any_key()
        self.el.drift_correct(self.fixation)


    def trial(self):
        """
        trial_factors: 1 = mask_type, 2 = target_level, 3 = mask_size, 4 = target_shape]
        """
        if P.development_mode:
            print(self.mask_type, self.target_level, self.mask_size, self.target_shape)
        
        self.rc.collect()
        resp = self.rc.keypress_listener.response()
        
        if P.development_mode:
            print(resp)

        # handle timeouts
        if resp.rt == TIMEOUT:
            feedback = CountDown(1)
            msg = message("Too slow!", "alert", blit_txt=False)
            while feedback.counting():
                ui_request()
                fill()
                blit(msg, 5, P.screen_c)
                flip()
            clear()

        #  create readable data as fixation is currrently in (x,y) coordinates

        if self.fixation == self.fixation_top:
            initial_fixation = "TOP"
        elif self.fixation == self.fixation_central:
            initial_fixation = "CENTRAL"
        else:
            initial_fixation = "BOTTOM"

        return {"practicing": P.practicing,
                "response": resp.value,
                "rt": float(resp.rt),
                "mask_type": self.mask_type,
                "mask_size": self.mask_size,
                "local": self.target_shape if self.target_level == LOCAL else "D",
                "global": self.target_shape if self.target_level == GLOBAL else "D",
                "d_orientation": self.orientation,
                "trial_num": P.trial_number,
                "block_num": P.block_number,
                "initial_fixation": initial_fixation}


    def trial_clean_up(self):
        self.fixation = None


    def clean_up(self):
        pass


    def render_texture(self, texture_figure, orientation=None):
        grid_size = (deg_to_px(self.stim_size) + self.stim_pad) * 2
        stim_offset = self.stim_pad // 2
        dc = Image.new('RGB', (grid_size, grid_size), NEUTRAL_COLOR[:3])
        stroke_width = 2  #px
        grid_cell_size = deg_to_px(self.bg_element_size + self.bg_element_pad)
        grid_cell_count = grid_size // grid_cell_size
        stim_offset += (grid_size % grid_cell_size) // 2  # split grid_size %% cells over pad

        # Visual Representation of the Texture Rendering Logic
        # <-------G-------->
        #  _______________   ^
        # |       O       |  |    O = element_offset, ie. 1/2 bg_element_padding
        # |     _____     |  |    E = element (ie. circle, square, D, etc.)
        # |    |     |    |  |    G = one grid length
        # | O  |  E  |  O |  G
        # |    |_____|    |  |
        # |               |  |
        # |_______O_______|  |
        #                    v

        element_offset = self.bg_element_pad // 2  # so as to apply padding equally on all sides of bg elements
        for col in range(0, grid_cell_count):
            for row in range(0, grid_cell_count):
                ui_request()
                top_out = int(row * grid_cell_size + element_offset + stim_offset)
                top_in = top_out + stroke_width  # ie. top_inner
                left_out = int(col * grid_cell_size + element_offset + stim_offset)
                left_in = left_out+ stroke_width
                bottom_out = int(top_out + deg_to_px(self.bg_element_size))
                bottom_in = bottom_out - stroke_width
                right_out = int(left_out + deg_to_px(self.bg_element_size))
                right_in = right_out - stroke_width

                if texture_figure == CIRCLE:
                    ImageDraw.Draw(dc, 'RGB').ellipse((left_out, top_out, right_out, bottom_out), WHITE[:3])
                    ImageDraw.Draw(dc, 'RGB').ellipse((left_in, top_in, right_in, bottom_in), NEUTRAL_COLOR[:3])

                elif texture_figure == SQUARE:
                    ImageDraw.Draw(dc, 'RGB').rectangle((left_out, top_out, right_out, bottom_out), WHITE[:3])
                    ImageDraw.Draw(dc, 'RGB').rectangle((left_in, top_in, right_in, bottom_in), NEUTRAL_COLOR[:3])

                elif texture_figure is False:
                    half_el_width = int(0.5 * deg_to_px(self.bg_element_size))
                    rect_right = right_out - half_el_width
                    ImageDraw.Draw(dc, 'RGB', ).ellipse((left_out, top_out, right_out, bottom_out), WHITE[:3])
                    ImageDraw.Draw(dc, 'RGB', ).ellipse((left_in, top_in, right_in, bottom_in), NEUTRAL_COLOR[:3])
                    ImageDraw.Draw(dc, 'RGB', ).rectangle((left_out, top_out, rect_right, bottom_out), WHITE[:3])
                    ImageDraw.Draw(dc, 'RGB', ).rectangle((left_in, top_in, rect_right, bottom_in), NEUTRAL_COLOR[:3])

        dc = dc.resize((grid_size // 2, grid_size // 2), Image.ANTIALIAS)
        dc = dc.rotate(orientation)

        return dc


    def render_figure(self, figure_shape, orientation):

        stim_size_px = deg_to_px(self.stim_size)
        half_pad = self.stim_pad
        pad = 2 * self.stim_pad
        tl_fig = pad
        br_fig = 2 * stim_size_px
        rect_right = br_fig - stim_size_px
        dc_size = (stim_size_px + half_pad) * 2
        dc = Image.new('L', (dc_size, dc_size), 0)

        if figure_shape == CIRCLE:
            ImageDraw.Draw(dc, 'L').ellipse((tl_fig, tl_fig, br_fig, br_fig), 255)
        if figure_shape == SQUARE:
            ImageDraw.Draw(dc, 'L').rectangle((tl_fig, tl_fig, br_fig, br_fig), 255)
        if figure_shape is False:
            ImageDraw.Draw(dc, 'L').ellipse((tl_fig, tl_fig, br_fig, br_fig), 255)
            ImageDraw.Draw(dc, 'L').rectangle((tl_fig, tl_fig, rect_right, br_fig), 255)

        if orientation > 0:
            dc = dc.rotate(orientation)
        cookie_cutter = dc.resize((dc_size // 2, dc_size // 2), Image.ANTIALIAS)

        return cookie_cutter


    def render_mask(self, diameter, mask_type):
        MASK_COLOR = NEUTRAL_COLOR
        diameter = deg_to_px(diameter)
        blur_width = self.mask_blur_width

        if mask_type != "none":
            
            if mask_type == PERIPHERAL:
                bg_width  = P.screen_x * 2
                bg_height = P.screen_y * 2
                inner_fill = TRANSPARENT
                outer_fill = OPAQUE
                
            elif mask_type == CENTRAL:
                bg_width  = diameter + blur_width * 4 + 2
                bg_height = bg_width
                inner_fill = OPAQUE
                outer_fill = TRANSPARENT
                
            # Create solid background
            bg = Image.new('RGB', (bg_width, bg_height), MASK_COLOR[:3])
    
            # Create an alpha mask
            r  = diameter // 2
            x1 = (bg_width  // 2) - r
            y1 = (bg_height // 2) - r
            x2 = (bg_width  // 2) + r
            y2 = (bg_height // 2) + r
            alpha_mask = Image.new('L', (bg_width, bg_height), outer_fill)
            ImageDraw.Draw(alpha_mask).ellipse((x1, y1, x2, y2), fill=inner_fill)
            alpha_mask = alpha_mask.filter( ImageFilter.GaussianBlur(blur_width) )
    
            # Apply mask to background and render
            bg.putalpha(alpha_mask)
            mask = aggdraw_to_numpy_surface(bg)

        return mask


    def screen_refresh(self):
        position = self.el.gaze()
        fill()
        blit(self.figure, 5, P.screen_c)
        if not position:
            clear()
        else:
            if self.mask is not None:
                blit(self.mask, 5, position)
        flip()
