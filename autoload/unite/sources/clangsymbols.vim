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
symbols = projectDatabase.getFilesProjectSymbolNames(filePath,args)
if symbols is None:
  vim.command("let list = [[\"Nothing\",\"Nothing\",0,0]]")
else:
  command = "let list = ["
  for s in symbols:
    kind = s[2]
    name = s[0]  + " (" + kind + ")"
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
        \ "source": "clangsymbols",
        \ "kind"  : "clangsymbols",
        \ }')
endfunction

function! unite#sources#clangsymbols#define()
  return s:unite_source
endfunction
