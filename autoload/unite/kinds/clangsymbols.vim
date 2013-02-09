let s:kind = {
      \ 'name'           : 'clangsymbols',
      \ 'default_action' : 'open',
      \ 'action_table'   : {},
      \ 'parent'         : [],
      \ }

let s:kind.action_table.open = {
      \ 'is_selectable' : 0,
      \ }

function! s:kind.action_table.open.func(candidate)
  execute "edit" a:candidate.file
  call cursor (a:candidate.line, a:candidate.column)
endfunction

function! unite#kinds#clangsymbols#define()
  return s:kind
endfunction
