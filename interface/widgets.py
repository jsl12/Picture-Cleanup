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

        self.output = widgets.Output(layout=ly(height='80px'))

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
            layout=layouts.dup_type
        )

        self.button_ext_filter = widgets.ToggleButton(description='Filter Ext', layout=layouts.dup_button)
        self.button_dup_filter = widgets.Button(description='Show Dups', layout=layouts.dup_button)

        self.dup_select.observe(self.main_select, 'value')
        self.col_select.observe(lambda *args, **kwargs: print('value event'), 'value')
        self.dup_type.observe(self.main_select, 'value')
        self.main_grid.on('selection_changed', self.main_select)
        self.col_select.observe(self.refresh, 'value')
        self.button_dup_filter.on_click(self.filter_dups)

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
                                self.button_ext_filter,
                                self.dup_type,
                                self.button_dup_filter
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

    def filter_dups(self, *args, **kwargs):
        res = self._df[self._df.duplicated(list(self.dup_select.value), keep=self.dup_type.value)]
        self.main_grid.df = res
        with self.output as out:
            clear_output()
            print(f'Showing {res.shape[0]} duplicates')

    def main_select(self, *args, **kwargs):
        with self.output as out:
            clear_output()
            keep = self.dup_type.value
            dup_cols = self.dup_cols

            df = self.shown_df
            sel = self.sel.drop_duplicates(dup_cols, keep='first')[self.show_cols]
            print(f'{sel.shape[0]} files selected')

            if sel.shape[0] == 0:
                return

            dups = df[df.duplicated(dup_cols, keep=keep)]
            print(f'Showing duplicates with respect to:\n{", ".join(dup_cols)}')

            res = pd.concat([dups[(row[dup_cols] == dups[dup_cols]).all(axis=1)] for i, row in sel.iterrows()])
            print(f'{res.shape[0]} total files')
        self.dup_display.df = res

    def refresh(self, *args, **kwargs):
        self.main_grid.df = self.shown_df

    @property
    def dup_cols(self):
        return list(self.dup_select.value)

    @property
    def show_cols(self):
        return pd.Series(list(self.col_select.value) + self.dup_cols).drop_duplicates(keep='first').to_list()

    @property
    def sel(self):
        return self.main_grid.get_selected_df()

    @property
    def df(self):
        return self.main_grid.get_changed_df()

    @property
    def shown_df(self):
        if hasattr(self, 'ext'):
            return self._df[pd.DataFrame(data={e: self._df['path'].apply(lambda p: p.suffix.upper()) == e.upper() for e in self.ext}).any(axis=1)][self.show_cols]
        else:
            return self._df[self.show_cols]


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
