import sys
import os
import unittest
sys.path.append("../plugin")
import projectDatabase as pd
import test_base



class TestSymbolNames(test_base.TestBase):
  # some globals we need often
  args = ["-x","c++"]
  mainFile = [os.path.abspath("./testProject1/main.cpp"),os.path.abspath("./testProject2/main.cpp"),os.path.abspath("./testProject3/main.cpp")]
  expectedSymbols1 = [
      ('TestClass', set([(mainFile[0], 1, 7)]), 'CLASS_DECL', 'c:@C@TestClass'),
      ('TestClass::TestClass()', set([(mainFile[0], 3, 5)]), 'CONSTRUCTOR', 'c:@C@TestClass@F@TestClass#'),
      ('TestClass::function(int)', set([(mainFile[0], 5, 9)]), 'CXX_METHOD', 'c:@C@TestClass@F@function#I#'),
      ('TestClass::~TestClass()', set([(mainFile[0], 4, 5)]), 'DESTRUCTOR', 'c:@C@TestClass@F@~TestClass#'),
      ('TestTypeDef', set([(mainFile[0], 21, 19)]), 'TYPEDEF_DECL', 'c:main.cpp@292@T@TestTypeDef')]
  expectedSymbols2 = [
      ('function()', set([(mainFile[1], 2, 3), (mainFile[1], 5, 3)]), 'FUNCTION_TEMPLATE', 'c:@FT@>1#Tfunction#'),
      ('function<>()', set([(mainFile[1], 10, 5)]), 'FUNCTION_DECL', 'c:@F@function<#I>#'),
      ('function<>()', set([(mainFile[1], 15, 8)]), 'FUNCTION_DECL', 'c:@F@function<#d>#')]
  expectedSymbols3 = [
      ('TemplClassDerv', set([(mainFile[2], 9, 7)]), 'CLASS_DECL', 'c:@C@TemplClassDerv'),
      ('TemplClassTest::TemplClassTest<T>()', set([(mainFile[2], 5, 3)]), 'CONSTRUCTOR', 'c:@CT>1#T@TemplClassTest@F@TemplClassTest<T>#'),
      ('TemplClassTest::~TemplClassTest<T>()', set([(mainFile[2], 6, 3)]), 'DESTRUCTOR', 'c:@CT>1#T@TemplClassTest@F@~TemplClassTest<T>#'),
      ('TemplClassTest<T>', set([(mainFile[2], 3, 7)]), 'CLASS_TEMPLATE', 'c:@CT>1#T@TemplClassTest')]
  expectedSymbols  = [expectedSymbols1, expectedSymbols2, expectedSymbols3]

  def testProject1Symbols(self):
    '''Get all symbol names in the project1.'''
    s = self.proj[0].getAllTypeNamesInProject()
    self.assertEqual(s, self.expectedSymbols[0])

  def testProject2Symbols(self):
    '''Get all symbol names in the project2.'''
    s = self.proj[1].getAllTypeNamesInProject()
    self.assertEqual(s, self.expectedSymbols[1])

  def testProject3Symbols(self):
    '''Get all symbol names in the project3.'''
    s = self.proj[2].getAllTypeNamesInProject()
    self.assertEqual(s, self.expectedSymbols[2])

