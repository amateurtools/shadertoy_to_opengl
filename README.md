Shadertoy to JUCE Shader Converter
(this is brand new as of today, so there's still problems that should be fixed soon)

Purpose:

This app converts Shadertoy fragment shaders into JUCE/OpenGL-compatible
 GLSL code, making it easy to use creative shaders in JUCE-based 
applications and plugins.


How it works:




Paste a Shadertoy fragment shader into the upper window.




The lower window instantly emits a JUCE/OpenGL-ready version, with uniforms and entry points adapted.




The tool handles most common Shadertoy features and can be extended to support more.




Supported Features




Converts mainImage to standard main and rewires output to gl_FragColor.




Replaces fragCoord with gl_FragCoord.xy.




Declares and injects common uniforms (iTime, iResolution, iMouse, etc.).




Detects and declares texture channels (iChannel0–iChannel3).




Ensures alpha is set to 1.0 in the output color.




How to Extend Support


Shadertoy shaders may use a variety of uniforms, features, and idioms. To extend this app:


1. Identify New Shadertoy Features


Common advanced features include:




Additional uniforms: iTimeDelta, iFrame, iDate, iChannelTime, iChannelResolution, iSampleRate




Texture and buffer handling: Multi-pass, feedback, and sound




Mouse/keyboard input: iMouse




Sound input/output




2. Update the Converter Logic




Uniforms:

Add detection and declaration for new uniforms. For example, if you see iTimeDelta used, ensure uniform float iTimeDelta; is injected at the top.




Textures:

Detect iChannel0–iChannel3 and declare as uniform sampler2D. For more advanced uses (e.g., 3D textures or buffers), flag for manual handling.




Output:

Always ensure output is assigned to gl_FragColor with alpha = 1.0.




Entry Points:

Some shaders use custom entry points or functions—ensure the main rendering logic is moved into main() and uses OpenGL conventions.




3. GUI/UX Enhancements




Add warnings or notes in the output if a feature is 
detected that needs manual JUCE-side setup (e.g., "This shader uses 
iChannel0; you must bind a texture in JUCE").




Add a status bar or info window to show which features were detected and how they were handled.




4. Testing




Use real Shadertoy examples that use the new features.




Compare the output in JUCE with the original Shadertoy result.




Prompt for LLMs or Contributors


Prompt:

This project is a Python/Tkinter GUI app that converts Shadertoy fragment shaders into JUCE/OpenGL-compatible GLSL code.




The app parses pasted Shadertoy code, rewrites the entry point and output, and injects uniform declarations as needed.




It aims to maximize compatibility and minimize manual editing for JUCE developers.




To extend, add support for more Shadertoy uniforms, input types, and idioms by updating the conversion logic.




All new features should be detected automatically and 
handled gracefully, with clear feedback to the user if manual JUCE-side 
setup is required.




When extending:




Identify new Shadertoy features in the input.




Update the conversion logic to handle them.




Ensure the output is valid GLSL for OpenGL 2.1+/JUCE.




Document any limitations or manual steps required for full functionality.




Example: Adding Support for iTimeDelta




Detection:

If iTimeDelta is found in the input, inject uniform float iTimeDelta; at the top of the output.




User Notification:

If possible, add a note: "This shader uses iTimeDelta; you must set this uniform from your JUCE code."




Testing:

Paste a Shadertoy shader using iTimeDelta and verify the output.




References




Shadertoy Uniforms Documentation




[JUCE OpenGL Tutorial]




Contributions and suggestions are welcome!

If you add support for a new feature, please update this README and add 
an example shader that demonstrates the new functionality.


[Example Shadertoy-to-ZGameEditor Converter]


