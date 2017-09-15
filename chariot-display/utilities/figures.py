"""Helper functions for working with matplotlib figures."""
try:
    from StringIO import StringIO
except:
    from io import StringIO

import svgutils

def to_svg(fig, **kwargs):
    fid = StringIO()
    try:
        fig.savefig(fid, format='svg', **kwargs)
    except ValueError:
        raise(ValueError, 'No matplotlib SVG backend')
    fid.seek(0)
    svg_fig = svgutils.transform.fromstring(fid.read())

    (width, height) = svg_fig.get_size()
    svg_fig.set_size((width.replace('pt', ''), height.replace('pt', '')))

    return svg_fig

