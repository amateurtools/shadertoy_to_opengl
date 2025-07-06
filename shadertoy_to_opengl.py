import tkinter as tk
from tkinter import ttk
import re

def extract_mainimage_and_transform(shader_code):
    """Extract mainImage function and transform it to OpenGL main()"""
    
    # Try multiple patterns to handle different Shadertoy formats
    patterns = [
        # Standard format with 'in' keyword
        re.compile(
            r'void\s+mainImage\s*\(\s*out\s+vec4\s+(\w+)\s*,\s*in\s+vec2\s+(\w+)\s*\)\s*\{',
            re.MULTILINE | re.DOTALL
        ),
        # Format without 'in' keyword (more common in minified code)
        re.compile(
            r'void\s+mainImage\s*\(\s*out\s+vec4\s+(\w+)\s*,\s*vec2\s+(\w+)\s*\)\s*\{',
            re.MULTILINE | re.DOTALL
        ),
        # More flexible whitespace handling
        re.compile(
            r'void\s+mainImage\s*\(\s*out\s+vec4\s+(\w+)\s*,\s*(?:in\s+)?vec2\s+(\w+)\s*\)\s*\{',
            re.MULTILINE | re.DOTALL
        )
    ]
    
    match = None
    for pattern in patterns:
        match = pattern.search(shader_code)
        if match:
            break
    
    if not match:
        return shader_code  # fallback
    
    out_var, coord_var = match.group(1), match.group(2)
    start = match.end()  # Position right after the opening brace
    
    # Find the matching closing brace
    brace_count = 1  # We already have one opening brace
    i = start
    while i < len(shader_code) and brace_count > 0:
        if shader_code[i] == '{':
            brace_count += 1
        elif shader_code[i] == '}':
            brace_count -= 1
        i += 1
    
    if brace_count != 0:
        return shader_code  # fallback - unmatched braces
    
    end = i - 1  # Position of the closing brace
    
    # Extract the body (everything between the braces)
    body = shader_code[start:end]
    before = shader_code[:match.start()]
    after = shader_code[i:]  # Everything after the closing brace
    
    # Build the new main() function
    main_lines = []
    main_lines.append('void main() {')
    main_lines.append(f'    vec2 {coord_var} = gl_FragCoord.xy;')
    main_lines.append(f'    vec4 {out_var} = vec4(0.0);')  # Initialize output variable
    
    # Process body lines and replace only the LAST assignment to output variable
    body_lines = body.split('\n')
    replaced = False
    
    # Go through lines in reverse to find the last assignment
    for idx in range(len(body_lines) - 1, -1, -1):
        line = body_lines[idx]
        
        # Check for assignment to output variable
        assign_match = re.match(r'\s*' + re.escape(out_var) + r'\s*=\s*(.+);', line)
        if assign_match and not replaced:
            expr = assign_match.group(1)
            # For the final assignment, set gl_FragColor
            body_lines[idx] = f'    gl_FragColor = {expr};'
            replaced = True
        else:
            # Add proper indentation to all lines
            if line.strip():
                body_lines[idx] = '    ' + line
            else:
                body_lines[idx] = line
    
    main_lines.extend(body_lines)
    main_lines.append('}')
    
    # Compose the new shader code
    new_code = before.rstrip() + '\n\n' + '\n'.join(main_lines) + '\n' + after.lstrip()
    return new_code

def apply_shadertoy_conventions(shader_code):
    """Apply Shadertoy to OpenGL conversion conventions"""
    
    # 1. Convert texture sampling
    # texture(sampler, uv) -> texture2D(sampler, uv)
    shader_code = re.sub(r'\btexture\s*\(', 'texture2D(', shader_code)
    
    # 2. Convert fragCoord normalization
    # Common pattern: uv = fragCoord/iResolution.xy
    shader_code = re.sub(
        r'(\w+)\s*=\s*(\w+)\s*/\s*iResolution\.xy',
        r'\1 = \2 / iResolution.xy',
        shader_code
    )
    
    # 3. Handle common Shadertoy built-ins that might need conversion
    # Most are already compatible, but we can add precision qualifiers
    
    # 4. Convert mix() calls (should work as-is in OpenGL)
    # 5. Convert smoothstep() calls (should work as-is in OpenGL)
    
    return shader_code

def prepend_uniforms_and_precision(shader_code):
    """Add precision qualifiers and uniforms that are referenced in the code"""
    
    # Precision qualifiers for fragment shaders
    precision_lines = [
        '#ifdef GL_ES',
        'precision mediump float;',
        '#endif',
        ''
    ]
    
    # Standard Shadertoy uniforms
    uniform_defs = {
        'iTime': 'uniform float iTime;',
        'iResolution': 'uniform vec2 iResolution;',
        'iMouse': 'uniform vec4 iMouse;',
        'iFrame': 'uniform int iFrame;',
        'iDate': 'uniform vec4 iDate;',
        'iTimeDelta': 'uniform float iTimeDelta;',
        'iFrameRate': 'uniform float iFrameRate;',
        'iChannelTime': 'uniform float iChannelTime[4];',
        'iChannelResolution': 'uniform vec3 iChannelResolution[4];',
        'iSampleRate': 'uniform float iSampleRate;'
    }
    
    # Check for texture channels
    channel_uniforms = []
    for i in range(4):
        if f'iChannel{i}' in shader_code:
            channel_uniforms.append(f'uniform sampler2D iChannel{i};')
    
    # Only add uniforms that are actually used
    uniforms = [u for key, u in uniform_defs.items() if key in shader_code]
    uniforms.extend(channel_uniforms)
    
    # Combine precision, uniforms, and shader code
    result_lines = precision_lines + uniforms
    if uniforms:
        result_lines.append('')  # Add blank line after uniforms
    
    return '\n'.join(result_lines) + shader_code

def convert_shadertoy_to_opengl(shader_code):
    """Main conversion function"""
    if not shader_code.strip():
        return shader_code
    
    # Step 1: Transform mainImage to main
    code = extract_mainimage_and_transform(shader_code)
    
    # Step 2: Apply Shadertoy conventions
    code = apply_shadertoy_conventions(code)
    
    # Step 3: Add precision qualifiers and uniforms
    code = prepend_uniforms_and_precision(code)
    
    return code

class ShaderToyToOpenGLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shadertoy to OpenGL/JUCE Converter")
        self.geometry("1000x800")
        self.create_widgets()
    
    def create_widgets(self):
        # Header with instructions
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(header_frame, text="Shadertoy to OpenGL Fragment Shader Converter", 
                 font=("Arial", 12, "bold")).pack()
        ttk.Label(header_frame, text="Paste your Shadertoy fragment shader code below:", 
                 font=("Arial", 10)).pack()
        
        # Input section
        input_frame = ttk.Frame(self)
        input_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        input_label_frame = ttk.Frame(input_frame)
        input_label_frame.pack(fill="x")
        ttk.Label(input_label_frame, text="Input (Shadertoy):").pack(side="left")
        ttk.Button(input_label_frame, text="Paste from Clipboard", 
                  command=self.paste_input).pack(side="right")
        
        self.input_text = tk.Text(input_frame, height=15, wrap="none", 
                                 font=("Consolas", 10))
        input_scrollbar = ttk.Scrollbar(input_frame, orient="vertical", 
                                       command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=input_scrollbar.set)
        
        self.input_text.pack(side="left", fill="both", expand=True)
        input_scrollbar.pack(side="right", fill="y")
        
        self.input_text.bind("<KeyRelease>", self.update_output)
        
        # Convert button
        ttk.Button(self, text="Convert", command=self.update_output).pack(pady=5)
        
        # Output section
        output_frame = ttk.Frame(self)
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        output_label_frame = ttk.Frame(output_frame)
        output_label_frame.pack(fill="x")
        ttk.Label(output_label_frame, text="Output (OpenGL/JUCE):").pack(side="left")
        ttk.Button(output_label_frame, text="Copy to Clipboard", 
                  command=self.copy_output).pack(side="right")
        
        self.output_text = tk.Text(output_frame, height=15, wrap="none", 
                                  font=("Consolas", 10))
        output_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", 
                                        command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scrollbar.set)
        
        self.output_text.pack(side="left", fill="both", expand=True)
        output_scrollbar.pack(side="right", fill="y")
        
        self.output_text.config(state="disabled")
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(self, textvariable=self.status_var, relief="sunken").pack(
            side="bottom", fill="x")
    
    def update_output(self, event=None):
        try:
            input_code = self.input_text.get("1.0", "end-1c")
            output_code = convert_shadertoy_to_opengl(input_code)
            
            self.output_text.config(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", output_code)
            self.output_text.config(state="disabled")
            
            self.status_var.set("Conversion complete")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
    
    def copy_output(self):
        try:
            self.output_text.config(state="normal")
            output_code = self.output_text.get("1.0", "end-1c")
            self.output_text.config(state="disabled")
            
            self.clipboard_clear()
            self.clipboard_append(output_code)
            self.status_var.set("Copied to clipboard")
        except Exception as e:
            self.status_var.set(f"Copy error: {str(e)}")
    
    def paste_input(self):
        try:
            clipboard_text = self.clipboard_get()
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", clipboard_text)
            self.update_output()
            self.status_var.set("Pasted from clipboard")
        except tk.TclError:
            self.status_var.set("Clipboard empty or not text")

if __name__ == "__main__":
    app = ShaderToyToOpenGLApp()
    app.mainloop()
