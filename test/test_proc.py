from cleanup import sorter
import unittest
import pandas as pd

class ProcTest(unittest.TestCase):
    def setUp(self) -> None:
        self.df = pd.read_pickle(r'test.pkl')

    def test_proc(self):
        s = sorter.UniqueIDer(self.df)
        s.process()
        return

if __name__ == '__main__':
    unittest.main()
