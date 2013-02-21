let s:unite_source = {
      \ 'name': 'clangsymbols',
      \ }

function! s:unite_source.gather_candidates(args,context)
python << endpython
import vim
import sys
import time
sys.path.insert(1, "../../../plugin")
import projectDatabase
filePath = vim.eval('expand("%:p")')
args = vim.eval('b:clang_parameters')
projRoot = vim.eval('a:args[0]')
bringProjectUpToDate(projRoot)
symbols = projectDatabase.getFilesProjectSymbolNames(filePath,args.split(" "))
if symbols is None:
  vim.command("let list = []")
else:
  def transform(s):
    kind = s[2]
    name = s[0]  + " (" + kind + ")"
    usr  = s[3]
    return [name,usr,projRoot]
  l = map(transform, symbols)
  command = "let list = " + str(l)
  vim.command(command)
endpython
  return map(list, '{
        \ "word" : v:val[0],
        \ "usr"  : v:val[1],
        \ "proj_root" : v:val[2],
        \ "source": "clangsymbols",
        \ "kind"  : "clangsymbols",
        \ }')
endfunction

function! unite#sources#clangsymbols#define()
  return s:unite_source
endfunction
