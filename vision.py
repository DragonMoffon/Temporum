from PIL import Image
from io import BytesIO

import arcade
import arcade.gl as gl

import constants


class VisionCalculator:

    def __init__(self, context: arcade.Window, caster):
        self.ctx = context
        self.caster = caster
        self.map_size = (0, 0)

        self.regenerate = True
        self.recalculate = 2

        self.map_image: Image.Image = None
        self.map_texture = None
        self.vision_texture = None
        self.vision_image: Image.Image = None
        self.buffer = None

        self.geometry = gl.geometry.screen_rectangle(-1, -1, 2, 2)
        self.vision_program = context.ctx.load_program(
            vertex_shader="shaders/arcade_vertex.glsl",
            fragment_shader="shaders/vision_frag.glsl"
        )
        self.draw_tiles_program = context.ctx.load_program(
            vertex_shader="shaders/arcade_vertex.glsl",
            fragment_shader="shaders/vision_to_isometric.glsl"
        )

    def setup(self, map_size):
        self.map_size = map_size
        self.map_image = Image.new("RGBA", map_size)
        self.vision_texture = self.ctx.ctx.texture(map_size, filter=(gl.NEAREST, gl.NEAREST),
                                                   wrap_x=gl.CLAMP_TO_BORDER,
                                                   wrap_y=gl.CLAMP_TO_BORDER)

        self.buffer = self.ctx.ctx.framebuffer(color_attachments=self.vision_texture)

    def modify_map(self, pos, data):
        self.regenerate = True
        self.map_image.putpixel(pos, tuple((255*x for x in data)))

    def calculate(self):
        if self.regenerate:
            self.map_texture = self.ctx.ctx.texture(self.map_size, data=self.map_image.tobytes(),
                                                    filter=(gl.NEAREST, gl.NEAREST))
            self.regenerate = False

        self.buffer.use()
        self.buffer.clear()
        arcade.set_viewport(0, self.map_size[0], 0, self.map_size[1])
        self.map_texture.use(0)
        self.vision_program['cast_pos_resolution'] = self.caster.e_x, self.caster.e_y, *self.map_size
        self.geometry.render(self.vision_program)
        self.ctx.use()
        arcade.set_viewport(self.ctx.view_x, self.ctx.view_x+constants.SCREEN_WIDTH,
                            self.ctx.view_y, self.ctx.view_y+constants.SCREEN_HEIGHT)
        self.vision_image = Image.frombytes("RGBA", self.map_size, bytes(self.vision_texture.read()))

    def draw_prep(self):
        if self.recalculate or self.regenerate:
            self.calculate()
            self.recalculate = 1

    def draw(self):
        if self.map_texture is not None:
            self.vision_texture.use()
            self.draw_tiles_program['screen_pos_resolution'] = [self.ctx.view_x, self.ctx.view_y, *self.map_size]
            self.geometry.render(self.draw_tiles_program)
