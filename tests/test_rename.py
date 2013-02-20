import sys
import os
import unittest
sys.path.append("../plugin")
import projectDatabase as pd



class TestRenames(unittest.TestCase):

# some globals we need often
  args = ["-x","c++"]
  constructorUsr = "c:@C@TestClass@F@TestClass#"
  destructorUsr  = "c:@C@TestClass@F@~TestClass#"
  classUsr       = "c:@C@TestClass"
  memberFuncUsr  = "c:@C@TestClass@F@function#"
  mainFile       = os.path.abspath("./testProject1/main.cpp")
  constructorRenameLocations = [(mainFile,3,5),(mainFile,9,13),(mainFile,10,23),(mainFile,15,12)]
  destructorRenameLocations  = [(mainFile,4,6),(mainFile,18,13)]
  classRenameLocations       = constructorRenameLocations + destructorRenameLocations + [(mainFile,1,7),(mainFile,8,5),(mainFile,9,3),(mainFile,10,3),(mainFile,15,1),(mainFile,18,1),(mainFile,21,9)]
  memberFuncRenameLocations = [(mainFile,5,9),(mainFile,8,16),(mainFile,12,10)]

  def setUp(self):
    '''Create to project'''
    if os.path.exists("./testProject1/.clang_complete.project.dict"):
      os.remove("./testProject1/.clang_complete.project.dict")
    pd.onLoadFile("./testProject1/main.cpp",self.args,1)
    pd.createOrUpdateProjectForFile("./testProject1/main.cpp",["-x","c++"],[])
    self.proj = pd.getProjectFromRoot("./testProject1")
    assert self.proj is not None

  def teardown(self):
    '''remove the project file, so that it is created freshly next time'''
    pd.onUnloadFile("./testPorject1/main.cpp")
    os.remove("./testProject1/.clang_complete.project.dict")
    self.proj = None

  def testConstructorSubRenameLocations(self):
    '''Test the rename locations for the constructor itself'''
    # need its usr info
    usrInfo = self.proj.usrInfos[self.constructorUsr]
    rl = self.proj.getUsrSubRenameLocations(usrInfo)
    self.assertEqual(rl, self.constructorRenameLocations)

  def testDestructorSubRenameLocations(self):
    '''Test the rename locations for the destructor itself'''
    # need its usr info
    usrInfo = self.proj.usrInfos[self.destructorUsr]
    rl = self.proj.getUsrSubRenameLocations(usrInfo)
    self.assertEqual(rl, self.destructorRenameLocations)

  def testClassDeclSubRenameLocations(self):
    '''Test the rename locations for the class itself'''
    # need its usr info
    usrInfo = self.proj.usrInfos[self.classUsr]
    rl = self.proj.getUsrSubRenameLocations(usrInfo)
    self.assertEqual(sorted(rl), sorted(self.classRenameLocations))

  def testMemberFuncRenameLocations(self):
    '''Test the rename locations for the member function itself'''
    # need its usr info
    usrInfo = self.proj.usrInfos[self.memberFuncUsr]
    rl = self.proj.getUsrSubRenameLocations(usrInfo)
    print rl
    print self.memberFuncRenameLocations
    self.assertEqual(sorted(rl), sorted(self.memberFuncRenameLocations))

  def testClassAllRenameLocations(self):
    '''Test what happens if we get all rename locations'''
    constRenameLoc = self.proj.getUsrRenameLocations(self.constructorUsr)
    destrRenameLoc = self.proj.getUsrRenameLocations(self.destructorUsr)
    classRenameLoc = self.proj.getUsrRenameLocations(self.classUsr)
    shouldRenameLoc = sorted(self.classRenameLocations)
    self.assertEqual(sorted(constRenameLoc), shouldRenameLoc)
    self.assertEqual(sorted(destrRenameLoc), shouldRenameLoc)
    self.assertEqual(sorted(classRenameLoc), shouldRenameLoc)


