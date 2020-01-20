from tkinter import filedialog, Tk

import ipywidgets as widgets
import pandas as pd
import qgrid
from ipywidgets import Layout as ly

from . import layouts


class FileBar(widgets.HBox):
    def __init__(self, button_text, output=None, **kwargs):
        children = [
            widgets.Button(
                description=button_text,
                layout=ly(
                    display='flex',
                    flex='0 1 85px'
                )
            ),
            widgets.Text(
                layout=ly(
                    display='flex',
                    flex='1 1 auto'
                )
            ),
            widgets.Button(
                description='Browse',
                layout=ly(
                    display='flex',
                    flex='0 1 65px'
                )
            )
        ]
        if 'layout' not in kwargs:
            kwargs['layout'] = layouts.opts_bar

        if output is not None:
            self.output = output

        super().__init__(children, **kwargs)


class LoadBar(FileBar):
    def __init__(self, qgrid_obj, handler, **kwargs):
        self.qg = qgrid_obj
        super().__init__(button_text='Load Pickle', **kwargs)
        self.children[0].on_click(handler)
        self.children[2].on_click(self.browse_file)

    def browse_file(self, *args):
        root = Tk()
        root.withdraw()
        root.call('wm', 'attributes', '.', '-topmost', True)
        file = filedialog.askopenfilename(initialdir = "./", title = "Select file", multiple=False)
        self.children[1].value = str(file)
        root.destroy()

    def load_file(self, *args):
        try:
            df = pd.read_pickle(self.children[1].value)
        except Exception as e:
            self.print(f'Failed to read')
        else:
            self.print(f'Read {df.shape[0]} lines')
        df.index = pd.RangeIndex(stop=df.shape[0], name='guid')
        return df

    def print(self, s):
        if hasattr(self, 'output'):
            with self.output:
                print(s)


class SaveBar(FileBar):
    def __init__(self, qgrid_obj: qgrid.QGridWidget, **kwargs):
        self.qg = qgrid_obj
        super().__init__(button_text='Save Pickle', **kwargs)
        self.children[0].on_click(self.save)
        self.children[2].on_click(self.browse)

    def save(self, *args):
        with self.output:
            if self.children[1].value != '':
                df = self.qg.get_changed_df()
                try:
                    df.to_pickle(self.children[1].value)
                except Exception as e:
                    print(f'Failed saving\n{repr(e)}')
                else:
                    print(f'Saved')
            else:
                print('No file selected to save')

    def browse(self, *args):
        root = Tk()
        root.withdraw()
        root.call('wm', 'attributes', '.', '-topmost', True)
        file = filedialog.asksaveasfilename(initialdir = "./", title = "Select file", filetypes = (("pickle files","*.pkl"),("all files","*.*")))
        self.children[1].value = str(file)
        root.destroy()
