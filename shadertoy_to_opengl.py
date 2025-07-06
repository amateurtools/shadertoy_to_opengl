import tkinter as tk
from tkinter import ttk
import re

def convert_shadertoy_to_juce(shader_code):
    # 1. Extract mainImage signature and body
    mainimage_regex = re.compile(
        r'void\s+mainImage\s*\(\s*out\s+vec4\s+(\w+)\s*,\s*in\s*vec2\s+(\w+)\s*\)\s*\{([\s\S]*?)^\}', 
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
    main_lines.append('    vec2 {} = gl_FragCoord.xy;'.format(coord_var))
    main_lines.append('    vec4 {} = vec4(0.0);'.format(out_var))

    # Indent and insert the mainImage body
    body_lines = body.split('\n')
    for line in body_lines:
        # Replace output assignments at the end with gl_FragColor
        # If line assigns to out_var and is not a compound assignment (+=, -=, etc.)
        assign_match = re.match(r'\s*' + re.escape(out_var) + r'\s*=\s*(.+);', line)
        if assign_match and ('gl_FragColor' not in line):
            expr = assign_match.group(1)
            # Ensure alpha is set to 1.0
            main_lines.append('    gl_FragColor = vec4({}.rgb, 1.0);'.format(expr))
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
    # Compose the list of uniforms to prepend
    uniforms = [u for key, u in uniform_defs.items() if key in shader_code]
    uniforms.extend(channel_uniforms)
    return '\n'.join(uniforms) + '\n' + shader_code

class ShaderToyToJUCEApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shadertoy to JUCE Shader Converter")
        self.geometry("900x700")
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Paste Shadertoy Fragment Shader Code Below:").pack(anchor="w", padx=8, pady=(8,0))
        self.input_text = tk.Text(self, height=18, wrap="word", font=("Consolas", 11))
        self.input_text.pack(fill="both", expand=False, padx=8)
        self.input_text.bind("<KeyRelease>", self.update_output)

        ttk.Label(self, text="JUCE/OpenGL Compatible Shader Output:").pack(anchor="w", padx=8, pady=(10,0))
        self.output_text = tk.Text(self, height=18, wrap="word", font=("Consolas", 11))
        self.output_text.pack(fill="both", expand=True, padx=8)
        self.output_text.config(state="disabled")

        # Add the copy button below the output window
        self.copy_button = ttk.Button(self, text="Copy Output to Clipboard", command=self.copy_output)
        self.copy_button.pack(pady=(8, 16))  # Extra bottom padding for clarity

    def update_output(self, event=None):
        input_code = self.input_text.get("1.0", "end-1c")
        output_code = convert_shadertoy_to_juce(input_code)
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", output_code)
        self.output_text.config(state="disabled")

    def copy_output(self):
        self.output_text.config(state="normal")
        output_code = self.output_text.get("1.0", "end-1c")
        self.output_text.config(state="disabled")
        self.clipboard_clear()
        self.clipboard_append(output_code)

if __name__ == "__main__":
    app = ShaderToyToJUCEApp()
    app.mainloop()
