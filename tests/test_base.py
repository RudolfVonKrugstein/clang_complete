
import sys
import os
import unittest
sys.path.append("../plugin")
import projectDatabase as pd

class TestBase(unittest.TestCase):
  numProjects = 3
  def setUp(self):
    self.proj = []
    '''Create the projects'''
    for pId in xrange(1,self.numProjects+1):
      p = "./testProject" + str(pId) + "/"
      if os.path.exists(p + ".clang_complete.project.dict"):
        os.remove(p + ".clang_complete.project.dict")
      pd.onLoadFile(p + "main.cpp",self.args,1)
      pd.createOrUpdateProjectForFile(p + "main.cpp",["-x","c++"],[])
      self.proj.append(pd.getProjectFromRoot(p))
      assert self.proj[pId-1] is not None

  def tearDown(self):
    '''remove the project file, so that it is created freshly next time'''
    for pId in xrange(1,self.numProjects+1):
      p = "./testProject" + str(pId) + "/"
      pd.onUnloadFile(p + "main.cpp")
      os.remove(p + ".clang_complete.project.dict")
    self.proj = None
      
