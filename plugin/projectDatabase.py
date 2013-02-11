import os, fnmatch
import clang.cindex as cindex
import cPickle as pickle

# info about an usr
class UsrInfo:
  ''' Information about an USR located in the database'''
  def __init__(self, usr, kind, displayname, spelling, lexical_parent_usr):
    self.usr = usr
    self.kind = kind
    # files during which parsing this usr was found
    self.associatedFiles = set()
    # location referencing this usr. These are pairs of locations and cursor kinds
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
    self.references   = set(filter(lambda loc: loc[0] != fileName, self.references))
    self.declarations = set(filter(lambda loc: loc[0] != fileName, self.declarations))
    self.definitions  = set(filter(lambda loc: loc[0] != fileName, self.definitions))
    self.associatedFiles.discard(fileName)
    return len(self.associatedFiles) == 0

  def addDefinition(self,loc):
    self.definitions.add((loc.file.name, loc.line, loc.column))
  def addDeclaration(self,loc):
    self.declarations.add((loc.file.name, loc.line, loc.column))
  def addReference(self,loc,kind,parent = None):
    ''' From the parent we can get the type of the derived class in
        case of a CXX_BASE_SPECIFIER.'''
    self.references.add((loc.file.name, loc.line, loc.column, kind, parent))
  def addAssociatedFile(self,fileName):
    self.associatedFiles.add(fileName)

  def isType(self):
    '''Checks if the Usr is a type. That is, if it is not a variable declaration.
       Most likely this list is not complete ...
       '''
    return not (self.kind in [cindex.CursorKind.FIELD_DECL.value,
                         cindex.CursorKind.ENUM_CONSTANT_DECL.value,
                         cindex.CursorKind.VAR_DECL.value,
                         cindex.CursorKind.PARM_DECL.value])

class FileInfo:
  '''Information about a file located in a projects database'''
  def __init__(self, fileName, mtime, args = None):
    self.name = fileName
    # set usrs this references
    self.usrStrings = set()
    self.args = args
    # change time when this file was parsed
    self.mtime = mtime
    # add information if the file is open
    self.isOpen = False
    self.changedtick = 0

  def open(self, changedtick):
    self.isOpen = True
    self.changedtick = changedtick


class ProjectDatabase:
  ''' Database for all files of a project.'''
  def __init__(self, root, args):
    # files in the project and the corresponing FileInfo
    self.fileInfos = dict()
    # USRs in this project and the corresponding UsrInfo
    self.usrInfos = dict()
    self.args = args
    self.root = root

  @staticmethod
  def loadProject(dictPath):
    f = open(dictPath,"r")
    res = pickle.load(f)
    f.close()
    if isinstance(res,ProjectDatabase):
      # mark all files closed
      for p,f in res.fileInfos.iteritems():
        f.isOpen = False
        f.changedtick = 0
      return res
    else:
      raise RuntimeError(dictPath + " is not a saved project database")

  def saveProject(self,dictPath):
    f = open(dictPath,"w")
    pickle.dump(self,f,protocol=2)
    f.close()

  def addFile(self,fileName, unsaved_files = None):
    ''' Add a file to database'''
    # check if file is already known
    if (self.fileInfos.has_key(fileName)):
      return
    print "Parsing",fileName
    transUnit = cindex.TranslationUnit.from_source(fileName, args = self.args, unsaved_files = unsaved_files)
    cursor = transUnit.cursor

    # remember file
    mtime = os.path.getmtime(fileName)
    self.fileInfos[fileName] = FileInfo(fileName, mtime, self.args)
    fileInfo = self.fileInfos[fileName]
    # build database with file
    self.buildDatabase(cursor,None,fileInfo,fileName)

  def openFile(self, path, changedtick, unsaved_files):
    '''Mark the file as open. if not in project, add it.'''
    if not self.fileInfos.has_key(path):
      self.addFile(path, unsaved_files)
    self.fileInfos[path].open(changedtick)

  def closeFile(self,path):
    '''Mark the file as closed and return if there are anymore open files.'''
    if self.fileInfos.has_key(path):
      fileInfos[path].close()
    for p,f in self.fileInfos.iteritems():
      if f.isOpen:
        return False
    return True

  def onFileSaved(self, path, changedtick, unsaved_files):
    '''When a file is saved, we want to know so that when the changedtick of the file
         is up to date (meaning the file that is changed is already up to date in the database)
         we want to update the mtime without reparsing it.
         Also of the file is not part of the project (because it did not exist under its file name before)
         we want to add it now.
         '''
    if self.fileInfos.has_key(path):
      if self.fileInfos[path].changedtick == changedtick:
        self.project.updateFilesMtimeWithoutReparse(path)
    else:
      self.openFile(path,changedtick,unsaved_files)

  def updateFilesMtimeWithoutReparse(self, fileName):
    mtime = os.path.getmtime(fileName)
    self.fileInfos[fileName].mtime = mtime

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

  def updateFileWithTU(fileName,tu,unsaved_files):
    ''' Update a file, but without creating a tu for it, but use the given tu.'''
    if self.fileInfos.has_key(fileName):
      self.removeFile(fileName)
    print "Parsing with exisiting tu",fileName
    cursor = tu.cursor

    # remember file
    mtime = os.path.getmtime(fileName)
    self.fileInfos[fileName] = FileInfo(fileName, mtime, self.args)
    fileInfo = self.fileInfos[fileName]
    # build database with file
    self.buildDatabase(cursor,None,fileInfo,fileName)

  def updateOrAddFile(self,fileName, unsaved_files = None):
    ''' Remove (if it exits) and re-add a file'''
    if self.fileInfos.has_key(fileName):
      self.removeFile(fileName)
    self.addFile(fileName, unsaved_files)

  def updateOutdatedFiles(self, unsaved_files):
    ''' Search for files which mtime is older than the mtime of the file on disc
        and update those.
        Also update all files for which the args are different than the given ones.
        Also remove files not existing anymore.'''
    outdatedFiles = []
    removedFiles  = []
    for file,fileInfo in self.fileInfos.iteritems():
      try:
        mtime = os.path.getmtime(fileInfo.name)
        if mtime > fileInfo.mtime or fileInfo.args != self.args:
          outdatedFiles.append(fileInfo.name)
      except:
        removedFiles.append(fileInfo.name)
    for f in removedFiles:
      self.removeFile(f)
    for f in outdatedFiles:
      self.updateOrAddFile(f, unsaved_files)
    for f in find_cpp_files(self.root):
      if not self.fileInfos.has_key(f):
        addFile(f,unsaved_files)

  def readCursor(self,c,parent, usrFileEntry, fileName):
    ''' Read symbol at cursor position.
        Also read any symbol cursor references
        and their lexical parents.
    '''

    # there are some cursor, we are not interested in
    # I am sure other things will come up
    if c.kind.value in [cindex.CursorKind.CXX_ACCESS_SPEC_DECL.value,
                        cindex.CursorKind.LINKAGE_SPEC.value
                       ]:
      return

    # get the usr of the parent
    # this is interesting for CXX_BASE_SPECIFIER, becaue we can get the type of the
    # derived class this way
    if parent is not None:
      parentUsr = parent.get_usr()
    else:
      parentUsr = None
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
      usrInfo = self.getOrCreateUsr(cursor.get_usr(), cursor.kind.value, usrFileEntry, cursor.displayname, cursor.spelling, getLexicalParent(cursor))
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
    # declarations or  ...
    if c.kind.is_declaration():
      addDeclaration(c)

    # reference
    if c.kind.is_reference():
      if ref is None:
        raise RuntimeError("Reference without reference cursor")
      refUsrInfo.addReference(c.location, c.kind.value, parentUsr)

    # no idea what to do with this ...
    #if c.kind.is_attribute():
    #  print "Attribute:",c.displayname,usr,c.location

    # expression
    if c.kind.is_expression():
      # expression without references do not interest us
      if not (ref is None):
        refUsrInfo.addReference(c.location, c.kind.value, parentUsr)

  def buildDatabase(self,c,parent, usrFileEntry, fileName):
    ''' Build (extend) the database based on a cursors.
        Calls readCursor and recurse'''
    # if we are outside of the src file
    # we are not interested. We are only interested in things defined, declared or referenced in out source file
    # and since we parse all files, we can be sure not to miss anything
    # if we do stop when not in the source file, database building takes much longer
    if not (c.location.file is None) and c.location.file.name != fileName:
      return
    
    self.readCursor(c,parent, usrFileEntry, fileName)

    for child in c.get_children():
      self.buildDatabase(child, c, usrFileEntry, fileName)

  def getOrCreateUsr(self,usr,kind,usrFileEntry,displayname,spelling,lexical_parent_usr):
    '''If the USR does not yet exist, create it.
       In any case, return it.'''
    usrFileEntry.usrStrings.add(usr)
    if not (self.usrInfos.has_key(usr)):
      self.usrInfos[usr] = UsrInfo(usr, kind, displayname, spelling, lexical_parent_usr)
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
       is returned multiple times.
       Returns a list of typles:
       [(typeName,(fileName,line,column),kindname,usr),...]
       '''
    for k,usr in self.usrInfos.iteritems():
      if not usr.isType():
        continue
      tName = self.getFullTypeName(usr)
      kind  = cindex.CursorKind.from_id(usr.kind).name
      # add the declaration positions. If there are none, add definition positions
      if len(usr.declarations) == 0:
        positions = usr.definitions
      else:
        positions = usr.declarations
      for p in positions:
        yield (tName,p,kind,usr.usr)

  def getAllTypeNamesInProject(self):
    ''' same as getAllTypeNames, but reduced to files in the project
       Returns a list of typles:
       [(typeName,(fileName,line,column),kindname,usr),...]'''
    for k,usr in self.usrInfos.iteritems():
      if not usr.isType():
        continue
      tName = self.getFullTypeName(usr)
      kind  = cindex.CursorKind.from_id(usr.kind).name
      # add the declaration positions. If there are none, add definition positions
      if len(usr.declarations) == 0:
        positions = usr.definitions
      else:
        positions = usr.declarations
      for p in positions:
        if self.fileInfos.has_key(p[0]):
          yield (tName,p,kind,usr.usr)

  def getDerivedClassesTypeNames(self, baseUsr):
    '''Iterator for type name of classes derived from the class specified by the usr
       Returns a list of tuples:
       [(typename,(fileName,line,column))]'''
    if not self.usrInfos.has_key(baseUsr):
      print "Sorry, base class not found"
    else:
      for file,row,column,kind,parentUsr in self.usrInfos[baseUsr].references:
        if kind == cindex.CursorKind.CXX_BASE_SPECIFIER.value:
          if (parentUsr is None) or (not self.usrInfos.has_key(parentUsr)):
            print "Sorry, no usr for derived class of ",baseUsr
          else:
            baseUsrInfo = self.usrInfos[parentUsr]
            positions = baseUsrInfo.definitions
            baseName = self.getFullTypeName(baseUsrInfo)
            for p in positions:
              yield (baseName,p)

#  def updateProjectWithOpenFiles(self,files,unsaved_files):
#    ''' Expects a list of tuples for files:
#        [(filePath,translationUnit,changedtick)].
#        For modified files it expects all files that contain changed contents to 
#        what is on discL
#        [(filePath,bufferContents)]'''
#    for filePath,tu,changedtick in files:
#      # check if the file belongs to this project at all
#      if not os.path.normpath(filePath).startswith(os.normpath(self.root)):
#        continue
#      # check if we already are up to date
#      if self.openFiles[filePath].changedtick == changedtick:
#        continue
#      self.project.updateFileWithTU(filePath,tu,self.args,unsaved_files)
#      self.openFiles[filePath].changedtick = changedtick


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

def onLoadFile(filePath, args, changedtick, unsaved_files):
  '''Check if the project for the file already exists. If not, create a new project.
     Add the file to the project.'''
  proj = getOrLoadFilesProject(filePath, args)
  if proj is not None:
    proj.openFile(filePath, changedtick, unsaved_files)
    return proj.root
  return None

def onFileSaved(self,path,changedtick,unsaved_files):
  '''When a file is saved, we want to know so that when the changedtick of the file
       is up to date (meaning the file that is changed is already up to date in the database)
       we want to update the mtime without reparsing it.
       Also of the file is not part of the project (because it did not exist under its file name before)
       we want to add it now.
       '''
  proj = getOrLoadFilesProject(path)
  if proj is not None:
    proj.onFileSaved(path,changedtick,unsaved_files)

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
      print "Loading clang project dictonary at " + projectRoot
      loadedProjects[projectRoot] = ProjectDatabase.loadProject(os.path.join(projectRoot, ".clang_complete.project.dict"))
      loadedProjects[projectRoot].args = args
    return loadedProjects[projectRoot]
  return None

def onUnloadFile(filePath):
  proj = getFilesProject(filePath)
  if proj is not None:
    proj.closeFile(filePath)
    # should we also update the project here?
    print "Saving clang project dictonary at " + projectRoot
    proj.saveProject(os.path.join(proj.root, ".clang_complete.project.dict"));
    del loadedProjects[proj.root]

def createOrUpdateProjectForFile(path,args, unsaved_files):
  '''Create a project for the file, by searching for .clang_complete
     and creating the project there'''
  projectPath = searchUpwardForFile(path,".clang_complete")
  if projectPath is None:
    print "Cannot create project because I cannot find .clang_complete"
    return None
  proj = getOrLoadFilesProject(path, args)
  if proj is None:
    proj = ProjectDatabase(projectPath,args)
    for f in find_cpp_files(projectPath):
      proj.addFile(f,unsaved_files)
  else:
    proj.args = args
    proj.updateOutdatedFiles(unsaved_files)
  proj.saveProject(os.path.join(projectPath, ".clang_complete.project.dict"))
  return projectPath

def getFilesProjectSymbolNames(filePath,args):
  proj = getOrLoadFilesProject(filePath, args)
  if proj is None:
    print "Sorry, no project for file " + filePath + " found"
  else:
    return proj.getAllTypeNamesInProject()

def getFilesProjectDerivedClassesSymbolNamesForBaseUsr(filePath, args, baseUsr):
  proj = getOrLoadFilesProject(filePath, args)
  if proj is None:
    print "Sorry, no project for file " + filePath + " found"
  else:
    return proj.getDerivedClassesTypeNames(baseUsr)

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
  return find_files(path,["*.cpp","*.cc","*.h","*.hpp","*.inl"])

conf = cindex.Config()


