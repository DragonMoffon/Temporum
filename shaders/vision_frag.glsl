#version 330

uniform sampler2D vision_map;
uniform vec4 cast_pos_resolution;
uniform bool lit;

float one_step = 1/cast_pos_resolution.z;

in vec2 frag_uv;

out vec4 frag_color;

float point_cast(ivec2 start_point, ivec2 cast_point)
{
    vec4 walls;

    int dx = cast_point.x-start_point.x, dy = cast_point.y-start_point.y;
    int nx = abs(dx), ny = abs(dy);
    int step_x = dx > 0? 1: -1, step_y = dy > 0? 1: -1;

    bool hit = false;
    bool x = false;

    ivec2 point = start_point;
    int ix, iy = 0;
    walls = texelFetch(vision_map, point, 0);

    float xcheckin, xcheckout, ycheckin, ycheckout;

    if (step_x > 0)
    {
        xcheckin = walls.a, xcheckout = walls.g;
    }
    else
    {
        xcheckin = walls.g, xcheckout = walls.a;
    }

    if (step_y > 0)
    {
        ycheckin = walls.b, ycheckout = walls.r;
    }
    else
    {
        ycheckin = walls.r, ycheckout = walls.b;
    }


    if ((0.5+ix) / nx < (0.5+iy) / ny)
    {
        x = true;
        if (xcheckout < 1)
        {
            hit = true;
        }
    }
    else
    {
        if (ycheckout < 1)
        {
            hit = true;
        }
    }

    if (!hit)
    {
        float check;

        while (ix < nx || iy < ny)
        {
            if ((0.5+ix) / nx < (0.5+iy) / ny)
            {
                point.x += step_x;
                ix++;
                x = true;
                if (xcheckout < 1)
                {
                    hit = true;
                }
            }
            else
            {
                point.y += step_y;
                iy++;
                x = false;
                if (ycheckout < 1)
                {
                    hit = true;
                }
            }

            walls = texelFetch(vision_map, point, 0);

            if (step_x > 0)
            {
                xcheckin = walls.a, xcheckout = walls.g;
            }
            else
            {
                xcheckin = walls.g, xcheckout = walls.a;
            }

            if (step_y > 0)
            {
                ycheckin = walls.b, ycheckout = walls.r;
            }
            else
            {
                ycheckin = walls.r, ycheckout = walls.b;
            }

            check = x? xcheckin: ycheckin;

            if (check < 1)
            {
                hit = true;
            }
        }
    }


    if (hit)
    {
        return 0.0;
    }

    return 1.0;

}



void main()
{
    vec2 cast_pos = (cast_pos_resolution.xy + vec2(1))/cast_pos_resolution.zw;
    ivec2 pos = ivec2(frag_uv*cast_pos_resolution.zw);

    vec2 cast_pos_square = (cast_pos_resolution.xy) * one_step;
    vec2 pos_square = pos * one_step;
    float dist = distance(cast_pos_square, pos_square);
    if (dist < 15/cast_pos_resolution.z || lit)
    {
        frag_color = vec4(point_cast(ivec2(frag_uv*cast_pos_resolution.zw), ivec2(cast_pos_resolution.xy)), dist, 1, 1);
    }
    else
    {
        frag_color = vec4(0, 0, 1, 1);
    }

}