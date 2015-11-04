import unittest
import os
import sys
tst_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(tst_path)
sys.path.append(os.path.join(tst_path, '..', 'src'))
from test_lybica import *

if __name__ == '__main__':
    unittest.main()
