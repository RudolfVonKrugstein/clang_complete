import projectDatabase
import os

proj = projectDatabase.getOrLoadFilesProject('./file',[])
print "Updating project ..."
def makeQuickFix(i):
  return { 'bufnr' : 0,
           'lnum'  : i[1],
           'col'   : i[2],
           'text'  : i[3],
           'type'  : i[4]
         }
qf = map (makeQuickFix,proj.getAllDiagnostics())
print str(qf)
