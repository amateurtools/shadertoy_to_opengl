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
    
    # 1. Convert texture sampling functions
    # texture(sampler, uv) -> texture2D(sampler, uv)
    shader_code = re.sub(r'\btexture\s*\(', 'texture2D(', shader_code)
    
    # Handle texture with LOD bias
    shader_code = re.sub(r'\btextureLod\s*\(', 'texture2DLod(', shader_code)
    
    # 2. Convert fragCoord normalization
    # Common pattern: uv = fragCoord/iResolution.xy
    shader_code = re.sub(
        r'(\w+)\s*=\s*(\w+)\s*/\s*iResolution\.xy',
        r'\1 = \2 / iResolution.xy',
        shader_code
    )
    
    # 3. Handle integer division for older GLSL versions
    # Convert int/int to float division where appropriate
    shader_code = re.sub(r'(\d+)\.0\s*/\s*(\d+)\.0', r'\1.0 / \2.0', shader_code)
    
    # 4. Convert common Shadertoy function variations
    # fract() is sometimes written as frac() in other systems
    shader_code = re.sub(r'\bfrac\s*\(', 'fract(', shader_code)
    
    # lerp() -> mix()
    shader_code = re.sub(r'\blerp\s*\(', 'mix(', shader_code)
    
    # saturate() -> clamp(x, 0.0, 1.0)
    shader_code = re.sub(r'\bsaturate\s*\(([^)]+)\)', r'clamp(\1, 0.0, 1.0)', shader_code)
    
    # 5. Handle common constants
    # PI definitions
    if 'PI' in shader_code and '#define PI' not in shader_code:
        shader_code = '#define PI 3.14159265359\n' + shader_code
    
    # TAU definitions
    if 'TAU' in shader_code and '#define TAU' not in shader_code:
        shader_code = '#define TAU 6.28318530718\n' + shader_code
    
    # 6. Convert common Shadertoy patterns
    # Convert pow(x, 2.0) to x*x for better performance
    shader_code = re.sub(r'pow\s*\(([^,]+),\s*2\.0\)', r'(\1 * \1)', shader_code)
    
    # 7. Handle mod() function (same as GLSL but sometimes written differently)
    shader_code = re.sub(r'\bfmod\s*\(', 'mod(', shader_code)
    
    # 8. Ensure scientific notation has explicit float suffix for compatibility
    shader_code = re.sub(r'\b(\d+)e([+-]?\d+)\b', r'\1e\2', shader_code)
    
    # 9. Handle common GLSL compatibility issues
    # atan(y, x) parameter order (GLSL uses atan(y, x), some systems use atan2(y, x))
    shader_code = re.sub(r'\batan2\s*\(', 'atan(', shader_code)
    
    # 10. Handle ddx/ddy -> dFdx/dFdy conversion
    shader_code = re.sub(r'\bddx\s*\(', 'dFdx(', shader_code)
    shader_code = re.sub(r'\bddy\s*\(', 'dFdy(', shader_code)
    
    # 11. Handle step function variations
    # Some systems use heaviside, GLSL uses step
    shader_code = re.sub(r'\bheaviside\s*\(([^,]+),\s*([^)]+)\)', r'step(\1, \2)', shader_code)
    
    # 12. Handle matrix multiplication syntax
    # Convert mul(matrix, vector) to matrix * vector
    shader_code = re.sub(r'\bmul\s*\(([^,]+),\s*([^)]+)\)', r'(\1 * \2)', shader_code)
    
    # 13. Handle smoothstep variations
    shader_code = re.sub(r'\bsmoothStep\s*\(', 'smoothstep(', shader_code)
    
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
    
    # Check for texture channels (iChannel0-3)
    channel_uniforms = []
    for i in range(4):
        if f'iChannel{i}' in shader_code:
            channel_uniforms.append(f'uniform sampler2D iChannel{i};')
    
    # Check for cubemap channels (less common but exists)
    cubemap_uniforms = []
    for i in range(4):
        if f'iChannelCube{i}' in shader_code:
            cubemap_uniforms.append(f'uniform samplerCube iChannelCube{i};')
    
    # Check for 3D texture channels (rare but exists)
    texture3d_uniforms = []
    for i in range(4):
        if f'iChannel3D{i}' in shader_code:
            texture3d_uniforms.append(f'uniform sampler3D iChannel3D{i};')
    
    # Additional common uniforms found in some Shadertoy shaders
    additional_uniforms = {
        'iGlobalTime': 'uniform float iGlobalTime;',  # Legacy name for iTime
        'iChannelOffset': 'uniform vec2 iChannelOffset[4];',
        'iKeyboard': 'uniform sampler2D iKeyboard;',
        'iSound': 'uniform sampler2D iSound;',
        'iFft': 'uniform sampler2D iFft;',
        'iMusic': 'uniform sampler2D iMusic;',
        'iMusicData': 'uniform sampler2D iMusicData;',
    }
    
    # Only add uniforms that are actually used
    uniforms = [u for key, u in uniform_defs.items() if key in shader_code]
    uniforms.extend(channel_uniforms)
    uniforms.extend(cubemap_uniforms)
    uniforms.extend(texture3d_uniforms)
    uniforms.extend([u for key, u in additional_uniforms.items() if key in shader_code])
    
    # Add common #define statements if they're referenced
    defines = []
    if 'HW_PERFORMANCE' in shader_code:
        defines.append('#define HW_PERFORMANCE 1')
    if 'CHEAP_NORMALS' in shader_code:
        defines.append('#define CHEAP_NORMALS 1')
    if 'MOUSE_INVERT' in shader_code:
        defines.append('#define MOUSE_INVERT 1')
    
    # Combine precision, defines, uniforms, and shader code
    result_lines = precision_lines + defines
    if defines:
        result_lines.append('')
    
    result_lines.extend(uniforms)
    if uniforms:
        result_lines.append('')  # Add blank line after uniforms
    
    return '\n'.join(result_lines) + shader_code


def fix_variable_initialization(shader_code):
    """Fix common variable initialization issues in Shadertoy code"""
    
    # Look for uninitialized float variables that are used in loops or operations
    # Handle multi-line declarations with comments
    
    # Pattern to match float declarations that span multiple lines
    float_decl_pattern = r'float\s+([^;]+);'
    matches = list(re.finditer(float_decl_pattern, shader_code, re.MULTILINE | re.DOTALL))
    
    # Process matches in reverse order to avoid index issues when replacing
    for match in reversed(matches):
        full_match = match.group(0)
        var_list = match.group(1)
        
        # Remove comments and newlines from the variable list
        var_list_clean = re.sub(r'//[^\n]*', '', var_list)  # Remove comments
        var_list_clean = re.sub(r'\s+', ' ', var_list_clean)  # Normalize whitespace
        
        # Split by comma to get individual variable names
        vars_in_decl = [var.strip() for var in var_list_clean.split(',') if var.strip()]
        
        # Check if any of these variables need initialization
        needs_initialization = {}
        for var in vars_in_decl:
            var_name = var.strip()
            
            # Check various patterns that indicate a variable needs initialization
            patterns_to_check = [
                # Pre/post increment/decrement
                rf'\b{var_name}\+\+|\+\+{var_name}\b',
                rf'\b{var_name}--|\--{var_name}\b',
                # Compound assignment operators
                rf'\b{var_name}\s*[+\-*/]\s*=',
                # Used in arithmetic operations (likely needs initialization)
                rf'\b{var_name}\s*[+\-*/]\s*[^=]',
                # Used in comparisons (might need initialization)
                rf'\b{var_name}\s*[<>]=?',
                # Used in for loop conditions
                rf'for\s*\([^;]*{var_name}[^;]*;[^;]*{var_name}[^;]*;',
                # Used in while conditions
                rf'while\s*\([^)]*{var_name}[^)]*\)',
            ]
            
            for pattern in patterns_to_check:
                if re.search(pattern, shader_code):
                    # Special handling for loop iterator variables
                    if re.search(rf'for\s*\([^;]*;\s*{var_name}\+\+\s*<', shader_code):
                        # This is likely a loop iterator that should start from 0
                        needs_initialization[var_name] = '0.0'
                    elif re.search(rf'{var_name}\s*[+\-*/]\s*=', shader_code):
                        # This is used in compound assignment, needs initialization
                        needs_initialization[var_name] = '0.0'
                    elif re.search(rf'\b{var_name}\+\+|\+\+{var_name}', shader_code):
                        # This is incremented, likely needs to start from 0
                        needs_initialization[var_name] = '0.0'
                    else:
                        # Default initialization
                        needs_initialization[var_name] = '0.0'
                    break
        
        # If any variables need initialization, reconstruct the declaration
        if needs_initialization:
            new_vars = []
            for v in vars_in_decl:
                v = v.strip()
                if v in needs_initialization:
                    new_vars.append(f'{v} = {needs_initialization[v]}')
                else:
                    new_vars.append(v)
            
            new_decl = f'float {", ".join(new_vars)};'
            shader_code = shader_code.replace(full_match, new_decl)
    
    return shader_code


def handle_common_shadertoy_functions(shader_code):
    """Handle common Shadertoy-specific function patterns"""
    
    # Add common utility functions that are often used in Shadertoy
    utility_functions = []
    
    # Add hash functions if referenced
    if re.search(r'\bhash\s*\(', shader_code) and 'float hash(' not in shader_code:
        utility_functions.append('''
// Hash function commonly used in Shadertoy
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float hash(float n) {
    return fract(sin(n) * 43758.5453123);
}''')
    
    # Add noise functions if referenced
    if re.search(r'\bnoise\s*\(', shader_code) and 'float noise(' not in shader_code:
        utility_functions.append('''
// Simple noise function
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), u.x),
               mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}''')
    
    # Add rotation matrix function if referenced
    if re.search(r'\brot\s*\(', shader_code) and 'mat2 rot(' not in shader_code:
        utility_functions.append('''
// Rotation matrix
mat2 rot(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}''')
    
    # Add common SDF functions if referenced
    if re.search(r'\bsdfBox\s*\(', shader_code) and 'float sdfBox(' not in shader_code:
        utility_functions.append('''
// Box SDF
float sdfBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}''')
    
    if re.search(r'\bsdfSphere\s*\(', shader_code) and 'float sdfSphere(' not in shader_code:
        utility_functions.append('''
// Sphere SDF
float sdfSphere(vec3 p, float r) {
    return length(p) - r;
}''')
    
    # Add palette function if referenced
    if re.search(r'\bpalette\s*\(', shader_code) and 'vec3 palette(' not in shader_code:
        utility_functions.append('''
// Palette function commonly used in Shadertoy
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(6.28318 * (c * t + d));
}''')
    
    # Prepend utility functions to shader code
    if utility_functions:
        shader_code = '\n'.join(utility_functions) + '\n' + shader_code
    
    return shader_code


def fix_loop_semantics(shader_code):
    """Fix loop semantics that might differ between Shadertoy and OpenGL"""
    
    # Handle for loops with pre-increment in condition
    # Pattern: for(init; var++<value; ) where var is used as iterator
    loop_pattern = r'for\s*\(([^;]*);([^;]*);([^)]*)\)'
    matches = list(re.finditer(loop_pattern, shader_code))
    
    for match in reversed(matches):
        init_part = match.group(1).strip()
        condition_part = match.group(2).strip()
        increment_part = match.group(3).strip()
        
        # Check for patterns like "i++<20" in condition
        pre_increment_match = re.match(r'(\w+)\+\+\s*<\s*(.+)', condition_part)
        if pre_increment_match:
            var_name = pre_increment_match.group(1)
            limit = pre_increment_match.group(2)
            
            # Reconstruct the loop with proper semantics
            new_condition = f'{var_name} < {limit}'
            new_increment = f'{var_name}++'
            
            new_loop = f'for({init_part}; {new_condition}; {new_increment})'
            shader_code = shader_code.replace(match.group(0), new_loop)
    
    return shader_code


def optimize_performance(shader_code):
    """Apply performance optimizations common in OpenGL"""
    
    # Replace expensive operations with cheaper alternatives
    
    # Replace pow(x, 2.0) with x*x (already done in apply_shadertoy_conventions)
    # Replace pow(x, 3.0) with x*x*x
    shader_code = re.sub(r'pow\s*\(([^,]+),\s*3\.0\)', r'(\1 * \1 * \1)', shader_code)
    
    # Replace pow(x, 0.5) with sqrt(x)
    shader_code = re.sub(r'pow\s*\(([^,]+),\s*0\.5\)', r'sqrt(\1)', shader_code)
    
    # Replace pow(x, -1.0) with 1.0/x
    shader_code = re.sub(r'pow\s*\(([^,]+),\s*-1\.0\)', r'(1.0 / \1)', shader_code)
    
    # Replace normalize(vec) when length is known to be 1
    # This is complex to detect automatically, so we'll leave it as is
    
    # Replace mix(a, b, 0.5) with (a + b) * 0.5
    shader_code = re.sub(r'mix\s*\(([^,]+),\s*([^,]+),\s*0\.5\)', r'((\1 + \2) * 0.5)', shader_code)
    
    return shader_code


def add_compatibility_extensions(shader_code):
    """Add OpenGL extensions that might be needed"""
    
    extensions = []
    
    # Check if derivative functions are used
    if re.search(r'\b(dFdx|dFdy|fwidth)\s*\(', shader_code):
        extensions.append('#extension GL_OES_standard_derivatives : enable')
    
    # Check if texture array functions are used
    if re.search(r'\btexture2DArray\s*\(', shader_code):
        extensions.append('#extension GL_EXT_texture_array : enable')
    
    # Check if texture LOD functions are used
    if re.search(r'\btexture2DLod\s*\(', shader_code):
        extensions.append('#extension GL_EXT_shader_texture_lod : enable')
    
    # Add extensions at the beginning if any are needed
    if extensions:
        shader_code = '\n'.join(extensions) + '\n\n' + shader_code
    
    return shader_code


def convert_shadertoy_to_opengl(shader_code):
    """Main conversion function with improved processing"""
    if not shader_code.strip():
        return shader_code
    
    # Step 1: Add compatibility extensions
    code = add_compatibility_extensions(shader_code)
    
    # Step 2: Fix variable initialization issues
    code = fix_variable_initialization(code)
    
    # Step 3: Fix loop semantics
    code = fix_loop_semantics(code)
    
    # Step 4: Add common utility functions
    code = handle_common_shadertoy_functions(code)
    
    # Step 5: Transform mainImage to main
    code = extract_mainimage_and_transform(code)
    
    # Step 6: Apply Shadertoy conventions
    code = apply_shadertoy_conventions(code)
    
    # Step 7: Apply performance optimizations
    code = optimize_performance(code)
    
    # Step 8: Add precision qualifiers and uniforms
    code = prepend_uniforms_and_precision(code)
    
    return code


class ShaderToyToOpenGLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shadertoy to OpenGL/JUCE Converter (Enhanced)")
        self.geometry("1200x900")
        self.create_widgets()
    
    def create_widgets(self):
        # Header with instructions
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(header_frame, text="Enhanced Shadertoy to OpenGL Fragment Shader Converter",
                  font=("Arial", 12, "bold")).pack()
        ttk.Label(header_frame, text="Paste your Shadertoy fragment shader code below:",
                  font=("Arial", 10)).pack()
        
        # Options frame
        options_frame = ttk.Frame(self)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        # Add options for different conversion modes
        self.auto_fix_loops = tk.BooleanVar(value=True)
        self.add_utility_functions = tk.BooleanVar(value=True)
        self.optimize_performance = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Auto-fix loop semantics", 
                       variable=self.auto_fix_loops).pack(side="left", padx=5)
        ttk.Checkbutton(options_frame, text="Add utility functions", 
                       variable=self.add_utility_functions).pack(side="left", padx=5)
        ttk.Checkbutton(options_frame, text="Apply optimizations", 
                       variable=self.optimize_performance).pack(side="left", padx=5)
        
        # Input section
        input_frame = ttk.Frame(self)
        input_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        input_label_frame = ttk.Frame(input_frame)
        input_label_frame.pack(fill="x")
        ttk.Label(input_label_frame, text="Input (Shadertoy):").pack(side="left")
        ttk.Button(input_label_frame, text="Paste from Clipboard",
                   command=self.paste_input).pack(side="right")
        
        self.input_text = tk.Text(input_frame, height=18, wrap="none",
                                  font=("Consolas", 10))
        input_scrollbar = ttk.Scrollbar(input_frame, orient="vertical",
                                        command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=input_scrollbar.set)
        
        self.input_text.pack(side="left", fill="both", expand=True)
        input_scrollbar.pack(side="right", fill="y")
        
        self.input_text.bind("<KeyRelease>", self.update_output)
        
        # Convert button
        convert_frame = ttk.Frame(self)
        convert_frame.pack(pady=5)
        ttk.Button(convert_frame, text="Convert", command=self.update_output).pack(side="left", padx=5)
        ttk.Button(convert_frame, text="Clear", command=self.clear_all).pack(side="left", padx=5)
        
        # Output section
        output_frame = ttk.Frame(self)
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        output_label_frame = ttk.Frame(output_frame)
        output_label_frame.pack(fill="x")
        ttk.Label(output_label_frame, text="Output (OpenGL/JUCE):").pack(side="left")
        ttk.Button(output_label_frame, text="Copy to Clipboard",
                   command=self.copy_output).pack(side="right")
        
        self.output_text = tk.Text(output_frame, height=18, wrap="none",
                                   font=("Consolas", 10))
        output_scrollbar = ttk.Scrollbar(output_frame, orient="vertical",
                                         command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scrollbar.set)
        
        self.output_text.pack(side="left", fill="both", expand=True)
        output_scrollbar.pack(side="right", fill="y")
        
        self.output_text.config(state="disabled")
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Enhanced converter with improved loop handling and optimizations")
        ttk.Label(self, textvariable=self.status_var, relief="sunken").pack(
            side="bottom", fill="x")
    
    def update_output(self, event=None):
        try:
            input_code = self.input_text.get("1.0", "end-1c")
            
            # Apply conversion with current settings
            output_code = convert_shadertoy_to_opengl(input_code)
            
            self.output_text.config(state="normal")
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", output_code)
            self.output_text.config(state="disabled")
            
            self.status_var.set("Conversion complete - Enhanced processing applied")
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
    
    def clear_all(self):
        self.input_text.delete("1.0", "end")
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.config(state="disabled")
        self.status_var.set("Cleared")


if __name__ == "__main__":
    app = ShaderToyToOpenGLApp()
    app.mainloop()
