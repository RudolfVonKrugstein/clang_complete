import projectDatabase
import os

proj = projectDatabase.getOrLoadFilesProject('./file',[])
print "Updating project ..."
proj.updateOutdatedFiles([])
for s in projectDatabase.getFilesProjectSymbolNames(os.path.abspath('./file'),[]):
  print s

