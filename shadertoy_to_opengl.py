import tkinter as tk
from tkinter import ttk

def convert_shadertoy_to_juce(shader_code):
    import re

    # 1. Find and replace mainImage with main, and handle fragCoord/fragColor
    mainimage_pattern = re.compile(
        r'void\s+mainImage\s*\(\s*out\s+vec4\s+(\w+)\s*,\s*in\s*vec2\s*(\w+)\s*\)', re.MULTILINE)
    match = mainimage_pattern.search(shader_code)
    if match:
        out_var, coord_var = match.group(1), match.group(2)
        # Remove mainImage header and replace with main
        shader_code = mainimage_pattern.sub('void main()', shader_code)
        # Replace all instances of coord_var with gl_FragCoord.xy
        shader_code = re.sub(r'\b{}\b'.format(coord_var), 'gl_FragCoord.xy', shader_code)
        # Replace output var assignment with gl_FragColor
        shader_code = re.sub(r'\b{}\b\s*='.format(out_var), 'gl_FragColor =', shader_code)
        # Ensure final output has alpha=1.0
        shader_code = re.sub(
            r'gl_FragColor\s*=\s*([^\n;]+);',
            r'gl_FragColor = vec4(\1.rgb, 1.0);',
            shader_code
        )

    # 2. Ensure required uniforms are present
    required_uniforms = [
        'uniform float iTime;',
        'uniform vec2 iResolution;',
        'uniform vec4 iMouse;',
        'uniform int iFrame;',
        'uniform vec4 iDate;',
    ]
    for uniform in required_uniforms:
        if uniform.split()[2] not in shader_code:
            shader_code = uniform + '\n' + shader_code

    # 3. Handle iChannel0-3 (textures)
    for i in range(4):
        sampler_decl = f'uniform sampler2D iChannel{i};'
        if f'iChannel{i}' in shader_code and sampler_decl not in shader_code:
            shader_code = sampler_decl + '\n' + shader_code

    # 4. Remove Shadertoy-specific comments or extra functions if needed (optional)

    return shader_code

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

        self.copy_button = ttk.Button(self, text="Copy Output", command=self.copy_output)
        self.copy_button.pack(pady=8)

    def update_output(self, event=None):
        input_code = self.input_text.get("1.0", "end-1c")
        output_code = convert_shadertoy_to_juce(input_code)
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", output_code)
        self.output_text.config(state="disabled")

    def copy_output(self):
        output_code = self.output_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(output_code)

if __name__ == "__main__":
    app = ShaderToyToJUCEApp()
    app.mainloop()
