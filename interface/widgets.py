import ipywidgets as widgets
import numpy as np
import pandas as pd
import qgrid
import yaml
from IPython.display import clear_output

from . import layouts
from .dupbar import DupBar
from .excbar import FilterSection
from .filebar import LoadBar, SaveBar


class DupInterface:
    @staticmethod
    def from_yaml(yaml_path):
        with open(yaml_path, 'r') as file:
            cfg = yaml.load(file, Loader=yaml.SafeLoader)
        return DupInterface(
                pd.DataFrame(),
                qgrid_opts=cfg.get('qgrid', {}),
                default_columns=cfg.get('default_columns', None),
                dup_pre_sel=cfg.get('default_duplicates', None),
                exclude_folders=cfg['exclude_folders'],
                include_ext=cfg['ext']
        )

    def __init__(
            self,
            df:pd.DataFrame = None,
            qgrid_opts=None,
            exclude_folders=None,
            include_ext=None,
            default_columns=None,
            dup_pre_sel=None,
    ):
        if df is not None:
            self._df = df

        self._cols = default_columns or ['filename', 'st_size', 'path']

        self.output = widgets.Output(layout=layouts.output)

        dup_pre_sel = dup_pre_sel or ['st_size']
        self.dup_bar = DupBar(self._cols, self.render, default=dup_pre_sel)

        self.qg = qgrid.show_grid(pd.DataFrame(columns=self._cols), **(qgrid_opts or {}))
        self.qg_dup = qgrid.show_grid(pd.DataFrame(columns=self._cols), **(qgrid_opts or {}))

        self.qg.on('selection_changed', self.main_select)
        self.loader = LoadBar(self.qg, handler=self.reload, output=self.output)
        self.saver = SaveBar(self.qg, output=self.output)

        self.exclude_section = FilterSection(
            options=[
                exclude_folders,
                include_ext
            ],
            descriptions=[
                'Exclude Folders',
                'Include Extensions'
            ]
        )

    @property
    def widget(self):
        return widgets.VBox(
            children=[
                self.options_section,
                widgets.Label('Modified file list'),
                self.qg,
                widgets.Label('Duplicates of selected files'),
                self.qg_dup
            ],
            layout=layouts.top_level
        )

    @property
    def options_section(self):
        return widgets.HBox(
            children=[
                widgets.VBox(
                    children=[
                        self.loader,
                        self.saver,
                        self.exclude_section,
                        self.dup_bar
                    ],
                    layout=layouts.options_container
                ),
                self.output
            ],
            layout=layouts.options_section
        )

    def main_select(self, *args):
        with self.output as out:
            clear_output()
            dup_cols = self.dup_bar.cols

            sel = self.sel.drop_duplicates(dup_cols, keep='first')
            print(f'{sel.shape[0]} files selected')

            if sel.shape[0] == 0:
                return

            dups = self._df[self._df.duplicated(dup_cols, keep=False)][self._cols]
            # print(f'Showing duplicates with respect to:\n{", ".join(dup_cols)}')

            res = pd.concat([dups[(row[dup_cols] == dups[dup_cols]).all(axis=1)] for i, row in sel.iterrows()])
            print(f'{res.shape[0]} total duplicates')
        self.qg_dup.df = res

    @property
    def sel(self):
        return self.qg.get_selected_df()

    @property
    def df(self):
        return self.qg.get_changed_df()

    def reload(self, *args):
        with self.output:
            clear_output()
        self._df = self.loader.load_file(*args)
        self.render(clear=False)

    def render(self, *args, **kwargs):
        with self.output:
            if kwargs.get('clear', True):
                clear_output()

            print(f'Rendering')
            if not hasattr(self, '_df'):
                print('No DataFrame loaded')
                return

            self.mask = pd.Series(np.ones(self._df.shape[0], dtype=bool), index=pd.RangeIndex(stop=self._df.shape[0]))

            if hasattr(self, 'exclude_section') and self.exclude_section.children[0].children[0].value:
                exclude_folders = list(self.exclude_section.children[0].children[-1].value)
                print(f'Excluding folders')
                for f in exclude_folders:
                    print(f' - {f}')

                exf_mask = pd.DataFrame(
                    {folder: self._df['path'].apply(str).str.contains(folder, case=False) for folder in
                     exclude_folders}).any(axis=1)
                self.mask &= ~exf_mask

            if hasattr(self, 'exclude_section') and self.exclude_section.children[1].children[0].value:
                include_ext = list(self.exclude_section.children[1].children[-1].value)
                print(f'Including ext')
                for e in include_ext:
                    print(f' - {e}')

                ext_mask = pd.DataFrame(
                    {ext: self._df['filename'].str.contains(ext, case=False) for ext in include_ext}
                ).any(axis=1)
                self.mask &= ext_mask

            self.dup_bar.total = self._df[self.mask].shape[0]
            if hasattr(self, 'dup_bar'):
                msg = {
                    -1: 'Keep all files',
                    0: 'Drop all duplicates',
                    'first': 'Keep first of duplicates',
                    'last': 'Keep last of duplicates'
                }
                print(f'{msg[self.dup_bar.keep]}')
                if self.dup_bar.keep != -1:
                    dups = self._df.duplicated(self.dup_bar.cols, keep=self.dup_bar.keep)
                    self.mask &= ~dups

                    self.dup_bar.dropped = self._df[dups].shape[0]

            try:
                res = self._df[self.mask][self._cols]
            except KeyError as e:
                print(f'{repr(e)}')
                for c in self._df:
                    print(f'  {c}')
                return
            else:
                self.dup_bar.remaining = res.shape[0]
                self.qg.df = res


if __name__ == '__main__':
    pass
