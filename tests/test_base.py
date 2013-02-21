
import sys
import os
import unittest
sys.path.append("../plugin")
import projectDatabase as pd

class TestBase(unittest.TestCase):
  def setUp(self):
    '''Create to project'''
    if os.path.exists("./testProject1/.clang_complete.project.dict"):
      os.remove("./testProject1/.clang_complete.project.dict")
    pd.onLoadFile("./testProject1/main.cpp",self.args,1)
    pd.createOrUpdateProjectForFile("./testProject1/main.cpp",["-x","c++"],[])
    self.proj = pd.getProjectFromRoot("./testProject1")
    assert self.proj is not None

  def tearDown(self):
    '''remove the project file, so that it is created freshly next time'''
    pd.onUnloadFile("./testPorject1/main.cpp")
    os.remove("./testProject1/.clang_complete.project.dict")
    self.proj = None
