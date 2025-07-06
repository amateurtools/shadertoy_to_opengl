import tkinter as tk
from tkinter import ttk
import re

def convert_shadertoy_to_juce(shader_code):
    # Match mainImage with any indentation for the closing brace
    mainimage_regex = re.compile(
        r'void\s+mainImage\s*\(\s*out\s+vec4\s+(\w+)\s*,\s*in\s*vec2\s+(\w+)\s*\)\s*\{([\s\S]*?)\n\}', 
        re.MULTILINE
    )
    match = mainimage_regex.search(shader_code)
    if not match:
        # If no mainImage, just return with uniforms prepended
        return prepend_uniforms(shader_code)

    out_var, coord_var, body = match.groups()

    # Remove the mainImage function from the original code
    code_wo_mainimage = mainimage_regex.sub('', shader_code)

    # Prepare the main() function
    main_lines = []
    main_lines.append('void main() {')
    main_lines.append(f'    vec2 {coord_var} = gl_FragCoord.xy;')
    main_lines.append(f'    vec4 {out_var} = vec4(0.0);')

    # Indent and insert the mainImage body, replacing output assignments at the end with gl_FragColor
    body_lines = body.split('\n')
    for line in body_lines:
        assign_match = re.match(r'\s*' + re.escape(out_var) + r'\s*=\s*(.+);', line)
        if assign_match and ('gl_FragColor' not in line):
            expr = assign_match.group(1)
            main_lines.append(f'    gl_FragColor = vec4({expr}.rgb, 1.0);')
        else:
            main_lines.append('    ' + line)

    main_lines.append('}')
    main_func = '\n'.join(main_lines)

    # Remove any trailing whitespace and blank lines
    code_wo_mainimage = code_wo_mainimage.rstrip('\n')

    # Prepend uniforms, append helper functions and main()
    return prepend_uniforms(code_wo_mainimage + '\n\n' + main_func)

def prepend_uniforms(shader_code):
    # Only add uniforms that are referenced in the code
    uniform_defs = {
        'iTime':      'uniform float iTime;',
        'iResolution':'uniform vec2 iResolution;',
        'iMouse':     'uniform vec4 iMouse;',
        'iFrame':     'uniform int iFrame;',
        'iDate':      'uniform vec4 iDate;',
    }
    channel_uniforms = []
    for i in range(4):
        if f'iChannel{i}' in shader_code:
            channel_uniforms.append(f'uniform sampler2D iChannel{i};')
    uniforms = [u for key, u in uniform_defs.items() if key in shader_code]
    uniforms.extend(channel_uniforms)
    return '\n'.join(uniforms) + '\n' + shader_code

# ... rest of your Tkinter code ...
