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
    # set if this usr should be listed in a list of all types
    self.shouldBeListed = (self.kind not in [cindex.CursorKind.FIELD_DECL.value,
      cindex.CursorKind.ENUM_CONSTANT_DECL.value,
      cindex.CursorKind.VAR_DECL.value,
      cindex.CursorKind.PARM_DECL.value,
      cindex.CursorKind.TEMPLATE_TYPE_PARAMETER.value,
      cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER.value])
    self.isInProject = False

  def removeFile(self,fileName):
    ''' Goes through all information about the usr and remove anything  that has to do wit the file. Returns if the usr has no associated files.'''
    self.references   = set(filter(lambda loc: loc[0] != fileName, self.references))
    self.declarations = set(filter(lambda loc: loc[0] != fileName, self.declarations))
    self.definitions  = set(filter(lambda loc: loc[0] != fileName, self.definitions))
    self.associatedFiles.discard(fileName)
    return len(self.associatedFiles) == 0

  def addDefinition(self,loc,projRoot):
    addition = (os.path.normpath(loc.file.name), loc.line, loc.column)
    if addition not in self.definitions:
      self.definitions.add(addition)
      if not self.isInProject:
        if addition[0].startswith(projRoot):
          self.isInProject = True

  def addDeclaration(self,loc,projRoot):
    self.declarations.add((os.path.normpath(loc.file.name), loc.line, loc.column))
    addition = (os.path.normpath(loc.file.name), loc.line, loc.column)
    if addition not in self.declarations:
      self.declarations.add(addition)
      if not self.isInProject:
        if addition[0].startswith(projRoot):
          self.isInProject = True

  def addReference(self,loc,kind,parent = None,projRoot = None):
    ''' From the parent we can get the type of the derived class in
        case of a CXX_BASE_SPECIFIER.'''
    self.references.add((os.path.normpath(loc.file.name), loc.line, loc.column, kind, parent))
  def addAssociatedFile(self,fileName):
    self.associatedFiles.add(os.path.normpath(fileName))

  def getLocations(self, locType):
    ''' Get the locations, sorted!'''
    if locType == "declarations":
      res = list(self.declarations)
      res.sort()
      return res
    if locType == "definitions":
      res = list(self.definitions)
      res.sort()
      return res
    if locType == "references":
      res = map(lambda x: (x[0],x[1],x[2]), self.references)
      res.sort()
      return res
    if locType == "declarations_and_definitions":
      decl = self.getLocations("declarations")
      defi = self.getLocations("definitions")
      decl.extend(defi)
      return decl
    if locType == "occurences":
      res = list(self.declarations.union(self.definitions))
      res.extend(self.getLocations("references"))
      res.sort()
      return res


class UnsavedFile():
  '''Information about a file still in the buffer.'''
  def __init__(self,name,buffer,changedtick,tu = None):
    self.name = os.path.normpath(name)
    self.buffer = buffer
    self.changedtick = changedtick
    self.tu = tu

class IncludeFileChangeTime():
  '''For files on which this file depends, the modification time
     and changedtick at time of parse has to be recorded, so
     that we now when the parse is outdated.'''
  def __init__(self, mtime, changedtick):
    self.mtime = mtime
    self.changedtick = changedtick

class FileInfo():
  '''Information about a file located in a projects database'''
  def __init__(self, fileName, args = None):
    self.name = fileName
    # set usrs this references
    self.usrStrings = set()
    self.args = args
    # diagnostics for the file
    self.diagnostics = set()

    # dict from file name to depdency file
    self.includedFiles = dict()

  def parseDiagnostics(self, diagnostics):
    self.diagnostics = set()
    for d in diagnostics:
      if d.location.file:
        filename = d.location.file.name
      else:
        filename = ""
      # get the type
      if d.severity == d.Ignored:
        type = 'I'
      elif d.severity == d.Note:
        type = 'I'
      elif d.severity == d.Warning:
        if "argument unused during compilation" in d.spelling:
          continue
        type = 'W'
      elif d.severity == d.Error:
        type = 'E'
      elif d.severity == d.Fatal:
        type = 'E'
      else:
        continue
      self.diagnostics.add((filename, d.location.line, d.location.column, d.spelling + " (while parsing " + os.path.basename(self.name) + ")" , type, d.severity))

  def addInclude(self,file,changedtick = 0):
    mtime = os.path.getmtime(file)
    self.includedFiles[os.path.normpath(file)] = IncludeFileChangeTime(mtime, changedtick)

  def needsReparse(self,unsavedFiles):
    ''' Returns true if the files needs to be reparsed.'''
    for uFile in unsavedFiles.itervalues():
      if uFile.name in self.includedFiles:
        if self.includedFiles[uFile.name].changedtick < uFile.changedtick:
          return True
    for dPath,data in self.includedFiles.iteritems():
      mtime = os.path.getmtime(dPath)
      if mtime > data.mtime:
        return True
    return False

  def onWriteFile(self,file,changedtick):
    ''' After a file has been written, we change if we are up to date and if we are
        we can update the mtime without reparsing.'''
    if file in self.includedFiles:
      if self.includedFiles[file].changedtick == changedtick:
        mtime = os.path.getmtime(file)
        self.includedFiles[file].mtime = mtime

  def onReload(self):
    ''' After relading we need to set all changedtick of dependend files to 0.'''
    for f in self.includedFiles.itervalues():
      f.changedtick = 0

      

class IncludedFile():
  ''' A file on which other depend (meaning with
      this file changes, the other has to be recompiled)'''
  def __init__(self):
    self.dependedFiles = set()

  def addDependendFile(self,path):
    self.dependedFiles.add(os.path.normpath(path))

  def removeDependendFile(self,path):
    self.dependedFiles.remove(os.path.normpath(path))
    return len(self.dependedFiles) == 0


class ProjectDatabase:
  ''' Database for all files of a project.'''
  def __init__(self, root, args):
    # files in the project and the corresponing FileInfo
    self.fileInfos = dict()
    # file that are included from somewhere
    self.includedFiles = dict()
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
      for p,f in res.fileInfos.iteritems():
        f.onReload()
      return res
    else:
      raise RuntimeError(dictPath + " is not a saved project database")

  def getAllDiagnostics(self):
    res = set()
    for p,f in self.fileInfos.iteritems():
      res = res.union(f.diagnostics)
    return res

  def saveProject(self,dictPath):
    f = open(dictPath,"w")
    pickle.dump(self,f,protocol=2)
    f.close()

  def addFile(self,fileName, unsavedFiles):
    ''' Add a file to database'''
    # check if file is already known
    if (self.fileInfos.has_key(fileName)):
      return
    print "Parsing",fileName
    transUnit = None
    if fileName in unsavedFiles:
      transUnit = unsavedFiles[fileName].tu
    if transUnit is None:
      # create libclang compatible data structure
      unsaved_files = map (lambda uFile: (uFile.name, uFilfe.buffer), unsavedFiles)
      transUnit = cindex.TranslationUnit.from_source(fileName, args = self.args, unsaved_files = unsaved_files)

    cursor = transUnit.cursor
    # remember file
    self.fileInfos[fileName] = FileInfo(fileName, self.args)
    fileInfo = self.fileInfos[fileName]
    fileInfo.parseDiagnostics(transUnit.diagnostics)
    # build database with file
    self.buildDatabase(cursor,None,fileInfo,fileName)

    # build include dependency
    for i in transUnit.get_includes():
      name = os.path.normpath(i.source.name)
      fileInfo.addInclude(name)
      if name not in self.includedFiles:
        self.includedFiles[name] = IncludedFile()
      self.includedFiles[name].addDependendFile(fileName)
      if name in unsavedFiles:
        fileInfo.includedFiles[name].changedtick = unsavedFiles[name].changedtick

  def openFile(self, path, changedtick):
    '''Set the changedtick for this file to the given changedtick.'''
    if path in self.includedFiles:
      for file in self.includedFiles[path].dependedFiles:
        self.fileInfos[file].includedFiles[path].changedtick = changedtick

  def closeFile(self,path):
    '''Nothing to do.'''
    pass

  def onFileSaved(self, path, changedtick):
    '''When a file is saved, we want to know so that when the changedtick of the file
       is up to date (meaning the file that is changed is already up to date in the database)
       we want to update the mtime without reparsing it.
       Also of the file is not part of the project (because it did not exist under its file name before)
       we want to add it now.
       '''
    if path in self.includedFiles:
      for file in self.includedFiles[path].dependedFiles:
        self.fileInfos[file].onWriteFile(path, changedtick)

  def removeFile(self,fileName):
    ''' Remove a file from the database.
        Removes all references from USRs to this file
        and removes USRs that do not reference any files anyore'''
    fileInfo = self.fileInfos[fileName]
    for u in fileInfo.usrStrings:
      if self.usrInfos[u].removeFile(fileName):
        # true means the USR is not referenced anymore
        del self.usrInfos[u]
    
    for d in self.fileInfos[fileName].includedFiles:
      if self.includedFiles[d].removeDependendFile(fileName):
        del self.includedFiles[d]

    del self.fileInfos[fileName]

  def updateOrAddFile(self,fileName, unsavedFiles):
    ''' Remove (if it exits) and re-add a file'''
    if self.fileInfos.has_key(fileName):
      self.removeFile(fileName)
    self.addFile(fileName, unsavedFiles)

  def updateOutdatedFiles(self, unsavedFiles):
    ''' Search for files which mtime is older than the mtime of the file on disc
        and update those.
        Also update all files for which the args are different than the given ones.
        Also remove files not existing anymore.'''

    outdatedFiles = []
    removedFiles  = []
    for file,fileInfo in self.fileInfos.iteritems():
      try:
        if fileInfo.needsReparse(unsavedFiles):
          outdatedFiles.append(fileInfo.name)
      except:
        removedFiles.append(fileInfo.name)
    for f in removedFiles:
      self.removeFile(f)
    for f in outdatedFiles:
      self.updateOrAddFile(f, unsavedFiles)
    for f in find_cpp_files(self.root):
      if not self.fileInfos.has_key(f):
        self.addFile(f,unsavedFiles)

  def readCursor(self,c,parent, usrFileEntry, fileName):
    ''' Read symbol at cursor position.
        Also read any symbol cursor references
        and their lexical parents.
    '''

    # there are some cursor, we are not interested in
    # I am sure other things will come up

    if c.kind.value in [cindex.CursorKind.CXX_ACCESS_SPEC_DECL.value,
                        cindex.CursorKind.LINKAGE_SPEC.value,
                        cindex.CursorKind.UNEXPOSED_DECL.value
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
      # if the lexical parent is delcaration, than also add it
      if (cursor.lexical_parent is not None) and cursor.lexical_parent.kind.is_declaration():
        addDeclaration(cursor.lexical_parent)
      usrInfo = self.getOrCreateUsr(cursor.get_usr(), cursor.kind.value, usrFileEntry, cursor.displayname, cursor.spelling, getLexicalParent(cursor))
      if cursor.is_definition():
        usrInfo.addDefinition(cursor.location,self.root)
      else:
        usrInfo.addDeclaration(cursor.location, self.root)
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
    # if we are outside of the project
    # we are not interested. We are only interested in things defined, declared or referenced in a file part of the project
    # and since we parse all files, we can be sure not to miss anything
    # if we do stop when not in the source file, database building takes much longer
    if not (c.location.file is None) and not c.location.file.name.startswith(self.root):
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

  def getFullDisplayTypeName(self,usrInfo):
    '''Get the full type name, with the top level beeing the display name.'''
    if not (usrInfo.lexical_parent is None):
      return self.getFullTypeNameFromUsr(usrInfo.lexical_parent) + "::" + usrInfo.displayname
    else:
      return usrInfo.displayname

  def getUsrLocations(self, usr, locType):
    return self.usrInfos[usr].getLocations(locType)

  def getAllTypeNames(self):
    '''Iterator that returns all (full) type names and the position where
       they are declated. If multiple positions are found for, the type name
       is returned multiple times.
       Returns a list of typles:
       [(typeName,set([(fileName,line,column)...]),kindname,usr),...]
       '''
    for k,usr in self.usrInfos.iteritems():
      if not usr.shouldBeListed:
        continue
      tName = self.getFullDisplayTypeName(usr)
      kind  = cindex.CursorKind.from_id(usr.kind).name
      # add the declaration positions. If there are none, add definition positions
      if len(usr.declarations) == 0:
        positions = usr.definitions
      else:
        positions = usr.declarations
      yield (tName,positions,kind,usr.usr)

  def getAllTypeNamesInProject(self):
    ''' same as getAllTypeNames, but reduced to files in the project
       Returns a list of typles:
       [(typeName,set([(fileName,line,column)...]),kindname,usr),...]'''
    for k,usr in self.usrInfos.iteritems():
      if not usr.shouldBeListed:
        continue
      tName = self.getFullDisplayTypeName(usr)
      kind  = cindex.CursorKind.from_id(usr.kind).name
      # add the declaration positions. If there are none, add definition positions
      if len(usr.declarations) == 0:
        positions = usr.definitions
      else:
        positions = usr.declarations
      if usr.isInProject:
        yield (tName,positions,kind,usr.usr)

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

def updateProject(projectPath, unsavedFiles):
  loadedProjects[projectPath].updateOutdatedFiles(unsavedFiles)

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

def onLoadFile(filePath, args, changedtick):
  '''Check if the project for the file already exists. If not, create a new project.
     Add the file to the project.'''
  proj = getOrLoadFilesProject(filePath, args)
  if proj is not None:
    proj.openFile(filePath, changedtick)
    return proj.root
  return None

def onFileSaved(self,path,changedtick,unsavedFiles):
  '''When a file is saved, we want to know so that when the changedtick of the file
     is up to date (meaning the file that is changed is already up to date in the database)
     we want to update the mtime without reparsing it.
     Also of the file is not part of the project (because it did not exist under its file name before)
     we want to add it now.
     '''
  proj = getOrLoadFilesProject(path)
  if proj is not None:
    proj.onFileSaved(path,changedtick,unsaved_files)
  for ex in cppExtensions:
    if path.endswith(ex):
      proj.addFile(path,unsaved_files,unsavedFilesChangedtick)

def getProjectFromRoot(root):
  if loadedProjects.has_key(root):
    return loadedProjects[root]
  return None

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

def printLoadedProjects():
  print loadedProjects

def onUnloadFile(filePath):
  proj = getFilesProject(filePath)
  if proj is not None:
    proj.closeFile(filePath)
    # should we also update the project here?
    print "Saving clang project dictonary at " + proj.root
    proj.saveProject(os.path.join(proj.root, ".clang_complete.project.dict"));
    del loadedProjects[proj.root]

def createOrUpdateProjectForFile(path,args, unsavedFiles):
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
      proj.addFile(f,unsavedFiles)
    loadedProjects[projectPath] = proj
  else:
    proj.args = args
    proj.updateOutdatedFiles(unsavedFiles)
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
  return find_files(path,map (lambda ex: "*" + ex, cppExtensions))

cppExtensions = [".cpp",".cc"]

conf = cindex.Config()


