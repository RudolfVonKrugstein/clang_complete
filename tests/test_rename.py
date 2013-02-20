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
  memberFuncUsr  = "c:@C@TestClass@F@function#I#"
  parameterUsr   = "c:main.cpp@116@C@TestClass@F@function#I#@a"
  localVarUsr    = "c:main.cpp@140@C@TestClass@F@function#I#@b"
  templClassUsr  = "c:@CT>1#T@TemplClassTest"
  templClassConstrUsr = "c:@CT>1#T@TemplClassTest@F@TemplClassTest<T>#"
  templClassDestrUsr = "c:@CT>1#T@TemplClassTest@F@~TemplClassTest<T>#"
  mainFile       = os.path.abspath("./testProject1/main.cpp")
  constructorRenameLocations = [(mainFile,3,5),(mainFile,9,13),(mainFile,10,23),(mainFile,15,12)]
  destructorRenameLocations  = [(mainFile,4,6),(mainFile,18,13)]
  classRenameLocations       = constructorRenameLocations + destructorRenameLocations + [(mainFile,1,7),(mainFile,8,5),(mainFile,9,3),(mainFile,10,3),(mainFile,15,1),(mainFile,18,1),(mainFile,21,9)]
  memberFuncRenameLocations = [(mainFile,5,9),(mainFile,8,16),(mainFile,12,10)]
  parameterRenameLocations  = [(mainFile,8,29),(mainFile,9,24),(mainFile,9,27),(mainFile,12,19)]
  localVarRenameLocations   = [(mainFile,9,20),(mainFile,9,31),(mainFile,12,23)]
  templClassRenameLocations = [(mainFile,24,7),(mainFile,26,3),(mainFile,27,4),(mainFile,30,31),(mainFile,34,1),(mainFile,34,20),(mainFile,35,3),(mainFile,35,35),(mainFile,38,1),(mainFile,38,21)]

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
    self.assertEqual(sorted(rl), sorted(self.memberFuncRenameLocations))

  def testParameterRenameLocations(self):
    '''Test the rename locations of the parameter a'''
    # need its usr info
    usrInfo = self.proj.usrInfos[self.parameterUsr]
    rl = self.proj.getUsrSubRenameLocations(usrInfo)
    self.assertEqual(sorted(rl), sorted(self.parameterRenameLocations))

  def testLocalVarRenameLocations(self):
    '''Test the rename locations of the local variable b'''
    # need its usr info
    usrInfo = self.proj.usrInfos[self.localVarUsr]
    rl = self.proj.getUsrSubRenameLocations(usrInfo)
    self.assertEqual(sorted(rl), sorted(self.localVarRenameLocations))

  def testClassAllRenameLocations(self):
    '''Test what happens if we get all rename locations'''
    constRenameLoc = self.proj.getUsrRenameLocations(self.constructorUsr)
    destrRenameLoc = self.proj.getUsrRenameLocations(self.destructorUsr)
    classRenameLoc = self.proj.getUsrRenameLocations(self.classUsr)
    shouldRenameLoc = sorted(self.classRenameLocations)
    self.assertEqual(sorted(constRenameLoc), shouldRenameLoc)
    self.assertEqual(sorted(destrRenameLoc), shouldRenameLoc)
    self.assertEqual(sorted(classRenameLoc), shouldRenameLoc)

  def testTemplClassAllRenameLocations(self):
    '''Test all the rename locations of the template class'''
    rl1 = self.proj.getUsrRenameLocations(self.templClassUsr)
    rl2 = self.proj.getUsrRenameLocations(self.templClassConstrUsr)
    rl3 = self.proj.getUsrRenameLocations(self.templClassDestrUsr)
    print sorted(rl1)
    print sorted(self.templClassRenameLocations)
    self.assertEqual(sorted(rl1), sorted(self.templClassRenameLocations))
    self.assertEqual(sorted(rl2), sorted(self.templClassRenameLocations))
    self.assertEqual(sorted(rl3), sorted(self.templClassRenameLocations))


