from pathlib import Path

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
from ..processing import filter


class DupInterface:
    @staticmethod
    def from_yaml(yaml_path):
        with open(yaml_path, 'r') as file:
            cfg = yaml.load(file, Loader=yaml.SafeLoader)
        interface = DupInterface(
            pd.DataFrame(),
            exclude_folders=cfg['exclude_folders'],
            include_ext=cfg['include_ext'],
            qgrid_opts=cfg.get('qgrid', {}),
            default_columns=cfg.get('default_columns', None),
            dup_pre_sel=cfg.get('default_duplicates', None),
        )

        if 'df' in cfg:
            p = Path(cfg['df'])
            if Path.cwd() in p.parents:
                p = p.relative_to(Path.cwd())
            interface.loader.children[1].value = str(p)

        return interface

    def __init__(
            self,
            df: pd.DataFrame = None,
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
        with self.output:
            clear_output()
            dup_cols = self.dup_bar.cols

            sel = self.sel.drop_duplicates(dup_cols, keep='first')
            print(f'{sel.shape[0]} files selected')

            if sel.shape[0] == 0:
                return

            df = self.df
            dups = df[df.duplicated(dup_cols, keep=False)][self._cols]
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

            print(f' Rendering '.center(20, '-'))
            if not hasattr(self, '_df'):
                print('No DataFrame loaded')
                return

            mask = pd.Series(np.ones(self._df.shape[0], dtype=bool), index=pd.RangeIndex(stop=self._df.shape[0]))

            w = 10
            ext_mask = self.mask_include_ext()
            if ext_mask is not None:
                # print(f'Including ext\n+{ext_mask.sum()} files')
                f = f'+{ext_mask.sum()}'.ljust(w)
                print(f'{f}matched extensions')
                mask &= ext_mask

            exf_mask = self.mask_exclude_folders()
            if exf_mask is not None:
                # print(f'Exclude folders\n-{exf_mask.sum()} files')
                f = f'-{exf_mask.sum()}'.ljust(w)
                print(f'{f}excluded folders')
                mask &= ~exf_mask

            self.dup_bar.total = mask.sum()

            msg = {
                -2: 'keep only dups',
                -1: 'keep all dups',
                0: 'drop all dups',
                'first': 'keep first',
                'last': 'keep last'
            }
            dup_mask = self.mask_duplicates()
            if dup_mask is not None:
                mask &= ~dup_mask
                self.dup_bar.dropped = dup_mask.sum()
                print(('-' + str(dup_mask.sum())).ljust(w) + msg[self.dup_bar.keep])

            for c in self._cols:
                if c not in self._df.columns:
                    self._cols.pop(self._cols.index(c))
                    print(f'Missing column: {c}')

            self.dup_bar.remaining = mask.sum()
            print('-' * int(w / 2))
            print(str(mask.sum()).ljust(w) + 'remaining')

            self._mask = mask
            res = self._df[mask][self._cols]
            self.qg.df = res

    @property
    def exclude_folders(self):
        return list(self.exclude_section.children[0].children[-1].value)

    def mask_exclude_folders(self):
        self._mask_exf = filter.filter_path(self._df, self.exclude_folders, 'path')
        if self.exclude_section.children[0].children[0].value:
            return self._mask_exf

    @property
    def include_ext(self):
        return list(self.exclude_section.children[1].children[-1].value)

    def mask_include_ext(self):
        self._mask_ext = filter.filter_extension(self._df, self.include_ext, 'path')
        if self.exclude_section.children[1].children[0].value:
            return self._mask_ext

    def mask_duplicates(self):
        if self.dup_bar.keep == -1:
            self._mask_dups = pd.Series(np.zeros(self._df.shape[0]), dtype=bool, index=self._df.index)
        elif self.dup_bar.keep == -2:
            self._mask_dups = ~self._df.duplicated(self.dup_bar.cols, keep=False)
        else:
            self._mask_dups = self._df.duplicated(self.dup_bar.cols, keep=self.dup_bar.keep)
        return self._mask_dups


if __name__ == '__main__':
    pass
