import ipywidgets as widgets
import pandas as pd
import qgrid
from IPython.display import clear_output
from ipywidgets import Layout as ly

from . import layouts


class DupInterface:
    def __init__(self, df:pd.DataFrame, qgrid_opts, default_columns=None, dup_pre_sel=None, **kwargs):
        self._df = df
        self.default_columns = default_columns or ['filename', 'st_size', 'path']
        self._cols = self.default_columns
        dup_pre_sel = dup_pre_sel or ['st_size']

        self.output = widgets.Output(layout=ly(height='80px'))

        self.main_grid = qgrid.show_grid(self.df, **qgrid_opts)
        self.dup_display = qgrid.show_grid(pd.DataFrame(columns=self.default_columns), **qgrid_opts)

        self.dup_bar = DupBar(self._cols, self.drop_dups)
        self.main_grid.on('selection_changed', self.main_select)

    @property
    def widget(self):
        return widgets.VBox(
            children=[
                self.dup_bar,
                self.main_grid,
                self.dup_display,
            ],
            layout=layouts.top_level
        )

    def drop_dups(self, *args, **kwargs):
        with self.dup_bar.out:
            clear_output()
            df = self.df
            if self.dup_bar.keep == -1:
                self.main_grid.df = df
                print(f'Reset table - including all duplicates')
            else:
                dups = df.duplicated(self.dup_bar.cols, keep=self.dup_bar.keep)
                dropped = df[dups]
                res = df[~dups]
                print(f'{"Initial size:":20}{df.shape[0]}')
                print(f'{"Dropped:":20}{dropped.shape[0]}')
                print(f'{"Remaining:":20}{res.shape[0]}')
                self.main_grid.df = res

    def main_select(self, *args, **kwargs):
        with self.output as out:
            clear_output()
            keep = self.dup_type.value
            dup_cols = self.dup_bar.cols

            df = self.df
            sel = self.sel.drop_duplicates(dup_cols, keep='first')[self._cols]
            print(f'{sel.shape[0]} files selected')

            if sel.shape[0] == 0:
                return

            dups = df[df.duplicated(dup_cols, keep=keep)]
            print(f'Showing duplicates with respect to:\n{", ".join(dup_cols)}')

            res = pd.concat([dups[(row[dup_cols] == dups[dup_cols]).all(axis=1)] for i, row in sel.iterrows()])
            print(f'{res.shape[0]} total files')
        self.dup_display.df = res

    @property
    def dup_cols(self):
        return list(self.dup_bar.children[2].value)

    @property
    def sel(self):
        return self.main_grid.get_selected_df()

    @property
    def dfx(self):
        return self.main_grid.get_changed_df()

    @property
    def df(self):
        return self._df[self._cols]


class DupBar(widgets.HBox):
    def __init__(self, cols, handler=None, default=['st_size'], **kwargs):
        children = [
               widgets.Dropdown(
                   options={'None': -1, 'First': 'first', 'Last': 'last', 'All': False},
                   value=-1,
                   layout=ly(
                       display='flex',
                       # flex='1 1 0%',
                       width='65px'
                   )
               ),
               widgets.SelectMultiple(
                   options=cols,
                   value=default,
                   layout=ly(
                       display='flex',
                       flex='1 1 0%',
                   )
               ),
               widgets.Output(
                   layout=ly(
                       display='flex',
                       flex='1 1 0%',
                   )
               )
        ]

        if 'layout' not in kwargs:
            kwargs['layout'] = ly(
                display='flex',
                flex='1 1 auto',
                width='100%'
            )

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
    def out(self):
        return self.children[-1]


if __name__ == '__main__':
    pass
