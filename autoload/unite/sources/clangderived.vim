let s:unite_source = {
      \ 'name': 'clangderived',
      \ }

function! s:unite_source.gather_candidates(args,context)
python << endpython
import vim
import sys
sys.path.insert(1, "../../../plugin")
import projectDatabase

baseUsr = getUsrUnderCursor()
filePath = vim.eval('expand("%:p")')
args = vim.eval('b:clang_parameters')
projRoot = vim.eval('b:clang_project_root')
bringProjectUpToDate(projRoot)
if baseUsr is None or baseUsr == "":
  vim.command("let list = []")
else:
  symbols = projectDatabase.getFilesProjectDerivedClassesSymbolNamesForBaseUsr(filePath,args.split(" "),baseUsr)
  command = "let list = [ "
  for s in symbols:
    name = s[0]
    pos  = s[1]
    command = command + "[\"" + name +"\",\"" + pos[0] + "\"," + str(pos[1]) + "," + str(pos[2]) + "],"
  # replace last command by closing symbol
  command = command[:-1] + ']'
  vim.command(command)
endpython
  return map(list, '{
        \ "word" : v:val[0],
        \ "file"  : v:val[1],
        \ "line"  : v:val[2],
        \ "column": v:val[3],
        \ "source": "clangderived",
        \ "kind"  : "clangderived",
        \ }')
endfunction

function! unite#sources#clangderived#define()
  return s:unite_source
endfunction
