import sys
import os
import unittest
sys.path.append("../plugin")
import projectDatabase as pd
import test_base



class TestRenames(test_base.TestBase):
  # some globals we need often
  args = ["-x","c++"]
  mainFile = [os.path.abspath("./testProject1/main.cpp"),os.path.abspath("./testProject2/main.cpp"),os.path.abspath("./testProject3/main.cpp")]
  constructorUsr = "c:@C@TestClass@F@TestClass#"
  destructorUsr  = "c:@C@TestClass@F@~TestClass#"
  classUsr       = "c:@C@TestClass"
  memberFuncUsr  = "c:@C@TestClass@F@function#I#"
  parameterUsr   = "c:main.cpp@116@C@TestClass@F@function#I#@a"
  localVarUsr    = "c:main.cpp@140@C@TestClass@F@function#I#@b"
  templClassUsr  = "c:@CT>1#T@TemplClassTest"
  templClassConstrUsr = "c:@CT>1#T@TemplClassTest@F@TemplClassTest<T>#"
  templClassDestrUsr = "c:@CT>1#T@TemplClassTest@F@~TemplClassTest<T>#"
  constructorRenameLocations = [(mainFile[0],3,5),(mainFile[0],9,13),(mainFile[0],10,23),(mainFile[0],15,12)]
  destructorRenameLocations  = [(mainFile[0],4,6),(mainFile[0],18,13)]
  classRenameLocations       = constructorRenameLocations + destructorRenameLocations + [(mainFile[0],1,7),(mainFile[0],8,5),(mainFile[0],9,3),(mainFile[0],10,3),(mainFile[0],15,1),(mainFile[0],18,1),(mainFile[0],21,9)]
  memberFuncRenameLocations = [(mainFile[0],5,9),(mainFile[0],8,16),(mainFile[0],12,10)]
  parameterRenameLocations  = [(mainFile[0],8,29),(mainFile[0],9,24),(mainFile[0],9,27),(mainFile[0],12,19)]
  localVarRenameLocations   = [(mainFile[0],9,20),(mainFile[0],9,31),(mainFile[0],12,23)]
  templClassRenameLocations = [(mainFile[2],3,7),(mainFile[2],5,3),(mainFile[2],6,4),(mainFile[2],9,31),(mainFile[2],13,1),(mainFile[2],13,20),(mainFile[2],14,3),(mainFile[2],14,35),(mainFile[2],17,1),(mainFile[2],17,21)]

  def testConstructorSubRenameLocations(self):
    '''Test the rename locations for the constructor itself (project 1)'''
    # need its usr info
    usrInfo = self.proj[0].usrInfos[self.constructorUsr]
    rl = self.proj[0].getUsrSubRenameLocations(usrInfo)
    self.assertEqual(rl, self.constructorRenameLocations)

  def testDestructorSubRenameLocations(self):
    '''Test the rename locations for the destructor itself (project 1)'''
    # need its usr info
    usrInfo = self.proj[0].usrInfos[self.destructorUsr]
    rl = self.proj[0].getUsrSubRenameLocations(usrInfo)
    self.assertEqual(rl, self.destructorRenameLocations)

  def testClassDeclSubRenameLocations(self):
    '''Test the rename locations for the class itself (project 1)'''
    # need its usr info
    usrInfo = self.proj[0].usrInfos[self.classUsr]
    rl = self.proj[0].getUsrSubRenameLocations(usrInfo)
    self.assertEqual(sorted(rl), sorted(self.classRenameLocations))

  def testMemberFuncRenameLocations(self):
    '''Test the rename locations for the member function itself (project 1)'''
    # need its usr info
    usrInfo = self.proj[0].usrInfos[self.memberFuncUsr]
    rl = self.proj[0].getUsrSubRenameLocations(usrInfo)
    self.assertEqual(sorted(rl), sorted(self.memberFuncRenameLocations))

  def testParameterRenameLocations(self):
    '''Test the rename locations of the parameter a (project 1)'''
    # need its usr info
    usrInfo = self.proj[0].usrInfos[self.parameterUsr]
    rl = self.proj[0].getUsrSubRenameLocations(usrInfo)
    self.assertEqual(sorted(rl), sorted(self.parameterRenameLocations))

  def testLocalVarRenameLocations(self):
    '''Test the rename locations of the local variable b (porject 1)'''
    # need its usr info
    usrInfo = self.proj[0].usrInfos[self.localVarUsr]
    rl = self.proj[0].getUsrSubRenameLocations(usrInfo)
    self.assertEqual(sorted(rl), sorted(self.localVarRenameLocations))

  def testClassAllRenameLocations(self):
    '''Test what happens if we get all rename locations (project 1)'''
    constRenameLoc = self.proj[0].getUsrRenameLocations(self.constructorUsr)
    destrRenameLoc = self.proj[0].getUsrRenameLocations(self.destructorUsr)
    classRenameLoc = self.proj[0].getUsrRenameLocations(self.classUsr)
    shouldRenameLoc = sorted(self.classRenameLocations)
    self.assertEqual(sorted(constRenameLoc), shouldRenameLoc)
    self.assertEqual(sorted(destrRenameLoc), shouldRenameLoc)
    self.assertEqual(sorted(classRenameLoc), shouldRenameLoc)

  def testTemplClassAllRenameLocations(self):
    '''Test all the rename locations of the template class (project 3)'''
    rl1 = self.proj[2].getUsrRenameLocations(self.templClassUsr)
    rl2 = self.proj[2].getUsrRenameLocations(self.templClassConstrUsr)
    rl3 = self.proj[2].getUsrRenameLocations(self.templClassDestrUsr)
    self.assertEqual(sorted(rl1), sorted(self.templClassRenameLocations))
    self.assertEqual(sorted(rl2), sorted(self.templClassRenameLocations))
    self.assertEqual(sorted(rl3), sorted(self.templClassRenameLocations))


