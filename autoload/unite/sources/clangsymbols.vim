let s:unite_source = {
      \ 'name': 'clangsymbols',
      \ }

function! s:unite_source.gather_candidates(args,context)
python << endpython
import vim
import sys
sys.path.insert(1, "../../../plugin")
import projectDatabase
filePath = vim.eval('expand("%:p")')
args = vim.eval('b:clang_parameters')
projRoot = vim.eval('b:clang_project_root')
bringProjectUpToDate(projRoot)
symbols = projectDatabase.getFilesProjectSymbolNames(filePath,args.split(" "))
if symbols is None:
  print "Sorry, project database found (or no symbols in project database)"
  vim.command("let list = []")
else:
  command = "let list = ["
  for s in symbols:
    kind = s[2]
    name = s[0]  + " (" + kind + ")"
    usr  = s[3]
    command = command + "[\"" + name +"\",\"" + usr + "\"],"
# replace last command by closing symbol
  command = command[:-1] + ']'
  vim.command(command)
endpython
  return map(list, '{
        \ "word" : v:val[0],
        \ "usr"  : v:val[1],
        \ "source": "clangsymbols",
        \ "kind"  : "clangsymbols",
        \ }')
endfunction

function! unite#sources#clangsymbols#define()
  return s:unite_source
endfunction
