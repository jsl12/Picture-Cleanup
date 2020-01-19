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
        dup_pre_sel = dup_pre_sel or ['st_size']

        self.output = widgets.Output()

        self.col_select = widgets.SelectMultiple(
            options=df.columns.to_list(),
            value=self.default_columns,
            layout=layouts.col_select
        )
        self.dup_select = widgets.SelectMultiple(
            options=df.columns.to_list(),
            value=dup_pre_sel,
            layout=layouts.col_select
        )

        self.main_grid = qgrid.show_grid(self._df[self.default_columns], **qgrid_opts)
        self.dup_display = qgrid.show_grid(pd.DataFrame(columns=self.default_columns), **qgrid_opts)

        self.dup_type = widgets.Dropdown(
            options={'First': 'first', 'Last': 'last', 'All': False},
            value=False,
            layout=ly(
                flex='1 1 auto',
                width='100%',
                padding='10px'
            )
        )

        self.dup_select.observe(self.main_select, 'value')
        self.col_select.observe(lambda *args, **kwargs: print('value event'), 'value')
        self.dup_type.observe(self.main_select, 'value')
        self.main_grid.on('selection_changed', self.main_select)
        self.col_select.observe(self.refresh, 'value')

    @property
    def widget(self):
        return widgets.VBox(
            children=[
                self.output,
                widgets.HBox(
                    children=[
                        widgets.VBox(
                            children=[
                                widgets.Label('Cols to Show', layout=layouts.select_label),
                                self.col_select
                            ],
                            layout=layouts.flex_col
                        ),
                        widgets.VBox(
                            children=[
                                widgets.Label('Dup Filter Cols', layout=layouts.select_label),
                                self.dup_select
                            ],
                            layout=layouts.flex_col
                        ),
                        widgets.VBox(
                            children=[
                                self.dup_type
                            ],
                            layout=layouts.opts_col
                        )
                    ],
                    layout=ly(height='200px')
                ),
                self.main_grid,
                self.dup_display,
            ],
            layout=layouts.top_level
        )

    def main_select(self, *args, **kwargs):
        with self.output as out:
            clear_output()
            type = self.dup_type.value
            dup_cols = list(self.dup_select.value)
            show_cols = set(list(self.col_select.value) + dup_cols)
            df = self.df[show_cols]
            sel = self.sel.drop_duplicates(dup_cols, keep='first')[show_cols]
            print(f'{sel.shape[0]} files selected')
            if sel.shape[0] == 0:
                return

            dups = df[df.duplicated(dup_cols, keep=type)]
            print(f'Showing duplicates with respect to:\n{", ".join(dup_cols)}')
            res = pd.concat([dups[(row[dup_cols] == dups[dup_cols]).all(axis=1)] for i, row in sel.iterrows()])
            print(f'{res.shape[0]} total files')
        self.dup_display.df = res

    def refresh(self, *args, **kwargs):
        self.main_grid.df = self._df[list(self.col_select.value) + list(self.dup_select.value)]

    @property
    def sel(self):
        return self.main_grid.get_selected_df()

    @property
    def df(self):
        return self.main_grid.get_changed_df()


if __name__ == '__main__':
    df = pd.read_pickle(r'jsl\df.pkl')
    record_id = 'guid'
    df.index = pd.RangeIndex(0, df.shape[0], name=record_id)
    di = DupInterface(
        df,
        qgrid_opts={
            'grid_options': {'forceFitColumns': False},
            'column_definitions': {
                record_id: {'minWidth': 30, 'width': 50},
                'filename': {'minWidth': 80, 'width': 200},
                'path': {'minWidth': 200, 'width': 500},
                'st_size': { 'minWidth': 60, 'width': 80},
            }
        }
    )
    print(di)
