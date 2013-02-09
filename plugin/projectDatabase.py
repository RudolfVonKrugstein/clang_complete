import os, fnmatch
import clang.cindex as cindex
import cPickle as pickle

# info about an usr
class UsrInfo:
  ''' Information about an USR located in the database'''
  def __init__(self, usr, displayname, spelling, lexical_parent_usr):
    self.usr = usr
    # files during which parsing this usr was found
    self.associatedFiles = set()
    # location referencing this usr
    self.references = set()
    # positions where this usr was declared (normaly there should be only one)
    self.declarations = set()
    # positions where this usr is defined
    self.definitions = set()
    self.displayname = displayname
    self.spelling = spelling
    # lexical parent for building full type name
    if (lexical_parent_usr != ""):
      self.lexical_parent = lexical_parent_usr
    else:
      self.lexical_parent = None

  def removeFile(self,fileName):
    ''' Goes through all information about the usr and remove anything  that has to do wit the file. Returns if the usr has no associated files.'''
    self.references = filter(file.name != fileName, self.references)
    self.declarations = filter(file.name != fileName, self.declarations)
    self.defintions = filter(file.name != fileName, self.defintions)
    self.associatedFiles.discard(fileName)
    return len(self.associatedFiles) == 0

  def addDefinition(self,loc):
    self.definitions.add((loc.file.name, loc.line, loc.column))
  def addDeclaration(self,loc):
    self.declarations.add((loc.file.name, loc.line, loc.column))
  def addReference(self,loc):
    self.references.add((loc.file.name, loc.line, loc.column))
  def addAssociatedFile(self,fileName):
    self.associatedFiles.add(fileName)

class FileInfo:
  '''Information about a file located in a projects database'''
  def __init__(self, fileName, mtime, args = None):
    self.name = fileName
    # set usrs this references
    self.usrStrings = set()
    self.args = args
    # change time when this file was parsed
    self.mtime = mtime


class ProjectDatabase:
  ''' Database for all files of a project.'''
  def __init__(self):
    # files in the project and the corresponing FileInfo
    self.fileInfos = dict()
    # USRs in this project and the corresponding UsrInfo
    self.usrInfos = dict()

  @staticmethod
  def loadProject(dictPath):
    f = open(dictPath,"r")
    res = pickle.load(f)
    f.close()
    if isinstance(res,ProjectDatabase):
      return res
    else:
      raise RuntimeError(dictPath + " is not a saved project database")

  def saveProject(self,dictPath):
    f = open(dictPath,"w")
    pickle.dump(self,f,protocol=2)
    f.close()

  def addFile(self,fileName, args = None):
    ''' Add a file to database'''
    # check if file is already known
    if (self.fileInfos.has_key(fileName)):
      return
    print "Parsing",fileName
    transUnit = cindex.TranslationUnit.from_source(fileName, args = args)
    cursor = transUnit.cursor


    # remember file
    mtime = os.path.getmtime(fileName)
    self.fileInfos[fileName] = FileInfo(fileName, mtime, args)
    fileInfo = self.fileInfos[fileName]
    # build database with file
    self.buildDatabase(cursor,fileInfo,fileName)

  def removeFile(self,fileName):
    ''' Remove a file from the database.
        Removes all references from USRs to this file
        and removes USRs that do not reference any files anyore'''
    fileInfo = self.fileInfos[fileName]
    for u in fileInfo.usrStrings:
      if self.usrInfos[u].removeFile(fileName):
        # true means the USR is not referenced anymore
        del self.usrInfos[u]
    
    del self.fileInfos[fileName]

  def updateOrAddFile(self,fileName, args = None):
    ''' Remove (if it exits) and re-add a file'''
    if self.fileInfos.has_key(fileName):
      self.removeFile(fileName)
    self.addFile(fileName, args)

  def updateOutdatedFiles(self):
    ''' Search for files which mtime is older than the mtime of the file on disc
        and update those.
        Also remove files not existing anymore.'''
    outdatedFiles = []
    removedFiles  = []
    for name,data in self.fileInfos:
      try:
        mtime = os.path.getmtime(name)
        if mtime > data[1]:
          outdatedFiles.append(name)
      except:
        removedFiles.append(name)
    for f in removedFiles:
      self.removeFile(f)
    for f in outdatedFiles:
      self.updateOrAddFile(f)

  def readCursor(self,c, usrFileEntry, fileName):
    ''' Read symbol at cursor position.
        Also read any symbol cursor references
        and their lexical parents.
    '''
    # get anything we are referencing
    ref = None
    if (not (c.referenced is None)) and (c.referenced != conf.lib.clang_getNullCursor()):
      ref = c.referenced
    # helper function to get the lexical parent
    def getLexicalParent(cursor):
      if cursor.lexical_parent is None:
        return None
      else:
        return cursor.lexical_parent.get_usr()
    # we have no interest in a cursor with no location in a source file
    # also if it nor its reference has an non-empty usr, it has nothing
    # interesing in it
    if c.location.file == None:
      return
    if c.get_usr() == "" and (ref is None or ref.get_usr() == ""):
      return

    # helper function adding declaration and returning the corresponding usr
    def addDeclaration(cursor):
      # if the lexical parent is delcaration, than also add tit
      if not (cursor.lexical_parent is None) and cursor.lexical_parent.kind.is_declaration():
        addDeclaration(cursor.lexical_parent)
      usrInfo = self.getOrCreateUsr(cursor.get_usr(), usrFileEntry, cursor.displayname, cursor.spelling, getLexicalParent(cursor))
      if cursor.is_definition():
        usrInfo.addDefinition(cursor.location)
      else:
        usrInfo.addDeclaration(cursor.location)
      usrInfo.addAssociatedFile(fileName)
      return usrInfo

    # if we have a reference, add it
    if not (ref is None):
      if not ref.kind.is_declaration():
        raise RuntimeError("Reference has to be delcaration")
      refUsrInfo = addDeclaration(ref)

    # add the curser itself
    # declarations or defintions ...
    if c.kind.is_declaration():
      addDeclaration(c)

    # reference
    if c.kind.is_reference():
      if ref is None:
        raise RuntimeError("Reference without reference cursor")
      refUsrInfo.addReference(c.location)

    # no idea what to do with this ...
    #if c.kind.is_attribute():
    #  print "Attribute:",c.displayname,usr,c.location

    # expression
    if c.kind.is_expression():
      # expression without references do not interest us
      if not (ref is None):
        refUsrInfo.addReference(c.location)

  def buildDatabase(self,c, usrFileEntry, fileName):
    ''' Build (extend) the database based on a cursors.
        Calls readCursor and recurse'''
    # if we are outside of the src file
    # we are not interested. We are only interested in things defined, declared or referenced in out source file
    # and since we parse all files, we can be sure not to miss anything
    # if we do stop when not in the source file, database building takes much longer
    if not (c.location.file is None) and c.location.file.name != fileName:
      return
    
    self.readCursor(c, usrFileEntry, fileName)

    for c in c.get_children():
      self.buildDatabase(c, usrFileEntry, fileName)

  def getOrCreateUsr(self,usr,usrFileEntry,displayname,spelling,lexical_parent_usr):
    '''If the USR does not yet exist, create it.
       In any case, return it.'''
    usrFileEntry.usrStrings.add(usr)
    if not (self.usrInfos.has_key(usr)):
      self.usrInfos[usr] = UsrInfo(usr, displayname, spelling, lexical_parent_usr)
    return self.usrInfos[usr]

  def getFullTypeNameFromUsr(self,usrName):
    '''Get the full type name from an usr string'''
    if self.usrInfos.has_key(usrName):
      return self.getFullTypeName(self.usrInfos[usrName])
    else:
      return "<not found usr: " + usrName + ">"

  def getFullTypeName(self,usrInfo):
    '''Get thhe full type name from an UsrInfo object.'''
    if not (usrInfo.lexical_parent is None):
      return self.getFullTypeNameFromUsr(usrInfo.lexical_parent) + "::" + usrInfo.spelling
    else:
      return usrInfo.spelling

  def getAllTypeNames(self):
    '''Iterator that returns all (full) type names and the position where
       they are declated. If multiple positions are found for, the type name
       is returned multiple times.'''
    for k,usr in self.usrInfos.iteritems():
      tName = self.getFullTypeName(usr)
      # add the declaration positions. If there are none, add definition positions
      if len(usr.declarations) == 0:
        positions = usr.definitions
      else:
        positions = usr.declarations
      for p in positions:
        yield (tName,p)

  def getAllTypeNamesInProject(self):
    ''' same as getAllTypeNames, but reduced to files in the project'''
    for k,usr in self.usrInfos.iteritems():
      tName = self.getFullTypeName(usr)
      # add the declaration positions. If there are none, add definition positions
      if len(usr.declarations) == 0:
        positions = usr.definitions
      else:
        positions = usr.declarations
      for p in positions:
        if self.fileInfos.has_key(p[0]):
          yield (tName,p)

class LoadedProject():
  '''Class representing a project loaded in memory.
     The class stores the location of the project root,
     files loaded for the project and compilation options.'''
  def __init__(self, root, args):
    self.root = root
    self.args = args
    self.openFiles = set()
    self.project = None

  def loadProject(self):
    self.project = ProjectDatabase.loadProject(os.path.join(self.root, ".clang_complete.project.dict"))

  def buildProjectDatabase(self):
    '''Take a directory and build a project database'''
    self.project = ProjectDatabase()
    for f in find_cpp_files(self.root):
      self.project.addFile(f, self.args)

  def openFile(self, path):
    self.openFiles.add(path)

  def closeFile(self,path):
    '''Close the file and return if any files are still open'''
    self.openFiles.delete(path)
    return len(self.openFiles) == 0

def searchUpwardForFile(startPath, fileName):
  '''Return the first encounter of the searched file, upward from the current direcotry'''
  startDir = os.path.abspath(os.path.dirname(startPath))

  curDir  = startDir
  lastDir = ""
  while curDir != lastDir:
    lastDir = curDir
    if os.path.exists(os.path.join(curDir, fileName)):
      return curDir #found the file, this is the projects root
    else:
      curDir = os.path.abspath(os.path.join(curDir,os.path.pardir))

  # Nothing found
  return None

def filesProjectRoot(filePath):
  '''Return the root directory for a files project by searching for .clang_complete'''
  return searchUpwardForFile(filePath, ".clang_complete.project.dict")

# global dictonary of all loaded projects
loadedProjects = dict()

def onLoadFile(filePath, args):
  '''Check if the project for the file already exists. If not, create a new project.
     Add the file to the project.'''
  projectRoot = filesProjectRoot(filePath)
  if projectRoot is not None:
    if loadedProjects.has_key(projectRoot):
      loadedProjects[projectRoot].openFile(filePath)
    else:
      print "Loading clang project dictonary at " + projectRoot
      loadedProjects[projectRoot] = LoadedProject(projectRoot, args)
      loadedProjects[projectRoot].loadProject()
      loadedProjects[projectRoot].openFile(filePath)

def getFilesProject(filePath):
  projectRoot = filesProjectRoot(filePath)
  if projectRoot is not None:
    if loadedProjects.has_key(projectRoot):
      return loadedProjects[projectRoot]
  return None

def getOrLoadFilesProject(filePath, args):
  ''' Returns the project for a file if loaded.
      If not loaded, load it and return it.'''
  projectRoot = filesProjectRoot(filePath)
  if projectRoot is not None:
    if not loadedProjects.has_key(projectRoot):
      loadedProjects[projectRoot] = LoadedProject(projectRoot, args)
      loadedProjects[projectRoot].loadProject()
    return loadedProjects[projectRoot]
  return None

def onUnloadFile(filePath):
  projectRoot = filesProjectRoot(filePath)
  if projectRoot is not None:
    if loadedProjects.has_key(projectRoot):
      if loadedProjects[projectRoot].closeFile(filePath):
        del loadedProjects[projectRoot]

def createProjectForFile(path,args):
  '''Create a project for the file, by searching for .clang_complete
     and creating the project there'''
  projectPath = searchUpwardForFile(path,".clang_complete")
  if projectPath is None:
    print "Cannot create project because I cannot find .clang_complete"
    return
  proj = LoadedProject(projectPath,args)
  proj.buildProjectDatabase()
  proj.project.saveProject(os.path.join(projectPath, ".clang_complete.project.dict"))

def getFilesProjectSymbolNames(filePath,args):
  proj = getOrLoadFilesProject(filePath, args)
  if proj is None:
    print "Sorry, no project for file found"
  else:
    return proj.project.getAllTypeNamesInProject()

def find_files(directory, patterns):
  ''' Supporting function to iterate over all files
  recusivly in a directory which follow a specific pattern.'''
  for root, dirs, files in os.walk(directory):
    for basename in files:
      for pattern in patterns:
        if fnmatch.fnmatch(basename, pattern):
          filename = os.path.join(root, basename)
          yield filename

def find_cpp_files(path = "."):
  '''Iterate over all files which are cpp file'''
  return find_files(path,["*.cpp","*.cc","*.h","*.hpp"])

conf = cindex.Config()


