import ipywidgets as widgets
from ipywidgets import Layout as ly

from . import layouts


class FilterCol(widgets.VBox):
    def __init__(self, options, description=None, **kwargs):

        if 'layout' not in kwargs:
            kwargs['layout'] = layouts.exclude_col

        children = [
            widgets.ToggleButton(
                description=description or 'Exclude',
                value=True,
                layout=ly(
                    display='flex',
                    align_self='center',
                    # flex='1 1 auto',
                )
            ),
            widgets.SelectMultiple(
                options=options,
                value=options,
                layout=ly(
                    display='flex',
                    align_self='center',
                    flex='1 1 0%',
                    width='85%'
                )
            )
        ]

        super().__init__(children, **kwargs)

class FilterSection(widgets.HBox):
    def __init__(self, options, descriptions, **kwargs):
        if 'layout' not in kwargs:
            kwargs['layout'] = layouts.exclude_section

        children = [FilterCol(opts, desc) for opts, desc in zip(options, descriptions)]

        super().__init__(children, **kwargs)