import sys
import os
import unittest
sys.path.append("../plugin")
import projectDatabase as pd
import test_base



class TestSymbolNames(test_base.TestBase):
  # some globals we need often
  args = ["-x","c++"]
  mainFile       = os.path.abspath("./testProject1/main.cpp")
  expectedSymbols = [('TemplClassDerv', set([(mainFile, 30, 7)]), 'CLASS_DECL', 'c:@C@TemplClassDerv'),
      ('TemplClassTest::TemplClassTest<T>()', set([(mainFile, 26, 3)]), 'CONSTRUCTOR', 'c:@CT>1#T@TemplClassTest@F@TemplClassTest<T>#'),
      ('TemplClassTest::~TemplClassTest<T>()', set([(mainFile, 27, 3)]), 'DESTRUCTOR', 'c:@CT>1#T@TemplClassTest@F@~TemplClassTest<T>#'),
      ('TemplClassTest<T>', set([(mainFile, 24, 7)]), 'CLASS_TEMPLATE', 'c:@CT>1#T@TemplClassTest'),
      ('TestClass', set([(mainFile, 1, 7)]), 'CLASS_DECL', 'c:@C@TestClass'),
      ('TestClass::TestClass()', set([(mainFile, 3, 5)]), 'CONSTRUCTOR', 'c:@C@TestClass@F@TestClass#'),
      ('TestClass::function(int)', set([(mainFile, 5, 9)]), 'CXX_METHOD', 'c:@C@TestClass@F@function#I#'),
      ('TestClass::~TestClass()', set([(mainFile, 4, 5)]), 'DESTRUCTOR', 'c:@C@TestClass@F@~TestClass#'),
      ('TestTypeDef', set([(mainFile, 21, 19)]), 'TYPEDEF_DECL', 'c:main.cpp@292@T@TestTypeDef')]

  def testProjectSymbols(self):
    '''Get all symbol names in the project.'''
    s = self.proj.getAllTypeNamesInProject()
    self.assertEqual(s, self.expectedSymbols)

