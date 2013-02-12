let s:unite_source = {
      \ 'name': 'clangsymbollocations',
      \ }

function! s:unite_source.gather_candidates(args,context)
python << endpython
import vim
import sys
import os
sys.path.insert(1, "../../../plugin")
import projectDatabase
usr = vim.eval("a:args[0]")
locationType = vim.eval("a:args[1]")
projRoot = vim.eval('b:clang_project_root')
if projRoot is None or projRoot == "" or usr is None or locationType is None or usr == "":
  vim.command("let list = []")
else:
  bringProjectUpToDate(projRoot)
  locations = projectDatabase.getProjectFromRoot(projRoot).getUsrLocations(usr, locationType)
  command = "let list = [ "
  for s in locations:
    file   = s[0]
    line   = s[1]
    column = s[2]
    name   = os.path.basename(file) + " " + str(line) + "," + str(column)
    command = command + "[\"" + name + "\",\"" + file + "\","  + str(line) + "," + str(column) + "],"
  # replace last command by closing symbol
  command = command[:-1] + ']'
  vim.command(command)
endpython
  return map(list, '{
        \ "word" : v:val[0],
        \ "file"  : v:val[1],
        \ "line"  : v:val[2],
        \ "column": v:val[3],
        \ "source": "clangsymbollocations",
        \ "kind"  : "goto",
        \ }')
endfunction

function! unite#sources#clangsymbollocations#define()
  return s:unite_source
endfunction
