<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# give this back to me in beautiful markup code, but don't mark it up, give it in plain text that will tell the markup program to make it pretty.

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

Here is your content in **plain text with formatting cues** for a markup program to make it visually appealing (such as Markdown, HTML, or a documentation generator). This version uses indentation, line breaks, and clear sectioning for maximum clarity when rendered by a markup tool.

Shadertoy to JUCE Shader Converter
*(this is brand new as of today, so there's still problems that should be fixed soon)*

**Purpose**

This app converts Shadertoy fragment shaders into JUCE/OpenGL-compatible GLSL code, making it easy to use creative shaders in JUCE-based applications and plugins.

**How it works**

1. Paste a Shadertoy fragment shader into the upper window.
2. The lower window instantly emits a JUCE/OpenGL-ready version, with uniforms and entry points adapted.
3. The tool handles most common Shadertoy features and can be extended to support more.

**Supported Features**

- Converts `mainImage` to standard `main` and rewires output to `gl_FragColor`.
- Replaces `fragCoord` with `gl_FragCoord.xy`.
- Declares and injects common uniforms (`iTime`, `iResolution`, `iMouse`, etc.).
- Detects and declares texture channels (`iChannel0`–`iChannel3`).
- Ensures alpha is set to `1.0` in the output color.

**How to Extend Support**

Shadertoy shaders may use a variety of uniforms, features, and idioms. To extend this app:

1. **Identify New Shadertoy Features**

Common advanced features include:
    - Additional uniforms: `iTimeDelta`, `iFrame`, `iDate`, `iChannelTime`, `iChannelResolution`, `iSampleRate`

<div style="text-align: center">⁂</div>

[^1]: https://github.com/juce-framework/JUCE/blob/master/examples/GUI/OpenGLAppDemo.h

[^2]: https://forum.juce.com/t/openglshaderprogram-adding-shaders/11488

[^3]: https://juce.com/tutorials/tutorial_open_gl_application/

[^4]: https://forum.juce.com/t/requested-improvements-to-opengl-shader-support-in-juce/27422

[^5]: https://forum.juce.com/t/opengl-shaders-line-plot/24062

[^6]: https://forum.juce.com/t/graphics-best-practice/42916

[^7]: https://forum.juce.com/t/2d-plug-in-using-opengl/38355

[^8]: https://github.com/juce-framework/JUCE/blob/master/modules/juce_opengl/opengl/juce_OpenGLShaderProgram.h

[^9]: https://forum.juce.com/t/using-framebuffers-as-texture-inputs-for-shaders/40222

