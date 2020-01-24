import ipywidgets as widgets
from ipywidgets import Layout as ly

from . import layouts


class DupBar(widgets.HBox):
    def __init__(self, cols, handler=None, default=['st_size'], **kwargs):
        children = [
               widgets.Dropdown(
                   options={'None': -1, 'First': 'first', 'Last': 'last', 'All': False, 'Only': -2},
                   value=-1,
                   layout=ly(
                       display='flex',
                       width='65px'
                   )
               ),
               widgets.SelectMultiple(
                   options=cols,
                   value=default,
                   layout=ly(
                       display='flex',
                       flex='1 1 0%',
                       align_self='stretch',
                   )
               ),
                widgets.VBox(
                    children=[
                        widgets.HBox(
                            [
                                widgets.Label(text, layout=ly(display='flex', width='50%')),
                                widgets.IntText(0, disabled=True, layout=ly(display='flex', width='50%'))
                            ],
                            layout=ly(
                                display='flex',
                            )
                        )
                        for text in ['Total files', 'Dropped', 'Remaining']
                    ],
                    layout=ly(
                        display='flex',
                        flex='0 1 175px',
                        flex_flow='column nowrap',
                        padding='10px',
                        # border='solid 1px blue',
                    )
                )
        ]

        if 'layout' not in kwargs:
            kwargs['layout'] = layouts.opts_bar

        super().__init__(children, **kwargs)

        if handler is not None:
            self.children[0].observe(handler, 'value')

    @property
    def keep(self):
        return self.children[0].value

    @property
    def cols(self):
        return list(self.children[1].value)

    @property
    def total(self):
        return self.children[-1].children[0].children[-1].value

    @total.setter
    def total(self, value):
        self.children[-1].children[0].children[-1].value = value

    @property
    def dropped(self):
        return self.children[-1].children[1].children[-1].value

    @dropped.setter
    def dropped(self, value):
        self.children[-1].children[1].children[-1].value = value

    @property
    def remaining(self):
        return self.children[-1].children[2].children[-1].value

    @remaining.setter
    def remaining(self, value):
        self.children[-1].children[2].children[-1].value = value