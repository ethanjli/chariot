#version 120

varying vec4 v_base_color;

void main() {
    gl_Position = $doc_to_render($visual_to_doc(vec4($position, 1.0)));
    v_base_color = vec4($color, 1.0);
}
