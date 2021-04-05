import arcade
import arcade.gl as gl
from array import array


def setup_fullscreen_shader(ctx: arcade.ArcadeContext, fragment_location):
    def pos():
        data = (-1, -1, -1, 3, 3, -1)
        for number in data:
            yield number

    num = pos()
    program = ctx.load_program(
        vertex_shader="shaders/basic_vertex.glsl",
        fragment_shader=fragment_location
    )
    buffer = ctx.buffer(data=array('f', num))
    description = gl.BufferDescription(buffer, '2f', ['in_pos'])
    geometry = ctx.geometry([description])

    return program, buffer, description, geometry
